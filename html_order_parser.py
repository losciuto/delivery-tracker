"""
HTML Order Parser for Delivery Tracker.
Parses raw HTML source from order pages (Amazon, Temu, eBay, generic)
and extracts order data without any external dependencies (regex only).
"""
import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import utils

logger = utils.get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Tracking patterns (shared across parsers)
# ─────────────────────────────────────────────────────────────────────────────
TRACKING_PATTERNS = [
    (r'\b(1Z[A-Z0-9]{16})\b',                   'UPS'),
    (r'\b(0034\d{16})\b',                        'Poste Italiane'),
    (r'\b(JD\d{18})\b',                          'DHL'),
    (r'\b(GM\d{16,18})\b',                       'GLS'),
    (r'\b(BRT\d{10,14})\b',                      'BRT'),
    (r'\b(9C[A-Z0-9]{10,12})\b',                 'Temu Carrier'),
    (r'\b([A-Z]{2}\d{9}[A-Z]{2})\b',            'Poste/Generic'),  # standard postal
    (r'\b(\d{12,14})\b',                         'Generic'),        # FedEx/DHL numeric
    (r'\b([A-Z0-9]{10,25})\b',                   'Generic'),        # fallback alphanumeric
]

# ─────────────────────────────────────────────────────────────────────────────
# Status keyword mapping
# ─────────────────────────────────────────────────────────────────────────────
STATUS_KEYWORDS = [
    ('Consegnato',         ['consegnato', 'delivered', 'consegna effettuata', 'package delivered',
                            'order delivered', 'ordine consegnato', 'arrived']),
    ('In Consegna',        ['in consegna', 'out for delivery', 'in delivery', 'arriverà oggi',
                            'arriving today', 'con il corriere']),
    ('In Transito',        ['in transito', 'in transit', 'at sorting', 'departed', 'assegnato',
                            'spedizione in corso', 'on the way', 'partito dal', 'in viaggio',
                            'transito', 'partito']),
    ('Spedito',            ['spedito', 'shipped', 'dispatched', 'invio', 'sent', 'in spedizione',
                            'order shipped', 'ordine spedito', 'has been shipped']),
    ('Processing',         ['in elaborazione', 'processing', 'preparazione', 'in preparazione',
                            'order processed', 'pagato', 'paid']),
    ('Problema/Eccezione', ['eccezione', 'problema', 'ritardo', 'exception', 'delay', 'failed',
                            'undeliverable', 'indirizzo non trovato', 'tentativo fallito']),
]

# ─────────────────────────────────────────────────────────────────────────────
# Date patterns (Italian and English)
# ─────────────────────────────────────────────────────────────────────────────
MONTH_IT = {
    'gen': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mag': 5, 'giu': 6,
    'lug': 7, 'ago': 8, 'set': 9, 'sett': 9, 'ott': 10, 'nov': 11, 'dic': 12,
    'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5,
    'giugno': 6, 'luglio': 7, 'agosto': 8, 'settembre': 9, 'ottobre': 10,
    'novembre': 11, 'dicembre': 12,
}
MONTH_EN = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11,
    'december': 12,
}
MONTH_MAP = {**MONTH_IT, **MONTH_EN}


def _clean_html(html: str) -> str:
    """Remove HTML tags and decode common entities, preserving some structure."""
    if not html: return ""
    
    # 1. Remove script and style blocks entirely
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Replace block-level tags with newlines to preserve structure
    text = re.sub(r'<(div|p|br|tr|li|h[1-6]|header|footer)[^>]*>', '\n', text, flags=re.IGNORECASE)
    
    # 3. Remove all other tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 4. Decode common HTML entities
    entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
        '&#39;': "'", '&nbsp;': ' ', '&euro;': '€', '&#x27;': "'",
    }
    for ent, char in entities.items():
        text = text.replace(ent, char)
        
    # 5. Clean up whitespace: collapse multiple spaces but keep newlines
    lines = []
    for line in text.split('\n'):
        line = re.sub(r'[ \t]+', ' ', line).strip()
        if line:
            lines.append(line)
            
    return '\n'.join(lines)


