"""
Utility functions for the Delivery Tracker application.
Includes logging, validation, formatting, and helper functions.
"""
import os
import json
import logging
import shutil
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List
import base64
import requests
from pathlib import Path
import config

# Setup logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f'app_{date.today()}.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class Settings:
    """Application settings manager"""
    SETTINGS_FILE = "settings.json"
    
    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Load settings from file"""
        try:
            if os.path.exists(cls.SETTINGS_FILE):
                with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    logger.info("Settings loaded successfully")
                    return {**config.DEFAULT_SETTINGS, **settings}
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
        
        return config.DEFAULT_SETTINGS.copy()
    
    @classmethod
    def save(cls, settings: Dict[str, Any]) -> bool:
        """Save settings to file"""
        try:
            with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            logger.info("Settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False


class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        if not url:
            return True  # Empty URL is valid
        return url.startswith(('http://', 'https://'))
    
    @staticmethod
    def validate_quantity(qty: str) -> tuple[bool, Optional[int]]:
        """Validate quantity input"""
        try:
            value = int(qty)
            if value > 0:
                return True, value
            return False, None
        except ValueError:
            return False, None
    
    @staticmethod
    def validate_date(date_str: str, format_str: str = '%Y-%m-%d') -> tuple[bool, Optional[date]]:
        """Validate date string"""
        try:
            parsed_date = datetime.strptime(date_str, format_str).date()
            return True, parsed_date
        except ValueError:
            return False, None
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required: List[str]) -> tuple[bool, List[str]]:
        """Validate required fields in data dictionary"""
        missing = [field for field in required if not data.get(field)]
        return len(missing) == 0, missing


class DateHelper:
    """Date manipulation and formatting utilities"""
    
    @staticmethod
    def format_date(date_obj: date, format_str: str = '%d/%m/%Y') -> str:
        """Format date object to string"""
        return date_obj.strftime(format_str)
    
    @staticmethod
    def parse_date(date_str: str, format_str: str = '%Y-%m-%d') -> Optional[date]:
        """Parse date string to date object"""
        try:
            return datetime.strptime(date_str, format_str).date()
        except ValueError:
            return None
    
    @staticmethod
    def days_until(target_date: date) -> int:
        """Calculate days until target date"""
        return (target_date - date.today()).days
    
    @staticmethod
    def is_overdue(target_date: date) -> bool:
        """Check if date is overdue"""
        return target_date < date.today()
    
    @staticmethod
    def is_due_today(target_date: date) -> bool:
        """Check if date is today"""
        return target_date == date.today()
    
    @staticmethod
    def is_upcoming(target_date: date, days: int = 2) -> bool:
        """Check if date is upcoming within specified days"""
        delta = DateHelper.days_until(target_date)
        return 0 < delta <= days
    
    @staticmethod
    def get_date_status(target_date: date, days_threshold: int = 2) -> str:
        """Get status string for a date"""
        if DateHelper.is_overdue(target_date):
            return "overdue"
        elif DateHelper.is_due_today(target_date):
            return "due_today"
        elif DateHelper.is_upcoming(target_date, days_threshold):
            return "upcoming"
        return "normal"

    @staticmethod
    def parse_smart(date_str: str) -> Optional[date]:
        """Try to parse date string using multiple formats and languages"""
        if not date_str or not isinstance(date_str, str):
            if isinstance(date_str, (date, datetime)):
                return date_str if isinstance(date_str, date) else date_str.date()
            return None
            
        date_str = date_str.lower().strip()
        
        # Standard formats
        formats = [
            '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', 
            '%Y/%m/%d', '%d.%m.%Y', '%m/%d/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
                
        # Natural language (Italian/English)
        months_it = {
            'gen': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mag': 5, 'giu': 6,
            'lug': 7, 'ago': 8, 'set': 9, 'ott': 10, 'nov': 11, 'dic': 12,
            'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5,
            'giugno': 6, 'luglio': 7, 'agosto': 8, 'settembre': 9,
            'ottobre': 10, 'novembre': 11, 'dicembre': 12
        }
        months_en = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5,
            'june': 6, 'july': 7, 'august': 8, 'september': 9,
            'october': 10, 'november': 11, 'december': 12
        }
        
        all_months = {**months_it, **months_en}
        
        # Try to match formats like "14 feb 2026" or "feb 14, 2026"
        import re
        parts = re.split(r'[,.\s/-]+', date_str)
        
        day = None
        month = None
        year = None
        
        for p in parts:
            if p in all_months:
                month = all_months[p]
            elif p.isdigit():
                val = int(p)
                if val > 2000:
                    year = val
                elif val <= 31:
                    if day is None:
                        day = val
                    else:
                        # Could be month digit
                        if month is None and val <= 12:
                            month = val
                        else:
                            # Already have day, maybe this is year in 2-digit?
                            if year is None: year = 2000 + val
                            
        if day and month and year:
            try:
                return date(year, month, day)
            except ValueError:
                pass
                
        return None


class BackupManager:
    """Database backup management"""
    
    @staticmethod
    def create_backup() -> tuple[bool, Optional[str]]:
        """Create a backup of the database"""
        try:
            os.makedirs(config.BACKUP_DIR, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}.db"
            backup_path = os.path.join(config.BACKUP_DIR, backup_name)
            
            if os.path.exists(config.DB_NAME):
                shutil.copy2(config.DB_NAME, backup_path)
                logger.info(f"Backup created: {backup_path}")
                
                # Clean old backups (keep last 10)
                BackupManager._cleanup_old_backups(keep=10)
                
                return True, backup_path
            else:
                logger.warning("Database file not found for backup")
                return False, None
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False, None
    
    @staticmethod
    def restore_backup(backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            if os.path.exists(backup_path):
                # Create a backup of current DB before restoring
                if os.path.exists(config.DB_NAME):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    temp_backup = f"{config.DB_NAME}.before_restore_{timestamp}"
                    shutil.copy2(config.DB_NAME, temp_backup)
                
                shutil.copy2(backup_path, config.DB_NAME)
                logger.info(f"Database restored from: {backup_path}")
                return True
            else:
                logger.error(f"Backup file not found: {backup_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    @staticmethod
    def list_backups() -> List[tuple[str, str, int]]:
        """List all available backups with metadata"""
        backups = []
        
        if os.path.exists(config.BACKUP_DIR):
            for filename in sorted(os.listdir(config.BACKUP_DIR), reverse=True):
                if filename.endswith('.db'):
                    filepath = os.path.join(config.BACKUP_DIR, filename)
                    stat = os.stat(filepath)
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M')
                    backups.append((filename, mtime, size))
        
        return backups
    
    @staticmethod
    def _cleanup_old_backups(keep: int = 10):
        """Remove old backups, keeping only the most recent ones"""
        try:
            if os.path.exists(config.BACKUP_DIR):
                backups = sorted(
                    [f for f in os.listdir(config.BACKUP_DIR) if f.endswith('.db')],
                    reverse=True
                )
                
                for old_backup in backups[keep:]:
                    os.remove(os.path.join(config.BACKUP_DIR, old_backup))
                    logger.info(f"Removed old backup: {old_backup}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")


class FileHelper:
    """File operations helper"""
    
    @staticmethod
    def get_file_size_str(size_bytes: int) -> str:
        """Convert bytes to human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    @staticmethod
    def ensure_dir(directory: str):
        """Ensure directory exists"""
        os.makedirs(directory, exist_ok=True)


