"""
Configuration module for Delivery Tracker application.
Contains all application settings, themes, and constants.
"""
from dataclasses import dataclass
from typing import Dict, Tuple
from enum import Enum

# Application Info
APP_NAME = "Scadenziario Consegne"
APP_VERSION = "2.1.0"
APP_AUTHOR = "Massimo Lo Sciuto"
APP_SUPPORT = "Antigravity"
APP_DEVELOPER = "Gemini 3 Pro"

# Database
DB_NAME = "delivery_tracker.db"
BACKUP_DIR = "backups"

# UI Constants
SIDEBAR_WIDTH_EXPANDED = 220
SIDEBAR_WIDTH_COLLAPSED = 60
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 700
ICON_SIZE = 24

class Theme(Enum):
    """Theme enumeration for light/dark modes"""
    LIGHT = "light"
    DARK = "dark"

@dataclass
class ColorScheme:
    """Color scheme for the application"""
    # Primary colors
    primary: str
    primary_hover: str
    primary_pressed: str
    
    # Background colors
    bg_main: str
    bg_secondary: str
    bg_sidebar: str
    bg_table: str
    bg_table_alternate: str
    
    # Text colors
    text_primary: str
    text_secondary: str
    text_link: str
    
    # Border colors
    border: str
    border_light: str
    
    # Status colors
    success: str
    warning: str
    error: str
    info: str
    
    # Delivery status colors
    delivered: str
    overdue: str
    due_today: str
    upcoming: str

# Light Theme
LIGHT_THEME = ColorScheme(
    primary="#2196F3",
    primary_hover="#1976D2",
    primary_pressed="#0D47A1",
    bg_main="#FAFAFA",
    bg_secondary="#FFFFFF",
    bg_sidebar="#E3F2FD",
    bg_table="#FFFFFF",
    bg_table_alternate="#F5F5F5",
    text_primary="#212121",
    text_secondary="#757575",
    text_link="#1976D2",
    border="#E0E0E0",
    border_light="#F5F5F5",
    success="#4CAF50",
    warning="#FF9800",
    error="#F44336",
    info="#2196F3",
    delivered="#C8E6C9",
    overdue="#FFCDD2",
    due_today="#FFE082",
    upcoming="#FFF9C4"
)

# Dark Theme
DARK_THEME = ColorScheme(
    primary="#42A5F5",
    primary_hover="#1E88E5",
    primary_pressed="#1565C0",
    bg_main="#121212",
    bg_secondary="#1E1E1E",
    bg_sidebar="#1A237E",
    bg_table="#1E1E1E",
    bg_table_alternate="#252525",
    text_primary="#FFFFFF",
    text_secondary="#B0B0B0",
    text_link="#64B5F6",
    border="#424242",
    border_light="#303030",
    success="#66BB6A",
    warning="#FFA726",
    error="#EF5350",
    info="#42A5F5",
    delivered="#2E7D32",
    overdue="#C62828",
    due_today="#F57C00",
    upcoming="#F9A825"
)

# Default settings
DEFAULT_SETTINGS = {
    'theme': Theme.LIGHT.value,
    'auto_backup': True,
    'backup_interval_days': 7,
    'notification_enabled': True,
    'notification_days_before': 2,
    'default_delivery_days': 7,
    'language': 'it',
    'date_format': '%d/%m/%Y',
    'show_delivered': True,
    'auto_refresh_minutes': 5
}

# Export formats
EXPORT_FORMATS = {
    'CSV': '.csv',
    'Excel': '.xlsx',
    'JSON': '.json'
}

# Platforms (predefined suggestions) - Expanded list
COMMON_PLATFORMS = [
    "Amazon",
    "Amazon.it",
    "eBay",
    "AliExpress",
    "Alibaba",
    "Etsy",
    "Wish",
    "Shein",
    "Temu",
    "Zalando",
    "ASOS",
    "Vinted",
    "Subito.it",
    "Wallapop",
    "Depop",
    "Banggood",
    "Gearbest",
    "DHgate",
    "Joom",
    "LightInTheBox",
    "Farfetch",
    "Yoox",
    "MediaWorld",
    "Unieuro",
    "Euronics",
    "Decathlon",
    "Ikea",
    "Leroy Merlin",
    "Zara",
    "H&M",
    "Altro"
]

# Categories/Tags - Expanded list
DEFAULT_CATEGORIES = [
    "Elettronica",
    "Computer e Accessori",
    "Smartphone e Tablet",
    "Fotografia e Video",
    "Audio e Hi-Fi",
    "Abbigliamento",
    "Scarpe",
    "Accessori Moda",
    "Borse e Valigie",
    "Orologi e Gioielli",
    "Casa e Cucina",
    "Arredamento",
    "Giardino e Fai da Te",
    "Elettrodomestici",
    "Libri",
    "Musica e Film",
    "Videogiochi e Console",
    "Giocattoli",
    "Prima Infanzia",
    "Sport e Tempo Libero",
    "Outdoor e Campeggio",
    "Fitness e Palestra",
    "Alimentari e Bevande",
    "Salute e Bellezza",
    "Cura della Persona",
    "Animali Domestici",
    "Auto e Moto",
    "Ufficio e Scuola",
    "Strumenti Musicali",
    "Attrezzi",
    "Hobby e Collezionismo",
    "Altro"
]

# Order Statuses
ORDER_STATUSES = [
    "In Attesa",
    "Spedito",
    "In Transito",
    "In Consegna",
    "Consegnato",
    "Problema/Eccezione"
]