def _detect_platform(html_lower: str) -> str:
    """Detect the e-commerce platform from HTML content."""
    if 'amazon.it' in html_lower or 'amazon.com' in html_lower or 'amazon.co' in html_lower:
        return 'Amazon'
    if 'temu.com' in html_lower or 'kwcdn.com' in html_lower:
        return 'Temu'
    if 'ebay.it' in html_lower or 'ebay.com' in html_lower:
        return 'eBay'
    if 'aliexpress' in html_lower or 'alicdn.com' in html_lower or 'ae01.alicdn' in html_lower:
        return 'AliExpress'
    if 'shein.com' in html_lower:
        return 'Shein'
    if 'zalando.it' in html_lower or 'zalando.com' in html_lower:
        return 'Zalando'
    if 'mediaworld.it' in html_lower:
        return 'MediaWorld'
    if 'unieuro.it' in html_lower:
        return 'Unieuro'
    if 'vinted.it' in html_lower or 'vinted.com' in html_lower:
        return 'Vinted'
    if 'subito.it' in html_lower:
        return 'Subito.it'
    return 'Altro'


def _detect_page_type(html: str, platform: str) -> str:
    """
    Detect if the page is a list page or a detail/order page.
    Returns 'list', 'detail', or 'unknown'.
    """
    html_lower = html.lower()
    if platform == 'Temu':
        # bgt_orders = order list, bgt_order_detail = single order
        if 'bgt_order_detail' in html_lower or 'order_detail' in html_lower:
            return 'detail'
        if 'bgt_orders' in html_lower and 'bgt_order_detail' not in html_lower:
            return 'list'
    if platform == 'Amazon':
        if 'order-details' in html_lower or 'orderdetails' in html_lower:
            return 'detail'
        if 'your-orders' in html_lower or 'order-history' in html_lower:
            return 'list'
    return 'unknown'


def _extract_order_ids(text: str, platform: str, html: str = "") -> List[str]:
    """Extract all order IDs from plain text or raw HTML based on platform patterns."""
    ids = []
    if platform == 'Amazon':
        ids = re.findall(r'\b(\d{3}-\d{7}-\d{7})\b', text)
    elif platform == 'Temu':
        ids = re.findall(r'\b(PO-\d{3}-\d{10,20})\b', text)
        if not ids:
            ids = re.findall(r'\b(PO\d{10,20})\b', text)
    elif platform == 'eBay':
        ids = re.findall(r'\b(\d{2}-\d{5}-\d{5})\b', text)
    elif platform == 'AliExpress':
        # AliExpress IDs are 15-20 digits long. 
        # Removed \b as some HTML structures might not have word boundaries around IDs.
        ids = re.findall(r'(\d{15,20})', text)
        # Also look for tradeOrderId Pattern in raw HTML
        if not ids and html:
             ids = re.findall(r'tradeOrderId[:\s\'"]*(\d{15,20})', html, re.IGNORECASE)

    # Generic fallback: look for "ordine" / "order" followed by alphanumeric
    if not ids:
        # Require at least one digit to avoid purely alphabetical false positives
        generic = re.findall(
            r'(?:ordine|order|n[°\.]?\s*ordine|order\s*#|ordine\s*n\.?)\s*[:\s]?\s*([A-Z0-9]*[0-9][-A-Z0-9]{3,30})',
            text, re.IGNORECASE
        )
        # Blacklist common false positives for IDs
        blacklist = {'aiuto', 'help', 'account', 'login', 'accedi', 'resi', 'rimborsi', 'dettagli'}
        ids = [g.strip() for g in generic if g.strip() and g.strip().lower() not in blacklist]
    
    return list(dict.fromkeys(ids))  # deduplicate preserving order