class StatisticsCalculator:
    """Calculate statistics from orders data"""
    
    @staticmethod
    def calculate_stats(orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        total = len(orders)
        delivered = sum(1 for o in orders if o['is_delivered'])
        pending = total - delivered
        
        overdue = 0
        due_today = 0
        upcoming = 0
        
        platforms = {}
        
        for order in orders:
            # Platform stats
            platform = order.get('platform', 'Unknown')
            platforms[platform] = platforms.get(platform, 0) + 1
            
            # Date stats (only for non-delivered)
            if not order['is_delivered'] and order.get('estimated_delivery'):
                est_date = DateHelper.parse_date(order['estimated_delivery'])
                if est_date:
                    status = DateHelper.get_date_status(est_date)
                    if status == 'overdue':
                        overdue += 1
                    elif status == 'due_today':
                        due_today += 1
                    elif status == 'upcoming':
                        upcoming += 1
        
        return {
            'total': total,
            'delivered': delivered,
            'pending': pending,
            'overdue': overdue,
            'due_today': due_today,
            'upcoming': upcoming,
            'platforms': platforms,
            'delivery_rate': (delivered / total * 100) if total > 0 else 0
        }


class TextMatcher:
    """Utility for fuzzy text matching and tokenization"""
    
    @staticmethod
    def get_tokens(text: str) -> set[str]:
        """Lowercase, keep alphanumeric tokens only, ignore very short words"""
        if not text:
            return set()
        import re
        # Support various languages by keeping word characters
        words = re.findall(r'\w+', str(text).lower())
        return {w for w in words if len(w) > 1}

    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate similarity between two strings using token intersection ratio"""
        tokens1 = TextMatcher.get_tokens(text1)
        tokens2 = TextMatcher.get_tokens(text2)
        
        if not tokens1 or not tokens2:
            return 0.0
            
        intersection = tokens1.intersection(tokens2)
        # Ratio of common tokens to the larger set size
        return len(intersection) / max(len(tokens1), len(tokens2))


def get_stylesheet(theme='light'):
    """Get application stylesheet based on theme"""
    
    # Load theme colors
    colors = config.LIGHT_THEME if theme == 'light' else config.DARK_THEME
    
    return f"""
        /* Global Styles */
        * {{
            font-family: 'Segoe UI', 'San Francisco', 'Helvetica Neue', Arial, sans-serif;
        }}
        
        QMainWindow {{
            background-color: {colors.bg_main};
        }}
        
        /* Sidebar Styles */
        QWidget#sidebar {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors.bg_sidebar}, stop:1 #1565C0);
            border-right: 2px solid {colors.border};
        }}
        
        QWidget#sidebar QPushButton {{
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            border: none;
            padding: 10px 15px;
            text-align: left;
            font-size: 14px;
            font-weight: 500;
            border-radius: 6px;
            margin: 2px 0;
        }}
        
        QWidget#sidebar QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.2);
        }}
        
        QWidget#sidebar QPushButton:pressed {{
            background-color: rgba(255, 255, 255, 0.3);
        }}
        
        QWidget#sidebar QLabel {{
            color: rgba(255, 255, 255, 0.7);
            font-weight: normal;
        }}
        
        /* Table Styles */
        QTableWidget {{
            background-color: {colors.bg_table};
            alternate-background-color: {colors.bg_table_alternate};
            selection-background-color: {colors.primary};
            selection-color: white;
            border: 1px solid {colors.border};
            border-radius: 8px;
            gridline-color: {colors.border_light};
        }}
        
        QHeaderView::section {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {colors.primary}, stop:1 {colors.primary_hover});
            color: white;
            padding: 8px;
            border: none;
            border-right: 1px solid rgba(255, 255, 255, 0.2);
            font-weight: bold;
            font-size: 13px;
        }}
        
        QHeaderView::section:hover {{
            background: {colors.primary_hover};
        }}
        
        QTableWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {colors.border_light};
        }}
        
        QTableWidget::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}
        
        /* Dialog Styles */
        QDialog {{
            background-color: {colors.bg_secondary};
        }}
        
        QDialog QPushButton {{
            background-color: {colors.primary};
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 500;
            min-width: 80px;
        }}
        
        QDialog QPushButton:hover {{
            background-color: {colors.primary_hover};
        }}
        
        QDialog QPushButton:pressed {{
            background-color: {colors.primary_pressed};
        }}
        
        /* Input Styles */
        QLineEdit, QDateEdit, QTextEdit, QComboBox {{
            padding: 8px;
            border: 2px solid {colors.border};
            border-radius: 6px;
            background-color: {colors.bg_secondary};
            color: {colors.text_primary};
            selection-background-color: {colors.primary};
        }}
        
        QLineEdit:focus, QDateEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border: 2px solid {colors.primary};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 25px;
            border-left: 1px solid {colors.border};
            background-color: {colors.bg_secondary};
        }}
        
        QComboBox::drop-down:hover {{
            background-color: {colors.border_light};
        }}
        
        QComboBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {colors.text_primary};
            margin-right: 5px;
        }}
        
        QComboBox::down-arrow:hover {{
            border-top-color: {colors.primary};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors.bg_secondary};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            selection-background-color: {colors.primary};
            selection-color: white;
            padding: 4px;
        }}
        
        QComboBox QAbstractItemView::item {{
            padding: 6px;
            border-radius: 4px;
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background-color: {colors.primary};
            color: white;
        }}
        
        /* GroupBox Styles */
        QGroupBox {{
            font-weight: bold;
            font-size: 14px;
            border: 2px solid {colors.border};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: {colors.bg_secondary};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 4px 10px;
            color: {colors.primary};
        }}
        
        /* Label Styles */
        QLabel {{
            color: {colors.text_primary};
        }}
        
        QFormLayout QLabel {{
            font-weight: 500;
            color: {colors.text_secondary};
        }}
        
        /* CheckBox Styles */
        QCheckBox {{
            spacing: 8px;
            color: {colors.text_primary};
        }}
        
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {colors.border};
            border-radius: 4px;
            background-color: {colors.bg_secondary};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors.primary};
            border-color: {colors.primary};
        }}
        
        /* ScrollBar Styles */
        QScrollBar:vertical {{
            border: none;
            background: {colors.bg_table_alternate};
            width: 12px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background: {colors.border};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {colors.primary};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        /* MenuBar Styles */
        QMenuBar {{
            background-color: {colors.bg_secondary};
            color: {colors.text_primary};
            border-bottom: 1px solid {colors.border};
            padding: 4px;
        }}
        
        QMenuBar::item {{
            padding: 6px 12px;
            border-radius: 4px;
            color: {colors.text_primary};
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}
        
        QMenuBar::item:pressed {{
            background-color: {colors.primary_pressed};
            color: white;
        }}
        
        QMenu {{
            background-color: {colors.bg_secondary};
            color: {colors.text_primary};
            border: 1px solid {colors.border};
            border-radius: 6px;
            padding: 4px;
        }}
        
        QMenu::item {{
            padding: 8px 24px;
            border-radius: 4px;
            color: {colors.text_primary};
        }}
        
        QMenu::item:selected {{
            background-color: {colors.primary};
            color: white;
        }}
        
        /* MessageBox Styles */
        QMessageBox {{
            background-color: {colors.bg_secondary};
            color: {colors.text_primary};
        }}
        
        QMessageBox QLabel {{
            color: {colors.text_primary};
        }}
        
        QMessageBox QPushButton {{
            min-width: 80px;
            padding: 8px 16px;
        }}
        
        /* Tooltip Styles */
        QToolTip {{
            background-color: {colors.text_primary};
            color: {colors.bg_secondary};
            border: 1px solid {colors.border};
            border-radius: 4px;
            padding: 6px;
        }}
    """


class ImageDownloader:
    """Utility for downloading images and converting to binary/base64"""
    
    @staticmethod
    def download_image(url: str) -> Optional[bytes]:
        """Download image from URL and return as bytes"""
        if not url:
            return None
        
        # Le miniature in formato AVIF non sono sempre compatibili con PyQt6.
        # Spesso URL come quelli di Temu terminano con format/avif, possiamo forzare jpeg.
        import re
        if 'format/avif' in url:
            url = url.replace('format/avif', 'format/jpeg')

        try:
            # Add common user-agent to avoid being blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Basic check if it's an image
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type and not url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                logger.warning(f"URL might not be an image: {url} (Content-Type: {content_type})")
            
            return response.content
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None

    @staticmethod
    def to_base64(image_data: bytes) -> Optional[str]:
        """Convert binary image data to base64 string for HTML use"""
        if not image_data:
            return None
        try:
            encoded = base64.b64encode(image_data).decode('utf-8')
            # We don't know the exact mime type here, so we use a generic placeholder or try to infer
            # JPEG/PNG are safest defaults for web.
            return f"data:image/png;base64,{encoded}"
        except Exception as e:
            logger.error(f"Error encoding image to base64: {e}")
            return None


class TrackingHelper:
    """Utility for generating tracking URLs for various carriers"""
    
    TRACKING_URLS = {
        'Amazon': 'https://www.amazon.it/gp/your-account/order-history',
        'Amazon.it': 'https://www.amazon.it/gp/your-account/order-history',
        'UPS': 'https://www.ups.com/track?loc=it_IT&tracknum={number}',
        'DHL': 'https://www.dhl.com/it-it/home/tracciamento.html?tracking_number={number}',
        'FedEx': 'https://www.fedex.com/fedextrack/?tracknumbers={number}',
        'GLS': 'https://www.gls-italy.com/it/servizi-per-te/m-tracking?view=mtracking&tracknum={number}',
        'Poste Italiane': 'https://www.poste.it/cerca/index.html#/risultati-spedizioni/{number}',
        'BRT': 'https://www.brt.it/it/tracking?n_spedizione={number}',
        'SDA': 'https://www.sda.it/wps/portal/SDAit/IT/Tracking?consegna={number}',
        'Too Good To Go': 'https://toogoodtogo.it/it', # TGTG doesn't have public tracking page, usually handled in-app
        'AliExpress': 'https://global.cainiao.com/detail.htm?mailNo={number}',
        'Temu': 'https://www.temu.com/it/order-list.html',
        'Shein': 'https://www.shein.com/user/order/list',
        'Vinted': 'https://www.vinted.it/member/items/purchased',
        'eBay': 'https://www.ebay.it/sh/ord',
    }
    
    @classmethod
    def get_tracking_url(cls, number: str, carrier: Optional[str] = None) -> Optional[str]:
        """Generate a tracking URL based on number and carrier"""
        if not number:
            return None
            
        number = str(number).strip()
        carrier = (carrier or "").strip()
        
        # 1. Match by carrier if provided
        if carrier in cls.TRACKING_URLS:
            url_template = cls.TRACKING_URLS[carrier]
            if '{number}' in url_template:
                return url_template.format(number=number)
            return url_template
            
        # 2. Heuristic matching if carrier is unknown or not in list
        if re.match(r'^1Z[A-Z0-9]{16}$', number, re.IGNORECASE):
            return cls.TRACKING_URLS['UPS'].format(number=number)
        elif re.match(r'^\d{10,12}$', number):
            # Could be many things, but Poste Italiane/DHL are common
            return cls.TRACKING_URLS['Poste Italiane'].format(number=number)
        elif re.match(r'^[A-Z]{2}\d{9}[A-Z]{2}$', number, re.IGNORECASE):
            # EMS/Poste Italiane standard
            return cls.TRACKING_URLS['Poste Italiane'].format(number=number)
            
        # 3. Fallback to generic Cainiao for international stuff if it looks like tracking
        if len(number) > 8 and re.match(r'^[A-Z0-9]+$', number):
            return cls.TRACKING_URLS['AliExpress'].format(number=number)
            
        return None


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
