"""
Email manager module for Delivery Tracker.
Handles IMAP connection (XOAUTH2), searching, and parsing of delivery-related emails.
"""
import imaplib
import email
from email.header import decode_header
import re
from typing import List, Dict, Any, Optional
import msal
import base64
import utils
import database
from datetime import datetime, date, timedelta

logger = utils.get_logger(__name__)

# Email Server Settings (Outlook/Office365/Hotmail)
MICROSOFT_IMAP_SERVER = "outlook.office365.com"
MICROSOFT_IMAP_PORT = 993

# Email Server Settings (Gmail)
GOOGLE_IMAP_SERVER = "imap.gmail.com"
GOOGLE_IMAP_PORT = 993

IMAP_TIMEOUT = 30 # secondi

# OAuth2 Settings
CLIENT_ID = "3932ab49-e115-44d6-964e-9b43a479c5bd"
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["https://outlook.office.com/IMAP.AccessAsUser.All"]

# Gerarchia degli stati: più alto = più avanzato
STATUS_HIERARCHY = {
    'In Attesa':          0,
    'Problema/Eccezione': 1,
    'Spedito':            2,
    'In Transito':        3,
    'In Consegna':        4,
    'Consegnato':         5,
    'Rimborsato':         5,
    'Annullato':          5,
}


def _is_status_upgrade(current_status: Optional[str], new_status: Optional[str]) -> bool:
    """Restituisce True solo se new_status è uguale o più avanzato di current_status.
    Impedisce di retrocedere lo stato di un ordine già aggiornato."""
    if not new_status:
        return False
    current_rank = STATUS_HIERARCHY.get(current_status or 'In Attesa', 0)
    new_rank = STATUS_HIERARCHY.get(new_status, 0)
    return new_rank >= current_rank