def _extract_tracking(text: str, html: str = "") -> tuple[Optional[str], Optional[str]]:
    """Return (tracking_number, carrier) from plain text or raw HTML."""
    # Tracking patterns
    # Added specific Temu and common carrier patterns
    # Prioritizing 9C and explicit JSON keys
    tracking_patterns = [
        (r'(\b9C[A-Z0-9]{10,12}\b)', 'Temu Carrier'), # Specific Temu carrier pattern
        (r'(\b950C[A-Z0-9]{8,15}\b)', 'Poste Italiane / SDA'), # Common Amazon/Italy carrier
        (r'(\bRTZ[A-Z0-9]{10,15}\b)', 'AliExpress / Cainiao'), # Specific AliExpress/Cainiao pattern
        (r'["\']tracking(?:No|Number|_no|_number)["\']\s*:\s*["\']([A-Z0-9]+)["\']', None),
        (r'["\']express(?:No|Number|_no|_number)["\']\s*:\s*["\']([A-Z0-9]+)["\']', None),
        (r'["\']shipping(?:No|Number|_no|_number)["\']\s*:\s*["\']([A-Z0-9]+)["\']', None),
        # Improved: exclude noise words and ensure at least one digit is present to avoid words like "produttore"
        (r'(?<!produttore)(?<!modello)(?<!articolo)(?<!prodotto)(?<!referenza)(?<!asin)(?:spedizione|tracking|vettore|codice|n\.|nr\.)(?:\s+(?:di))?[:\s]+([A-Z]*[0-9][A-Z0-9]{7,25})', None),
        (r'([A-Z]*[0-9][A-Z0-9]{9,25})\s+(?:tracciare|traking|visualizza|copia)', None),
        (r'(1Z[A-Z0-9]{16})', 'UPS'),     # UPS
        (r'(\b[0-9]{10,12}\b)', 'Generic'),   # DHL / BRT common
    ]

    # Combine with global TRACKING_PATTERNS
    all_patterns = tracking_patterns + TRACKING_PATTERNS

    # First look near "tracking" keyword for better accuracy
    tracking_ctx = re.search(
        r'(?:tracking|tracciamento|codice\s+spedizione)[^\w]*([A-Z0-9]{8,30})',
        text, re.IGNORECASE
    )
    if tracking_ctx:
        candidate = tracking_ctx.group(1)
        # Skip common Amazon product-related noise if it looks like ASIN
        if re.match(r'^B0[A-Z0-9]{8}$', candidate):
            pass 
        else:
            for pattern_str, carrier_name in all_patterns:
                if re.fullmatch(pattern_str.strip(r'\b'), candidate):
                    return candidate, carrier_name
            if len(candidate) >= 10:
                return candidate, None

    # Full scan with all patterns
    for pattern_str, carrier_name in all_patterns:
        m = re.search(pattern_str, text)
        if not m and html:
            m = re.search(pattern_str, html)
        if m:
            candidate = m.group(1)
            # Filter matches that are obviously ASINs
            if re.match(r'^B0[A-Z0-9]{8}$', candidate):
                continue
            return candidate, carrier_name if carrier_name != 'Generic' else None

    return None, None


def _extract_status(text_lower: str) -> Optional[str]:
    """
    Map text keywords to app status values.
    User requested default 'In Attesa' for HTML imports to let email sync update it.
    """
    return 'In Attesa'


