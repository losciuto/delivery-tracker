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


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
