"""
Enhanced database module for Delivery Tracker.
Includes optimizations, indices, categories, attachments, and export functionality.
"""
import sqlite3
import csv
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, Generator
from contextlib import contextmanager
import utils

logger = utils.get_logger(__name__)

DB_NAME = "delivery_tracker.db"


def get_db_connection() -> sqlite3.Connection:
    """Get database connection with row factory"""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise


@contextmanager
def db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    """Context manager for database cursor with auto-commit/rollback"""
    conn = get_db_connection()
    try:
        yield conn.cursor()
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Database error in cursor context: {e}")
        raise
    except Exception as e:
        conn.rollback()
        logger.error(f"Unexpected error in cursor context: {e}")
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database with all tables and indices"""
    try:
        with db_cursor() as cursor:
            # Main orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_date TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    seller TEXT,
                    destination TEXT,
                    description TEXT NOT NULL,
                    link TEXT,
                    quantity INTEGER DEFAULT 1,
                    estimated_delivery TEXT,
                    alarm_enabled BOOLEAN DEFAULT 1,
                    is_delivered BOOLEAN DEFAULT 0,
                    position TEXT,
                    notes TEXT,
                    category TEXT,
                    last_email_id TEXT,
                    last_sync_at TEXT,
                    tracking_number TEXT,
                    carrier TEXT,
                    last_mile_carrier TEXT,
                    site_order_id TEXT,
                    status TEXT DEFAULT 'In Attesa',
                    price REAL,
                    image_url TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Attachments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    file_size INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                )
            ''')
            
            # Create indices for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_delivery ON orders(estimated_delivery)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_platform ON orders(platform)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_delivered ON orders(is_delivered)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_category ON orders(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attachments_order ON attachments(order_id)')
            
            # Migration: Add new columns if they don't exist
            cursor.execute("PRAGMA table_info(orders)")
            columns = [column[1] for column in cursor.fetchall()]
            
            migrations = [
                ('position', 'ALTER TABLE orders ADD COLUMN position TEXT'),
                ('category', 'ALTER TABLE orders ADD COLUMN category TEXT'),
                ('last_email_id', 'ALTER TABLE orders ADD COLUMN last_email_id TEXT'),
                ('last_sync_at', 'ALTER TABLE orders ADD COLUMN last_sync_at TEXT'),
                ('tracking_number', 'ALTER TABLE orders ADD COLUMN tracking_number TEXT'),
                ('carrier', 'ALTER TABLE orders ADD COLUMN carrier TEXT'),
                ('last_mile_carrier', 'ALTER TABLE orders ADD COLUMN last_mile_carrier TEXT'),
                ('site_order_id', 'ALTER TABLE orders ADD COLUMN site_order_id TEXT'),
                ('status', "ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'In Attesa'"),
                ('created_at', 'ALTER TABLE orders ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP'),
                ('updated_at', 'ALTER TABLE orders ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP'),
                ('price', 'ALTER TABLE orders ADD COLUMN price REAL'),
                ('image_url', 'ALTER TABLE orders ADD COLUMN image_url TEXT'),
            ]
            
            for column_name, migration_sql in migrations:
                if column_name not in columns:
                    cursor.execute(migration_sql)
                    logger.info(f"Added column: {column_name}")
            
            logger.info("Database initialized successfully")
            
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise


def add_order(order_data: Dict[str, Any]) -> Optional[int]:
    """Add a new order to database"""
    try:
        with db_cursor() as cursor:
            cursor.execute('''
                INSERT INTO orders (
                    order_date, platform, seller, destination, description, 
                    link, quantity, estimated_delivery, alarm_enabled, 
                    is_delivered, position, notes, category,
                    tracking_number, carrier, last_mile_carrier, site_order_id,
                    status, price, image_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order_data['order_date'],
                order_data['platform'],
                order_data.get('seller', ''),
                order_data.get('destination', ''),
                order_data['description'],
                order_data.get('link', ''),
                order_data.get('quantity', 1),
                order_data.get('estimated_delivery', ''),
                order_data.get('alarm_enabled', True),
                order_data.get('is_delivered', False),
                order_data.get('position', ''),
                order_data.get('notes', ''),
                order_data.get('category', ''),
                order_data.get('tracking_number', ''),
                order_data.get('carrier', ''),
                order_data.get('last_mile_carrier', ''),
                order_data.get('site_order_id', ''),
                order_data.get('status', 'In Attesa'),
                order_data.get('price', None),
                order_data.get('image_url', ''),
            ))
            
            order_id = cursor.lastrowid
            logger.info(f"Order added successfully: ID {order_id}")
            return order_id
        
    except Exception as e:
        logger.error(f"Error adding order: {e}")
        return None


def get_orders(include_delivered: bool = True, search: str = '', 
               platform_filter: str = '', category_filter: str = '') -> List[Dict[str, Any]]:
    """Get orders with optional filters"""
    try:
        # We use get_db_connection directly for reads to avoid transaction overhead of context manager
        # or we could implement a read-only context manager. 
        # For simplicity/consistency, let's use standard connection for reads.
        conn = get_db_connection()
        try:
            query = 'SELECT * FROM orders WHERE 1=1'
            params = []
            
            if not include_delivered:
                query += ' AND is_delivered = 0'
            
            if search:
                query += ' AND (description LIKE ? OR seller LIKE ? OR notes LIKE ?)'
                search_param = f'%{search}%'
                params.extend([search_param, search_param, search_param])
            
            if platform_filter:
                query += ' AND platform = ?'
                params.append(platform_filter)
            
            if category_filter:
                query += ' AND category = ?'
                params.append(category_filter)
            
            query += ' ORDER BY created_at DESC, estimated_delivery ASC'
            
            cursor = conn.execute(query, params)
            orders = cursor.fetchall()
            return [dict(order) for order in orders]
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return []


def get_order_by_id(order_id: int) -> Optional[Dict[str, Any]]:
    """Get a single order by ID"""
    try:
        conn = get_db_connection()
        try:
            order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
            return dict(order) if order else None
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {e}")
        return None


def update_order(order_id: int, order_data: Dict[str, Any]) -> bool:
    """Update an existing order"""
    try:
        with db_cursor() as cursor:
            cursor.execute('''
                UPDATE orders SET
                    order_date = ?,
                    platform = ?,
                    seller = ?,
                    destination = ?,
                    description = ?,
                    link = ?,
                    quantity = ?,
                    estimated_delivery = ?,
                    alarm_enabled = ?,
                    is_delivered = ?,
                    position = ?,
                    notes = ?,
                    category = ?,
                    last_email_id = ?,
                    last_sync_at = ?,
                    tracking_number = ?,
                    carrier = ?,
                    last_mile_carrier = ?,
                    site_order_id = ?,
                    status = ?,
                    price = ?,
                    image_url = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                order_data['order_date'],
                order_data['platform'],
                order_data.get('seller', ''),
                order_data.get('destination', ''),
                order_data['description'],
                order_data.get('link', ''),
                order_data.get('quantity', 1),
                order_data.get('estimated_delivery', ''),
                order_data.get('alarm_enabled', True),
                order_data.get('is_delivered', False),
                order_data.get('position', ''),
                order_data.get('notes', ''),
                order_data.get('category', ''),
                order_data.get('last_email_id', ''),
                order_data.get('last_sync_at', ''),
                order_data.get('tracking_number', ''),
                order_data.get('carrier', ''),
                order_data.get('last_mile_carrier', ''),
                order_data.get('site_order_id', ''),
                order_data.get('status', 'In Attesa'),
                order_data.get('price', None),
                order_data.get('image_url', ''),
                order_id
            ))
            
            logger.info(f"Order updated successfully: ID {order_id}")
            return True
        
    except Exception as e:
        logger.error(f"Error updating order {order_id}: {e}")
        return False


def merge_order_data(order_id: int, new_data: Dict[str, Any]) -> bool:
    """
    Merge new data into an existing order.
    Only fills fields that are currently empty or have default values.
    """
    try:
        existing = get_order_by_id(order_id)
        if not existing:
            return False

        merged_data = dict(existing)
        
        # Fields to potentially update if empty in DB
        fields_to_merge = [
            'seller', 'destination', 'link', 'estimated_delivery', 
            'position', 'category', 'tracking_number', 'carrier', 
            'last_mile_carrier', 'site_order_id', 'price', 'image_url'
        ]

        changes_made = False
        for field in fields_to_merge:
            new_val = new_data.get(field)
            old_val = existing.get(field)
            
            # Fill if old is empty and new is not
            if new_val and (old_val is None or str(old_val).strip() == ''):
                merged_data[field] = new_val
                changes_made = True

        # Special case: Status
        # If current status is 'In Attesa' and new status is different and not 'In Attesa'
        new_status = new_data.get('status')
        if new_status and new_status != 'In Attesa' and existing.get('status') == 'In Attesa':
            merged_data['status'] = new_status
            changes_made = True

        # Special case: Quantity
        new_qty = new_data.get('quantity', 1)
        if new_qty > existing.get('quantity', 1):
            merged_data['quantity'] = new_qty
            changes_made = True

        # Special case: Notes (append if new notes added)
        new_notes = new_data.get('notes', '').strip()
        if new_notes and new_notes not in existing.get('notes', ''):
            if existing.get('notes'):
                merged_data['notes'] = existing['notes'] + "\n" + new_notes
            else:
                merged_data['notes'] = new_notes
            changes_made = True

        if changes_made:
            return update_order(order_id, merged_data)
        
        return True # No changes needed, but operation successful
        
    except Exception as e:
        logger.error(f"Error merging order {order_id}: {e}")
        return False


def delete_order(order_id: int) -> bool:
    """Delete an order and its attachments"""
    try:
        with db_cursor() as cursor:
            cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
            logger.info(f"Order deleted successfully: ID {order_id}")
            return True
        
    except Exception as e:
        logger.error(f"Error deleting order {order_id}: {e}")
        return False


def mark_as_delivered(order_id: int, delivered: bool = True) -> bool:
    """Mark an order as delivered or not delivered"""
    try:
        with db_cursor() as cursor:
            cursor.execute(
                'UPDATE orders SET is_delivered = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (delivered, order_id)
            )
            logger.info(f"Order {order_id} marked as {'delivered' if delivered else 'not delivered'}")
            return True
        
    except Exception as e:
        logger.error(f"Error marking order {order_id} as delivered: {e}")
        return False


# Category Management
def add_category(name: str, color: str = '') -> Optional[int]:
    """Add a new category"""
    try:
        with db_cursor() as cursor:
            cursor.execute('INSERT INTO categories (name, color) VALUES (?, ?)', (name, color))
            category_id = cursor.lastrowid
            logger.info(f"Category added: {name}")
            return category_id
        
    except sqlite3.IntegrityError:
        logger.warning(f"Category already exists: {name}")
        return None
    except Exception as e:
        logger.error(f"Error adding category: {e}")
        return None


def get_categories() -> List[Dict[str, Any]]:
    """Get all categories"""
    try:
        conn = get_db_connection()
        try:
            categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
            return [dict(cat) for cat in categories]
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return []


def delete_category(category_id: int) -> bool:
    """Delete a category"""
    try:
        with db_cursor() as cursor:
            cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
            logger.info(f"Category deleted: ID {category_id}")
            return True
    except Exception as e:
        logger.error(f"Error deleting category: {e}")
        return False


# Statistics
def get_platforms() -> List[str]:
    """Get list of unique platforms"""
    try:
        conn = get_db_connection()
        try:
            platforms = conn.execute('SELECT DISTINCT platform FROM orders ORDER BY platform').fetchall()
            return [p[0] for p in platforms if p[0]]
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Error getting platforms: {e}")
        return []


# Export/Import
def export_to_csv(filepath: str, orders: List[Dict[str, Any]]) -> bool:
    """Export orders to CSV file"""
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            if not orders:
                return True
            
            fieldnames = orders[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(orders)
        
        logger.info(f"Exported {len(orders)} orders to CSV: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        return False


def export_to_json(filepath: str, orders: List[Dict[str, Any]]) -> bool:
    """Export orders to JSON file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(orders, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(orders)} orders to JSON: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        return False


def import_from_json(filepath: str) -> Tuple[bool, int]:
    """Import orders from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as jsonfile:
            orders = json.load(jsonfile)
        
        count = 0
        for order in orders:
            # Remove id and timestamps to avoid conflicts
            order.pop('id', None)
            order.pop('created_at', None)
            order.pop('updated_at', None)
            
            if add_order(order):
                count += 1
        
        logger.info(f"Imported {count} orders from JSON: {filepath}")
        return True, count
        
    except Exception as e:
        logger.error(f"Error importing from JSON: {e}")
        return False, 0


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