def _extract_date(text: str) -> Optional[str]:
    """
    Try to extract a delivery/estimated date from text.
    Returns ISO format YYYY-MM-DD or None.
    """
    current_year = date.today().year

    # Pattern: "12 gennaio 2025" / "12 jan 2025" / "12 jan"
    m = re.search(
        r'\b(\d{1,2})\s+([a-zA-Zàèéìòù]+)\s*(\d{4})?\b',
        text, re.IGNORECASE
    )
    if m:
        day = int(m.group(1))
        month_str = m.group(2).lower()
        year = int(m.group(3)) if m.group(3) else current_year
        month = MONTH_MAP.get(month_str)
        if month and 1 <= day <= 31:
            try:
                return date(year, month, day).isoformat()
            except ValueError:
                pass

    # Pattern: "Jan 12, 2025" / "January 12"
    m = re.search(
        r'\b([a-zA-Zàèéìòù]+)\s+(\d{1,2})[,\s]*(\d{4})?\b',
        text, re.IGNORECASE
    )
    if m:
        month_str = m.group(1).lower()
        day = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else current_year
        month = MONTH_MAP.get(month_str)
        if month and 1 <= day <= 31:
            try:
                return date(year, month, day).isoformat()
            except ValueError:
                pass

    # Pattern: dd/mm/yyyy or dd-mm-yyyy
    m = re.search(r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b', text)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if len(m.group(3)) == 2:
            y += 2000
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            pass

    # Pattern: yyyy-mm-dd (ISO numeric, common in AliExpress JSON)
    m = re.search(r'\b(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})\b', text)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            pass

    # Pattern: yyyy-mm-dd (ISO already)
    m = re.search(r'\b(\d{4})-(\d{2})-(\d{2})\b', text)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            pass

    return None


def _extract_items_amazon(text: str, html: str) -> List[Dict[str, Any]]:
    """
    Extract individual items from Amazon order page text.
    Returns list of dicts with description, quantity, seller.
    """
    items = []
    seen_descriptions = set()

    # 1. High-precision extraction using data-component="itemTitle"
    # Amazon often places the full product title in a predictable data component
    title_components = re.findall(
        r'data-component="itemTitle"[^>]*>.*?<a[^>]*>(.*?)</a>',
        html, re.DOTALL | re.IGNORECASE
    )
    for title in title_components:
        title = _clean_html(title).strip()
        if title and len(title) > 10 and title not in seen_descriptions:
            # Skip noise
            if any(kw in title.lower() for kw in ['mio account', 'miei ordini', 'accedi', ' prime']):
                continue
            items.append({'description': title, 'quantity': 1, 'seller': ''})
            seen_descriptions.add(title)

    # 2. Fallback to data-component="itemImage" alt text
    if not items:
        img_alts = re.findall(
            r'data-component="itemImage"[^>]*>.*?<img[^>]+alt=["\']([^"\'<>]{10,250})["\']',
            html, re.DOTALL | re.IGNORECASE
        )
        for alt in img_alts:
            alt = html.unescape(alt).strip()
            if alt and alt not in seen_descriptions:
                items.append({'description': alt, 'quantity': 1, 'seller': ''})
                seen_descriptions.add(alt)

    # 3. Legacy splitting/heuristic fallback (if still no luck)
    if not items:
        # Heuristic: product names are typically 10-150 chars, mixed case, not just numbers
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines:
            if 15 < len(line) < 200 and not re.match(r'^[\d\s€.,/-]+$', line):
                skip_words = ['accedi', 'account', 'carrello', 'ordini', 'resi', 'aiuto',
                              'cerca', 'amazon', 'prime', 'offerte', 'copyright', 'privacy',
                              'condizioni', 'cookie', 'pubblicità', 'preferenze']
                if not any(sw in line.lower() for sw in skip_words):
                    if line not in seen_descriptions:
                        items.append({'description': line, 'quantity': 1, 'seller': ''})
                        seen_descriptions.add(line)
                        if len(items) >= 5: break

    # Try to find seller
    seller_match = re.search(
        r'(?:venduto\s+da|sold\s+by|venditore)[:\s]+([^\n<]{2,60})',
        text, re.IGNORECASE
    )
    seller = seller_match.group(1).strip() if seller_match else ''
    for item in items:
        if not item['seller']:
            item['seller'] = seller

    # Try to find quantities near titles
    qty_pattern = re.compile(r'(?:quantit[àa]|qty|q\.t[àa]\.?|pz\.?)[:\s]*(\d+)', re.IGNORECASE)
    for item in items:
        qty_m = qty_pattern.search(item['description'])
        if qty_m:
            item['quantity'] = int(qty_m.group(1))

    return items if items else [{'description': 'Articolo Amazon (da completare)', 'quantity': 1, 'seller': seller}]


def _extract_items_temu(text: str, html: str) -> List[Dict[str, Any]]:
    """
    Extract items from a Temu order detail page.
    Robust version for browser-captured DOM.
    """
    items = []
    seen_descriptions = set()

    # 1. Look for order ID to ensure we are on the right page
    order_id_match = re.search(r'\bPO-\d{3}-\d{10,25}\b', html)
    if not order_id_match:
        logger.warning("TEMU-PARSER: ID Ordine non trovato nel sorgente")

    # 2. Extract JSON blocks containing goods logic
    # We look for "goodsList" or "goods_list"
    list_patterns = [
        r'\\?["\'](?:package|goods|order|item)_?List\\?["\']\s*:\s*\[(.*?)\]',
        r'\\?["\'](?:package|goods|order|item)_?_list\\?["\']\s*:\s*\[(.*?)\]'
    ]
    
    valid_blocks = []
    for pattern in list_patterns:
        for match in re.finditer(pattern, html, re.DOTALL | re.IGNORECASE):
            block_content = match.group(1)
            # Filter out recommendation blocks by looking for noise nearby
            # We check if the block itself contains enough context or if the parent key is noise
            context_area = html[max(0, match.start() - 100) : match.end() + 100].lower()
            noise_markers = ['suggest', 'recommend', 'rec_list', 'recently', 'visti', 'piacere', 'recent_view']
            if any(m in context_area for m in noise_markers):
                continue
            
            valid_blocks.append(block_content)

    # 3. Extract item names and quantities
    item_name_patterns = [
        r'\\?["\'](?:goods|product|item)(?:Name|_name|Title|_title)\\?["\']\s*[:=]\s*\\?["\']([^"\'\\]{5,200})\\?["\']',
        # Non-JSON fallback (cleaner tags)
        r'>(?:[ \n\t]*)([^<]{10,150})(?:[ \n\t]*)<', 
    ]
    qty_pattern = r'\\?["\'](?:quantity|qty|goodsNum|goods_num)\\?["\']\s*:\s*(\d+)'

    for block in valid_blocks:
        item_objects = re.split(r'\}\s*,\s*\{', block)
        for obj in item_objects:
            name = None
            # Prioritize the name pattern from JSON
            n_match = re.search(item_name_patterns[0], obj, re.IGNORECASE)
            if n_match:
                name = n_match.group(1).strip().replace('\\u002F', '/').replace('\\"', '"')
            
            if name and name not in seen_descriptions:
                if any(k in name.lower() for k in ['privacy', 'cookie', 'copyright', 'javascript', 'localeswitch']):
                    continue
                
                qty = 1
                q_match = re.search(qty_pattern, obj, re.IGNORECASE)
                if q_match:
                    qty = int(q_match.group(1))
                
                items.append({'description': name, 'quantity': qty, 'seller': 'Temu'})
                seen_descriptions.add(name)

    # 4. DIRECT DOM SCRAPING (If JSON extraction is sparse)
    # Temu often has product names in <span> or <div> with specific classes or data attributes
    if len(items) < 1:
        # Search for titles near the PO number context
        scrap_patterns = [
            r'class="[^"]*goods-name[^"]*"[^>]*>([^<]{10,150})<',
            r'class="[^"]*item-title[^"]*"[^>]*>([^<]{10,150})<',
            r'class="[^"]*product-title[^"]*"[^>]*>([^<]{10,150})<',
            r'alt=["\']([^"\'<>]{10,120})["\']'
        ]
        context_start = order_id_match.start() if order_id_match else 0
        # Search in the area AFTER the Order ID (where items usually are)
        search_area = html[context_start:context_start + 200000] 
        
        for pattern in scrap_patterns:
            for match in re.finditer(pattern, search_area, re.IGNORECASE):
                m = match.group(1).strip()
                if m and len(m) > 10 and m not in seen_descriptions:
                    # Filter out navigation noise
                    if any(x in m.lower() for x in ['home', 'cart', 'search', 'back', 'temu', 'logo', 'help', 'account', 'sign in']):
                        continue
                    items.append({'description': m, 'quantity': 1, 'seller': 'Temu'})
                    seen_descriptions.add(m)

    return items if items else [{'description': 'Articolo Temu (da completare)', 'quantity': 1, 'seller': 'Temu'}]


def _extract_items_aliexpress(text: str, html: str) -> List[Dict[str, Any]]:
    """
    Extract individual items from AliExpress order page with high precision.
    Uses exhaustive collection, scoring, and aggressive blacklisting.
    """
    candidates = []
    
    # 0. Focus search area - Avoid recommendation sections
    stop_words = [
        'più da amare', 'more to love', 'consigliati per te', 'recommended for you',
        'visti di recente', 'recently viewed', 'prodotti sponsorizzati', 'might also like'
    ]
    search_html = html
    for sw in stop_words:
        stop_idx = search_html.lower().find(sw)
        if stop_idx > -1:
            search_html = search_html[:stop_idx]
            break

    # Aggressive UI/Service Blacklist
    blacklist = [
        'aiuto', 'account', 'registrati', 'carrello', 'lista', 'privacy', 'copyright', 
        'assistenza', 'supporto', 'shipping', 'payment', 'order detail', 'checkout',
        'aliexpress', 'customer service', 'store name', 'contact seller', 'dettagli',
        'riepilogo', 'totale', 'iva', 'metodo di pagamento', 'spedizione', 'indirizzo',
        'impostazioni', 'notifiche', 'messaggi', 'coupon', 'monete', 'centro'
    ]

    # 1. Collect from JSON (High priority)
    json_patterns = [
        (r'"(?:product|goods)Name"\s*:\s*"([^"]{10,250})"', 100), # Very reliable
        (r'"name"\s*:\s*"([^"]{20,250})"', 70), # Likely product name but can be noise
    ]
    for pattern, score in json_patterns:
        for m in re.finditer(pattern, search_html):
            name = m.group(1)
            try:
                name = name.encode('utf-8').decode('unicode_escape') if '\\u' in name else name
            except: pass
            name = _clean_html(name).strip()
            if 20 < len(name) < 255:
                if not any(kw in name.lower() for kw in blacklist):
                    if not re.match(r'^[\d\s€.,/|:()+-]+$', name):
                        candidates.append({'description': name, 'score': score, 'source': 'JSON'})

    # 2. Collect from DOM (Medium/Low priority)
    scrap_patterns = [
        (r'data-pl="product-title"[^>]*>([^<]{10,250})<', 80),
        (r'class="[^"]*(?:product-name|item-title|product-title|title--line-one)[^"]*"[^>]*>([^<]{10,250})<', 60),
        (r'<a[^>]*title=["\']([^"\'<>]{20,250})["\']', 50),
        (r'<img[^>]*alt=["\']([^"\'<>]{20,250})["\']', 40),
    ]
    for pattern, score in scrap_patterns:
        for m in re.finditer(pattern, search_html, re.IGNORECASE):
            name = _clean_html(m.group(1)).strip()
            if 25 < len(name) < 250:
                if not any(kw in name.lower() for kw in blacklist):
                    if not re.match(r'^[\d\s€.,/|:()+-]+$', name):
                        candidates.append({'description': name, 'score': score, 'source': 'DOM'})

    # 3. Last Resort: Heuristic (Very low priority)
    if not candidates:
        clean_text = _clean_html(search_html)
        for line in clean_text.split('\n'):
            line = line.strip()
            if 30 < len(line) < 180 and not re.match(r'^[\d\s€.,/|:()+-]+$', line):
                 if not any(kw in line.lower() for kw in blacklist + ['ordine', 'tracking']):
                     candidates.append({'description': line, 'score': 10, 'source': 'Heuristic'})

    # 4. Selection and Deduplication
    # Sort by score (desc) and remove duplicates keeping highest score
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    unique_items = []
    seen = set()
    for c in candidates:
        if c['description'] not in seen:
            unique_items.append({
                'description': c['description'],
                'quantity': 1,
                'seller': 'AliExpress',
                'debug_source': c['source']
            })
            seen.add(c['description'])
            if len(unique_items) >= 2: break # AliExpress order details usually show 1-2 items clearly

    # 5. Quantity extraction (Proximity search in search_html)
    if unique_items:
        # Search for quantity markers near the end of the restricted area
        qty_match = re.search(r'(?:quantit[àa]|qty|q\.t[àa])[:\s]*(\d+)', search_html, re.IGNORECASE)
        if qty_match:
            for item in unique_items:
                item['quantity'] = int(qty_match.group(1))

    return unique_items if unique_items else [{'description': 'Articolo AliExpress (da completare)', 'quantity': 1, 'seller': 'AliExpress', 'debug_source': 'Fallback'}]


def _extract_items_generic(text: str, html: str) -> List[Dict[str, Any]]:
    """Generic item extraction fallback."""
    items = []
    
    # Look for product titles in common HTML patterns
    title_patterns = [
        r'class="[^"]*(?:product[_-]?name|item[_-]?name|product[_-]?title|goods[_-]?name)[^"]*"[^>]*>([^<]{5,150})<',
        r'<h[1-4][^>]*>([^<]{10,120})</h[1-4]>',
    ]
    for pattern in title_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        for m in matches[:5]:
            m = m.strip()
            if m and len(m) > 5:
                items.append({'description': m, 'quantity': 1, 'seller': ''})
        if items:
            break

    # Seller
    seller_match = re.search(
        r'(?:venduto\s+da|sold\s+by|venditore|seller)[:\s]+([^\n<]{2,60})',
        text, re.IGNORECASE
    )
    seller = seller_match.group(1).strip() if seller_match else ''
    for item in items:
        item['seller'] = seller

    return items if items else [{'description': 'Articolo (da completare)', 'quantity': 1, 'seller': seller}]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

class HtmlOrderParser:
    """
    Parse raw HTML from an order page and return a list of order dicts
    ready to be inserted into the database via database.add_order().
    """

    def parse(self, html: str) -> List[Dict[str, Any]]:
        """
        Main entry point.
        Returns a list of order dicts (one per item found).
        Each dict has the same keys as database.add_order() expects.
        """
        return self.parse_with_meta(html)['orders']

    def parse_with_meta(self, html: str) -> Dict[str, Any]:
        """
        Extended parse that returns orders + metadata.
        Returns dict with keys:
          - orders: list of order dicts
          - platform: detected platform name
          - page_type: 'list', 'detail', or 'unknown'
          - warning: optional warning message string (or None)
        """
        if not html or not html.strip():
            return {'orders': [], 'platform': 'Sconosciuto', 'page_type': 'unknown', 'warning': None}

        html_lower = html.lower()
        platform = _detect_platform(html_lower)
        page_type = _detect_page_type(html, platform)
        text = _clean_html(html)
        text_lower = text.lower()

        logger.info(f"HTML-PARSER: Piattaforma rilevata: {platform}, Tipo pagina: {page_type}")

        # ── Warn if this is a list page (orders loaded dynamically) ───────
        warning = None
        if page_type == 'list':
            platform_hints = {
                'Temu': (
                    "Hai incollato la pagina LISTA ordini di Temu.\n\n"
                    "I dati degli ordini vengono caricati dinamicamente e non sono nel sorgente HTML.\n\n"
                    "👉 Come procedere:\n"
                    "1. Vai su temu.com → I tuoi ordini\n"
                    "2. Clicca su un singolo ordine per aprire il DETTAGLIO\n"
                    "3. Usa Ctrl+U (o tasto destro → Visualizza sorgente pagina)\n"
                    "4. Copia tutto il sorgente e incollalo qui"
                ),
                'Amazon': (
                    "Hai incollato la pagina LISTA ordini di Amazon.\n\n"
                    "👉 Come procedere:\n"
                    "1. Vai su amazon.it → I miei ordini\n"
                    "2. Clicca su 'Dettagli ordine' per un singolo ordine\n"
                    "3. Usa Ctrl+U per visualizzare il sorgente\n"
                    "4. Copia tutto il sorgente e incollalo qui"
                ),
            }
            warning = platform_hints.get(platform,
                f"Hai incollato una pagina LISTA ordini di {platform}.\n"
                "Incolla invece il sorgente della pagina DETTAGLIO di un singolo ordine."
            )
            logger.warning(f"HTML-PARSER: Pagina lista rilevata per {platform} - dati non disponibili nell'HTML statico")
            return {'orders': [], 'platform': platform, 'page_type': page_type, 'warning': warning}

        # ── Order IDs ──────────────────────────────────────────────────────
        order_ids = _extract_order_ids(text, platform, html)
        primary_order_id = order_ids[0] if order_ids else ''
        logger.info(f"HTML-PARSER: ID ordini trovati: {order_ids}")

        # ── Tracking ───────────────────────────────────────────────────────
        tracking, carrier = _extract_tracking(text, html)
        logger.info(f"HTML-PARSER: Tracking={tracking}, Carrier={carrier}")

        # ── Status ─────────────────────────────────────────────────────────
        # User requested 'In Attesa' for HTML imports to let email sync update it.
        # But for Amazon, we can try to extract the specific status message for notes.
        status = 'In Attesa'
        amazon_status_text = ""
        if platform == 'Amazon':
            # Look for status message in data-component="shipmentStatus"
            status_match = re.search(
                r'data-component="shipmentStatus"[^>]*>.*?<h4[^>]*>(.*?)</h4>',
                html, re.DOTALL | re.IGNORECASE
            )
            if status_match:
                amazon_status_text = _clean_html(status_match.group(1)).strip()
                logger.info(f"HTML-PARSER: Amazon Status extra: {amazon_status_text}")
        
        logger.info(f"HTML-PARSER: Stato rilevato: {status}")

        # ── Estimated delivery date ────────────────────────────────────────
        est_delivery = None
        
        # 1. Try Amazon specific logic
        if platform == 'Amazon':
            if amazon_status_text:
                est_delivery = _extract_date(amazon_status_text)

        # 2. Generic logic with strict proximity search
        if not est_delivery:
            # Look specifically for delivery-related phrases
            target_phrases = [
                r'(?:consegna\s+prevista|estimated\s+delivery|arriverà|arrives?|consegna\s+entro|deliver(?:y|ed)\s+by)[:\s]*([^\n]{5,100})',
                r'(?:consegnato\s+il|delivered\s+on)[:\s]*([^\n]{5,100})'
            ]
            for phrase_p in target_phrases:
                m = re.search(phrase_p, text, re.IGNORECASE)
                if m:
                    est_delivery = _extract_date(m.group(1))
                    if est_delivery: break
        
        logger.info(f"HTML-PARSER: Data consegna prevista: {est_delivery}")

        # ── Order Date ──────────────────────────────────────────────────────
        order_date_raw = None
        # Look for order date keywords with strict proximity
        order_date_phrases = [
            r'(?:data\s+(?:dell\')?ordine|order\s+date|data\s+acquisto|purchased\s+on|ordine\s+effettuato\s+il)[:\s]*([^\n]{5,100})'
        ]
        for od_phrase in order_date_phrases:
            m = re.search(od_phrase, text, re.IGNORECASE)
            if m:
                order_date_raw = _extract_date(m.group(1))
                if order_date_raw: break
        
        # Fallback to first plausible date ONLY if it's a short text or we are very desperate
        # For AliExpress, we often find "17 feb 2026" and it's the only date.
        if not order_date_raw and platform == 'AliExpress':
             order_date_raw = _extract_date(text)

        logger.info(f"HTML-PARSER: Data ordine reale: {order_date_raw}")

        # ── Items ──────────────────────────────────────────────────────────
        if platform == 'Amazon':
            items = _extract_items_amazon(text, html)
        elif platform == 'Temu':
            items = _extract_items_temu(text, html)
        elif platform == 'AliExpress':
            items = _extract_items_aliexpress(text, html)
        else:
            items = _extract_items_generic(text, html)
        logger.info(f"HTML-PARSER: Articoli trovati: {len(items)}")

        # ── Build result list ──────────────────────────────────────────────
        today_iso = date.today().isoformat()
        final_order_date = order_date_raw or today_iso
        results = []
        for i, item in enumerate(items):
            # If multiple order IDs, try to assign one per item
            order_id_for_item = order_ids[i] if i < len(order_ids) else primary_order_id
            results.append({
                'platform':         platform,
                'seller':           item.get('seller', ''),
                'description':      item.get('description', 'Articolo'),
                'quantity':         item.get('quantity', 1),
                'site_order_id':    order_id_for_item,
                'tracking_number':  tracking or '',
                'carrier':          carrier or '',
                'last_mile_carrier': '',
                'status':           status,
                'estimated_delivery': est_delivery or '',
                'order_date':       final_order_date,
                'is_delivered':     status == 'Consegnato',
                'alarm_enabled':    True,
                'link':             '',
                'destination':      '',
                'position':         '',
                'notes':            f'[{platform}] [Source: {item.get("debug_source", "Unknown")}] [Importato il {datetime.now().strftime("%d/%m/%Y %H:%M")}]',
                'category':         '',
            })

        return {'orders': results, 'platform': platform, 'page_type': page_type, 'warning': warning}