class EmailSyncManager:
    """Manages email synchronization and parsing via OAuth2"""
    
    def __init__(self):
        self.settings = utils.Settings.load()
        self.email_addr = self.settings.get('email_address', '')
        self.enabled = self.settings.get('email_sync_enabled', False)
        self.provider = self.settings.get('email_provider', 'microsoft')
        
        # Decode app password if present
        self.app_password = ""
        saved_b64 = self.settings.get('email_app_password', '')
        if saved_b64:
            try:
                self.app_password = base64.b64decode(saved_b64).decode('utf-8')
            except Exception:
                pass
                
        self.token_cache = msal.SerializableTokenCache()
        
        # Load cache if exists
        cache_data = self.settings.get('ms_token_cache')
        if cache_data:
            self.token_cache.deserialize(cache_data)

    def _save_cache(self):
        """Save token cache to settings"""
        if self.token_cache.has_state_changed:
            self.settings['ms_token_cache'] = self.token_cache.serialize()
            utils.Settings.save(self.settings)

    def get_access_token(self) -> Optional[str]:
        """Get or refresh access token"""
        app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=self.token_cache)
        
        # Try silent acquisition
        accounts = app.get_accounts(username=self.email_addr)
        result = None
        if accounts:
            result = app.acquire_token_silent(SCOPES, account=accounts[0])
            
        if result and "access_token" in result:
            self._save_cache()
            return result["access_token"]
            
        return None

    def connect(self) -> Optional[imaplib.IMAP4_SSL]:
        """Connect and login to IMAP server with appropriate auth method"""
        if not self.email_addr:
            logger.warning("EMAIL-SYNC: Indirizzo email non configurato.")
            return None
            
        if self.provider == 'google':
            if not self.app_password:
                logger.error("EMAIL-SYNC: Password per le App non configurata per Gmail.")
                raise Exception("Devi inserire una Password per le App valida nelle Impostazioni per usare Gmail.")
            
            try:
                logger.info(f"IMAP: Inizializzazione connessione SSL a {GOOGLE_IMAP_SERVER}...")
                mail = imaplib.IMAP4_SSL(GOOGLE_IMAP_SERVER, GOOGLE_IMAP_PORT, timeout=IMAP_TIMEOUT)
                
                logger.info("IMAP: Accesso standard tramite Password per le App...")
                # Standard IMAP login
                status, resp = mail.login(self.email_addr, self.app_password)
                if status != 'OK':
                    logger.error(f"IMAP: Login Gmail fallito: {resp}")
                    raise Exception(f"Errore Login: {resp}")
                
                logger.info("IMAP: Accesso Gmail completato con successo.")
                return mail
            except imaplib.IMAP4.error as e:
                logger.error(f"IMAP: Errore di autenticazione Gmail (password errata o blocco sicurezza): {e}")
                raise Exception("Credenziali Gmail non valide. Verifica la Password per le App e assicurati che non abbia spazi.")
            except Exception as e:
                logger.error(f"IMAP: Errore durante la connessione Gmail: {e}")
                raise e
                
        else:
            # Default Microsoft OAuth2
            token = self.get_access_token()
            if not token:
                logger.error("EMAIL-SYNC: Token non disponibile. Necessaria nuova autorizzazione.")
                raise Exception("Account Microsoft non autorizzato. Vai nelle impostazioni per connetterlo.")
                
            try:
                logger.info(f"OAUTH2: Inizializzazione connessione SSL a {MICROSOFT_IMAP_SERVER}...")
                mail = imaplib.IMAP4_SSL(MICROSOFT_IMAP_SERVER, MICROSOFT_IMAP_PORT, timeout=IMAP_TIMEOUT)
                
                # Generate XOAUTH2 string
                auth_string = f"user={self.email_addr}\1auth=Bearer {token}\1\1"
                
                logger.info("OAUTH2: Invio comando AUTHENTICATE XOAUTH2...")
                status, resp = mail.authenticate('XOAUTH2', lambda x: auth_string)
                
                if status != 'OK':
                    logger.error(f"OAUTH2: Autenticazione fallita: {resp}")
                    raise Exception(f"Errore OAuth2: {resp}")
                    
                logger.info("OAUTH2: Autenticazione completata con successo.")
                return mail
            except Exception as e:
                logger.error(f"OAUTH2: Errore durante la connessione: {e}")
                raise e

    def fetch_updates(self) -> List[Dict[str, Any]]:
        """Fetch and parse recent delivery emails from multiple relevant folders"""
        if not self.enabled:
            return []
            
        mail = self.connect()
        if not mail:
            return []
            
        updates = []
        try:
            # 1. Get all folders
            status, folder_list = mail.list()
            if status != 'OK':
                logger.warning(f"EMAIL-SYNC: Impossibile recuperare la lista delle cartelle: {status}")
                # Fallback to just INBOX
                folders_to_scan = ["INBOX"]
            logger.info(f"EMAIL-SYNC: Trovate {len(folder_list)} cartelle totali.")
            
            # 2. Filter folders dynamically based on active orders in DB
            from database import get_orders
            active_orders = get_orders(include_delivered=False)
            active_platforms = set()
            for o in active_orders:
                p = o.get('platform', '').strip().lower()
                if p: active_platforms.add(p)
            
            logger.info(f"EMAIL-SYNC: Piattaforme attive rilevate nel DB: {list(active_platforms)}")
            
            active_platform_list = list(active_platforms)
            
            # --- Build folders to scan based on active platforms ---
            # Map platform names to potential folder name fragments
            platform_aliases = {
                'amazon': ['amazon'],
                'temu': ['temu'],
                'ebay': ['ebay'],
                'too good to go': ['too good to go', 'too good t go', 'tgtg', 'magico sacchetto'],
                'aliexpress': ['aliexpress', 'cainiao'],
                'vinted': ['vinted'],
                'shein': ['shein'],
                'poste italiane': ['poste', 'sda'],
                'ups': ['ups'],
                'dhl': ['dhl'],
                'gls': ['gls'],
                'brt': ['brt']
            }

            folders_to_scan = []
            platform_found_folders = set()

            for f in folder_list:
                line = f.decode()
                # Extract folder name (handling quoted names or multi-word unquoted names)
                # IMAP format: (Attributes) "Delimiter" Name
                parts = line.split(' "')
                if len(parts) >= 3:
                    # Usually: [attributes, "delimiter", name]
                    folder_name = parts[-1].strip().strip('"')
                else:
                    # Fallback to regex or last part
                    match = re.search(r'"([^"]+)"$', line)
                    if match:
                        folder_name = match.group(1).strip()
                    else:
                        folder_name = line.split()[-1].strip('"')
                        # If the last word is part of a multi-word name, this is still a risk,
                        # but most IMAP servers quote multi-word names.
                
                lower_name = folder_name.lower()
                    
                # 1. Check if folder matches any active platform OR its aliases
                matched_platform = False
                for plat in active_platform_list:
                    aliases = platform_aliases.get(plat.lower(), [plat.lower()])
                    if any(alias in lower_name for alias in aliases):
                        folders_to_scan.append(folder_name)
                        platform_found_folders.add(plat.lower())
                        matched_platform = True
                        break
                
                # 2. Add generic order folders (if not already added)
                if not matched_platform and any(kw in lower_name for kw in ["order", "ordine", "spedizion"]):
                    if "inbox/" not in lower_name:
                        folders_to_scan.append(folder_name)

            # 3. ALWAYS scan Inbox as many platforms send there
            # (Use case: "se non trovo niente ripeto in inbox")
            inbox_name = next((f.decode().split()[-1].strip('"') for f in folder_list if "inbox" in f.decode().lower()), "INBOX")
            if inbox_name in folders_to_scan:
                folders_to_scan.remove(inbox_name)
            folders_to_scan.insert(0, inbox_name) # Put Inbox FIRST to prioritize it
            
            # Limit to max 15 folders to prevent Outlook from closing connection
            folders_to_scan = folders_to_scan[:15]
            logger.info(f"EMAIL-SYNC: Cartelle selezionate per scansione (max 15): {folders_to_scan}")
            
            # Keywords for Python-side filtering
            all_keywords = ["spedito", "consegnato", "tracking", "delivery", "shipped", 
                            "ordine", "order", "acquisto", "delivered", "dispatched",
                            "transito", "transit", "partito", "consegna", "too good to go", "too good t go", "to good to go", 
                            "assegnazion", "sacchetto", "ritiro", "spedizione", "tgtg"]
            
            # --- 3. Scan each folder ---
            # IMPORTANT: IMAP requires English month names (Jan, Feb, ...).
            # strftime("%b") is locale-dependent and might fail on non-English systems.
            months_en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            d_target = date.today() - timedelta(days=30) # Reduced from 60 to 30 for performance
            since_date = f"{d_target.day:02d}-{months_en[d_target.month-1]}-{d_target.year}"
            
            logger.info(f"EMAIL-SYNC: Data di inizio scansione (IMAP format): {since_date}")
            
            for folder in folders_to_scan:
                try:
                    logger.info(f"EMAIL-SYNC: Scansione folder: {folder}...")
                    # Selection
                    try:
                        status, _ = mail.select(f'"{folder}"', readonly=True)
                    except Exception as select_err:
                        logger.error(f"EMAIL-SYNC: Errore critico select {folder}: {select_err}")
                        if "closed" in str(select_err).lower() or "eof" in str(select_err).lower():
                            break
                        continue
                        
                    if status != "OK":
                        logger.warning(f"EMAIL-SYNC: Server ha rifiutato folder {folder}: {status}")
                        continue
                    
                    # Search by date (Standard IMAP SINCE)
                    try:
                        # Passing as separate arguments ensures imaplib formats them correctly as tokens
                        # instead of a single quoted string.
                        status, messages = mail.search(None, 'SINCE', since_date)
                    except Exception as search_err:
                        logger.error(f"EMAIL-SYNC: Errore search in {folder}: {search_err}")
                        continue
                        
                    if status != "OK" or not messages[0]:
                        logger.info(f"EMAIL-SYNC: Nessuna email recente in {folder}")
                        continue
                        
                    email_ids = messages[0].split()
                    logger.info(f"EMAIL-SYNC: Trovate {len(email_ids)} email recenti in {folder}")
                    
                    # Process those emails in chunks to drastically reduce network roundtrips for headers
                    chunk_size = 100
                    relevant_emails_data = [] # List of tuples: (e_id, subject, date)
                    
                    for i in range(0, len(email_ids), chunk_size):
                        chunk_ids = email_ids[i:i + chunk_size]
                        chunk_str = b",".join(chunk_ids)
                        
                        try:
                            # Fetch headers for the whole chunk at once (BODY.PEEK prevents marking as read)
                            res, headers_data = mail.fetch(chunk_str, "(BODY.PEEK[HEADER.FIELDS (SUBJECT DATE)])")
                            if res != "OK" or not headers_data:
                                continue
                                
                            for response_part in headers_data:
                                if isinstance(response_part, tuple):
                                    msg_info = response_part[0].decode(errors='ignore')
                                    # Extract ID from response (e.g. "123 (BODY.PEEK...")
                                    e_id_match = re.search(r'^(\d+)', msg_info)
                                    if not e_id_match: continue
                                    e_id = e_id_match.group(1).encode()
                                    
                                    header_text = response_part[1].decode(errors='replace')
                                    
                                    # Extract Subject
                                    subject_match = re.search(r'Subject:\s*(.*?)(?:\r\n[^\s]|\Z)', header_text, re.IGNORECASE | re.DOTALL)
                                    subject_raw = subject_match.group(1).strip() if subject_match else ""
                                    
                                    # Extract Date
                                    date_match = re.search(r'Date:\s*(.*?)(?:\r\n[^\s]|\Z)', header_text, re.IGNORECASE)
                                    email_date = date_match.group(1).strip() if date_match else ""
                                    
                                    # Decode subject
                                    subject = ""
                                    try:
                                        decoded_parts = decode_header(subject_raw)
                                        for part, enc in decoded_parts:
                                            if isinstance(part, bytes):
                                                subject += part.decode(enc or 'utf-8', errors='replace')
                                            else:
                                                subject += part
                                    except:
                                        subject = subject_raw.replace('\r\n', '').replace('\n', '')
                                    
                                    subject = " ".join(subject.split()) # clear newlines

                                    # Python-side filtering: Check if subject is relevant
                                    is_relevant = any(kw in subject.lower() for kw in all_keywords)
                                    if not is_relevant and not ("too good to go" in folder.lower() or "tgtg" in folder.lower()):
                                        continue
                                        
                                    relevant_emails_data.append((e_id, subject, email_date))
                        except Exception as chunk_err:
                            logger.error(f"EMAIL-SYNC: Errore nel fetching batch degli header in {folder}: {chunk_err}")
                            continue

                    logger.info(f"EMAIL-SYNC: Di {len(email_ids)} totali, {len(relevant_emails_data)} sono rilevanti dai filtri dell'oggetto.")

                    # Fetch full body only for relevant emails
                    for e_id, subject, email_date in relevant_emails_data:
                        try:
                            # 1. Fetch full body (RFC822) to have all content for extraction
                            logger.info(f"EMAIL-SYNC: Analisi body completo per email: {subject[:50]}...")
                            res, msg_data = mail.fetch(e_id, "(RFC822)")
                            if not msg_data or not msg_data[0]: continue
                            
                            raw_email = msg_data[0][1]
                            msg = email.message_from_bytes(raw_email)
                            
                            # Inherit Date if not correctly parsed from RFC822 top-level
                            final_date = msg.get("Date") or email_date
                            
                            # Get body
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() in ["text/plain", "text/html"] and "attachment" not in str(part.get("Content-Disposition")):
                                        payload = part.get_payload(decode=True)
                                        charset = part.get_content_charset() or 'utf-8'
                                        try:
                                            body = payload.decode(charset, errors='replace')
                                        except:
                                            body = payload.decode('utf-8', errors='replace')
                                        break
                            else:
                                payload = msg.get_payload(decode=True)
                                charset = msg.get_content_charset() or 'utf-8'
                                try:
                                    body = payload.decode(charset, errors='replace')
                                except:
                                    body = payload.decode('utf-8', errors='replace')
                            
                            # Clean HTML if present
                            body = re.sub('<[^<]+?>', '', body) # Simple tag removal
                            
                            body_lower = body.lower()
                            subject_lower = subject.lower()

                            # --- extraction of Tracking and Carrier ---
                            tracking = None
                            carrier = None
                            site_order_id = None
                            
                            # Clean body and subject for extraction
                            content_to_scan = f"{subject} {body}"
                            content_to_scan_lower = content_to_scan.lower()

                            # Identification of carrier (preliminary)
                            if any(kw in content_to_scan_lower for kw in ["too good to go", "to good to go", "tgtg"]):
                                carrier = "Too Good To Go"
                            elif "too good to go" in folder.lower() or "tgtg" in folder.lower():
                                carrier = "Too Good To Go"
                            elif any(kw in content_to_scan_lower for kw in ["amazon"]):
                                carrier = "Amazon"
                            elif any(kw in content_to_scan_lower for kw in ["temu"]):
                                carrier = "Temu"
                            elif any(kw in content_to_scan_lower for kw in ["ebay"]):
                                carrier = "eBay"

                            # 2. Extraction of Site Order ID (Amazon, Temu, eBay etc.)
                            amazon_match = re.search(r'(\d{3}-\d{7}-\d{7})', content_to_scan)
                            temu_match = re.search(r'(PO-\d{3}-\d{15,20})', content_to_scan)
                            ebay_match = re.search(r'(\d{2}-\d{5}-\d{5})', content_to_scan)
                            # Pattern TGTG: ID ordine, Prenotazione oppure il nuovo pattern "spedizione" seguito da codice (due punti opzionali, allow some words between)
                            tgtg_match = re.search(r'(?:ID ordine|Order ID|ordine|prenotazione|spedizione|sacchetto):?.*?\b([a-z0-9]{8,15})\b', content_to_scan, re.IGNORECASE | re.DOTALL)
                            
                            if amazon_match:
                                site_order_id = amazon_match.group(1)
                                carrier = "Amazon"
                            elif temu_match:
                                site_order_id = temu_match.group(1)
                                carrier = "Temu"
                            elif ebay_match:
                                site_order_id = ebay_match.group(1)
                                carrier = "eBay"
                            elif tgtg_match:
                                site_order_id = tgtg_match.group(1)
                                carrier = "Too Good To Go"

                            # 3. Tracking patterns (standard)
                            tracking_patterns = [
                                r'(1Z[A-Z0-9]{16})',  # UPS
                                r'(\d{10,14})',       # FedEx/DHL/GLS
                                r'(0034\d{16})',      # Poste Italiane
                                r'([A-Z0-9]{10,25})'  # Generic alphanumeric (at the end)
                            ]
                            
                            for pattern in tracking_patterns:
                                if tracking: break
                                matches = re.finditer(pattern, content_to_scan)
                                for match in matches:
                                    potential = match.group(1)
                                    if site_order_id and potential in site_order_id:
                                        continue
                                    # Very basic heuristic: if it's in the subject or near "tracking" or "spedizione" keyword
                                    if potential in subject or any(kw in content_to_scan_lower for kw in ["tracking", "spedizione", "consuln"]):
                                        tracking = potential
                                        break

                            if not carrier:
                                if any(kw in subject_lower or kw in body_lower for kw in ["too good to go", "to good to go"]):
                                    carrier = "Too Good To Go"
                                elif "too good to go" in folder.lower() or "to good to go" in folder.lower():
                                    carrier = "Too Good To Go"

                            # --- extraction of status - EN/IT keywords ---
                            status = None
                            
                            # 1. Subject priority: if subject says delivered/shipped, that's it.
                            if any(kw in subject_lower for kw in ["consegnato", "delivered", "consegna effettuata", "handed over"]):
                                status = "Consegnato"
                            elif any(kw in subject_lower for kw in ["in consegna", "out for delivery", "arriverà oggi"]):
                                status = "In Consegna"
                            elif any(kw in subject_lower for kw in ["spedito", "shipped", "invio", "dispatched", "sent", "partito"]):
                                status = "Spedito"
                            
                            # 2. Identify if it's just a confirmation: if so, we don't want "Delivered" from body
                            is_confirmation = any(kw in subject_lower for kw in ["conferma", "ricevuto", "grazie", "thank you", "confirmed", "riepilogo"])
                            
                             # 3. Body check (only if status not found in subject)
                            if not status:
                                # For Delivered: be more restrictive in body (avoid "will be delivered on...")
                                if any(kw in body_lower for kw in ["consegna effettuata", "consegnato il", "consegnata il", "stato consegnato", "stata consegnata", "delivered on"]):
                                    # Confirmation emails often say "will be delivered", so we only accept "delivered on" or similar
                                    if not is_confirmation:
                                        status = "Consegnato"
                                
                                elif any(kw in body_lower for kw in ["in consegna", "out for delivery", "today", "oggi"]):
                                    status = "In Consegna"
                                
                                elif any(kw in body_lower for kw in ["in transito", "in transit", "at sorting", "departed", "assegnato", "assegnazione"]):
                                    status = "In Transito"
                                
                                elif any(kw in body_lower for kw in ["spedito", "shipped", "invio", "dispatched", "sent", "in spedizione"]):
                                    status = "Spedito"
                            
                            # 4. Too Good To Go Specific Mapping
                            if carrier == "Too Good To Go":
                                if any(kw in subject_lower or kw in body_lower for kw in ["grazie per aver salvato", "ordine completato", "ritirato", "sacchetto salvato", "salvato del cibo", "consegnato", "consegnata"]):
                                    status = "Consegnato"
                                elif any(kw in subject_lower or kw in body_lower for kw in ["confermato", "prenotazione", "magico sacchetto", "non dimenticare", "ritiro", "preparato"]):
                                    status = "In Transito"
                                # If we found an Order ID but no clear status, TGTG usually means it's ready/booked
                                if not status:
                                    status = "In Transito"
                            
                            # Default status for confirmation emails if not found otherwise
                            if not status and is_confirmation:
                                status = "In Transito"
                                
                            if any(kw in subject_lower or kw in body_lower for kw in ["eccezione", "problema", "ritardo", "exception", "delay", "address", "failure"]):
                                status = "Problema/Eccezione"
                                
                            updates.append({
                                'email_id': f"{folder}_{e_id.decode()}",
                                'subject': subject,
                                'tracking': tracking,
                                'carrier': carrier,
                                'last_mile_carrier': None,
                                'site_order_id': site_order_id,
                                'status': status,
                                'received_at': final_date,
                                'body_snippet': body[:1000],
                                'folder': folder
                            })
                        except Exception as ex:
                            logger.error(f"EMAIL-SYNC: Errore email {e_id} in {folder}: {ex}")
                except Exception as folder_err:
                    logger.error(f"EMAIL-SYNC: Errore folder {folder}: {folder_err}")
                    
        finally:
            try:
                mail.logout()
            except:
                pass
            
        return updates

    def sync_with_db(self):
        """Match email updates with database orders"""
        logger.info("EMAIL-SYNC: Inizio sync_with_db...")
        try:
            updates = self.fetch_updates()
            logger.info(f"EMAIL-SYNC: Recuperati {len(updates)} potenziali aggiornamenti")
        except Exception as e:
            logger.error(f"EMAIL-SYNC: Errore fatale in fetch_updates: {e}")
            return 0
        
        applied_count = 0
        
        # Load all active orders once (outside the loop for efficiency)
        orders = database.get_orders(include_delivered=False)
        
        for update in updates:
            logger.info(f"EMAIL-SYNC: Tentativo matching per email: '{update['subject']}'")
            logger.info(f"EMAIL-SYNC: Dati estratti: Tracking={update['tracking']}, OrderID={update['site_order_id']}, Status={update['status']}")

            # Collect ALL matching orders (not just the first one).
            # Multiple DB rows can share the same order (e.g. multi-item orders with the
            # same site_order_id or tracking_number). They must all receive the same status.
            matched_orders = []

            # Match against database orders
            matched_ids = set()
            
            # 1. Match by site_order_id (CASE-INSENSITIVE)
            if update.get('site_order_id'):
                u_id = update['site_order_id'].strip().lower()
                for order in orders:
                    if order['id'] in matched_ids: continue
                    o_sid = (order.get('site_order_id') or "").strip().lower()
                    o_tr = (order.get('tracking_number') or "").strip().lower()
                    if u_id == o_sid or u_id == o_tr:
                        matched_orders.append(order)
                        matched_ids.add(order['id'])

            # 2. Match by tracking (CASE-INSENSITIVE, always check)
            if update.get('tracking'):
                u_tr = update['tracking'].strip().lower()
                for order in orders:
                    if order['id'] in matched_ids: continue
                    o_sid = (order.get('site_order_id') or "").strip().lower()
                    o_tr = (order.get('tracking_number') or "").strip().lower()
                    if u_tr == o_tr or u_tr == o_sid:
                        matched_orders.append(order)
                        matched_ids.add(order['id'])

            # 3. Fallback: match by description keywords (only if nothing found above)
            if not matched_orders:
                for order in orders:
                    desc_lower = (order.get('description') or "").lower()
                    if desc_lower and (desc_lower in update['subject'].lower() or desc_lower in update['body_snippet'].lower()):
                        logger.info(f"EMAIL-SYNC: Match trovato tramite descrizione: '{desc_lower}'")
                        matched_orders.append(order)
                        break  # description match is less reliable; take only the best one

            if not matched_orders:
                logger.info("EMAIL-SYNC: Nessun ordine corrispondente trovato in DB per questa email.")
                continue

            logger.info(f"EMAIL-SYNC: {len(matched_orders)} ordine/i corrispondente/i trovato/i.")

            # Pre-compute values shared across all matched orders
            new_status = update.get('status')
            is_delivered_from_subject = any(
                kw in update['subject'].lower()
                for kw in ["consegnato", "delivered", "consegna effettuata"]
            )

            date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', update['body_snippet'])
            parsed_est_delivery = None
            if date_match:
                d, m, y = date_match.groups()
                if len(y) == 2:
                    y = "20" + y
                parsed_est_delivery = f"{y}-{m.zfill(2)}-{d.zfill(2)}"

            # Apply update to EVERY matched order
            for matched_order in matched_orders:
                # Skip if this email was already applied to this specific order
                if matched_order.get('last_email_id') == update['email_id']:
                    continue

                current_status = matched_order.get('status')
                est_delivery = parsed_est_delivery or matched_order.get('estimated_delivery')

                update_data = dict(matched_order)
                update_data['last_email_id'] = update['email_id']
                update_data['last_sync_at'] = datetime.now().isoformat()

                # Update status only if it's an upgrade (never downgrade)
                if new_status and _is_status_upgrade(current_status, new_status):
                    update_data['status'] = new_status
                    if new_status == 'Consegnato':
                        update_data['is_delivered'] = True
                    logger.info(f"EMAIL-SYNC: Ordine {matched_order['id']}: stato '{current_status}' -> '{new_status}'")
                elif new_status:
                    logger.info(f"EMAIL-SYNC: Ordine {matched_order['id']}: stato ignorato (retrocessione) '{current_status}' -> '{new_status}'")

                # Fallback: no status extracted but subject says delivered
                if not new_status and is_delivered_from_subject:
                    if _is_status_upgrade(current_status, 'Consegnato'):
                        update_data['is_delivered'] = True
                        update_data['status'] = 'Consegnato'

                # Persist new info only if the field is currently empty in DB
                if update.get('site_order_id') and not update_data.get('site_order_id'):
                    update_data['site_order_id'] = update['site_order_id']
                if update.get('tracking') and not update_data.get('tracking_number'):
                    update_data['tracking_number'] = update['tracking']
                if update.get('carrier') and not update_data.get('carrier'):
                    update_data['carrier'] = update['carrier']
                if update.get('last_mile_carrier') and not update_data.get('last_mile_carrier'):
                    update_data['last_mile_carrier'] = update['last_mile_carrier']

                # Update estimated delivery only if not yet delivered and date changed
                if not update_data.get('is_delivered') and parsed_est_delivery and parsed_est_delivery != matched_order.get('estimated_delivery'):
                    update_data['estimated_delivery'] = parsed_est_delivery

                # Append a note about the email update
                new_note = f"\n[Aggiornamento Email {datetime.now().strftime('%d/%m/%Y')}]: {update['subject']}"
                update_data['notes'] = (update_data.get('notes') or "") + new_note

                if database.update_order(matched_order['id'], update_data):
                    applied_count += 1
                    logger.info(f"EMAIL-SYNC: Ordine {matched_order['id']} aggiornato da email: {update['subject']}")

        return applied_count
