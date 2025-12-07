"""
Enhanced database module for Delivery Tracker.
Includes optimizations, indices, categories, attachments, and export functionality.
"""
import sqlite3
import csv
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import utils

logger = utils.get_logger(__name__)

DB_NAME = "delivery_tracker.db"


def get_db_connection():
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


def init_db():
    """Initialize database with all tables and indices"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
            ('created_at', 'ALTER TABLE orders ADD COLUMN created_at TEXT DEFAULT CURRENT_TIMESTAMP'),
            ('updated_at', 'ALTER TABLE orders ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP'),
        ]
        
        for column_name, migration_sql in migrations:
            if column_name not in columns:
                cursor.execute(migration_sql)
                logger.info(f"Added column: {column_name}")
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()


def add_order(order_data: Dict[str, Any]) -> Optional[int]:
    """Add a new order to database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (
                order_date, platform, seller, destination, description, 
                link, quantity, estimated_delivery, alarm_enabled, 
                is_delivered, position, notes, category
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            order_data.get('category', '')
        ))
        
        order_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Order added successfully: ID {order_id}")
        return order_id
        
    except sqlite3.Error as e:
        logger.error(f"Error adding order: {e}")
        return None
    finally:
        conn.close()


def get_orders(include_delivered: bool = True, search: str = '', 
               platform_filter: str = '', category_filter: str = '') -> List[Dict[str, Any]]:
    """Get orders with optional filters"""
    try:
        conn = get_db_connection()
        
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
        
        query += ' ORDER BY estimated_delivery ASC, created_at DESC'
        
        orders = conn.execute(query, params).fetchall()
        return [dict(order) for order in orders]
        
    except sqlite3.Error as e:
        logger.error(f"Error getting orders: {e}")
        return []
    finally:
        conn.close()


def get_order_by_id(order_id: int) -> Optional[Dict[str, Any]]:
    """Get a single order by ID"""
    try:
        conn = get_db_connection()
        order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
        return dict(order) if order else None
    except sqlite3.Error as e:
        logger.error(f"Error getting order {order_id}: {e}")
        return None
    finally:
        conn.close()


def update_order(order_id: int, order_data: Dict[str, Any]) -> bool:
    """Update an existing order"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
            order_id
        ))
        
        conn.commit()
        logger.info(f"Order updated successfully: ID {order_id}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error updating order {order_id}: {e}")
        return False
    finally:
        conn.close()


def delete_order(order_id: int) -> bool:
    """Delete an order and its attachments"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM orders WHERE id = ?', (order_id,))
        conn.commit()
        logger.info(f"Order deleted successfully: ID {order_id}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error deleting order {order_id}: {e}")
        return False
    finally:
        conn.close()


def mark_as_delivered(order_id: int, delivered: bool = True) -> bool:
    """Mark an order as delivered or not delivered"""
    try:
        conn = get_db_connection()
        conn.execute(
            'UPDATE orders SET is_delivered = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (delivered, order_id)
        )
        conn.commit()
        logger.info(f"Order {order_id} marked as {'delivered' if delivered else 'not delivered'}")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error marking order {order_id} as delivered: {e}")
        return False
    finally:
        conn.close()


# Category Management
def add_category(name: str, color: str = '') -> Optional[int]:
    """Add a new category"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO categories (name, color) VALUES (?, ?)', (name, color))
        category_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Category added: {name}")
        return category_id
        
    except sqlite3.IntegrityError:
        logger.warning(f"Category already exists: {name}")
        return None
    except sqlite3.Error as e:
        logger.error(f"Error adding category: {e}")
        return None
    finally:
        conn.close()


def get_categories() -> List[Dict[str, Any]]:
    """Get all categories"""
    try:
        conn = get_db_connection()
        categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
        return [dict(cat) for cat in categories]
    except sqlite3.Error as e:
        logger.error(f"Error getting categories: {e}")
        return []
    finally:
        conn.close()


def delete_category(category_id: int) -> bool:
    """Delete a category"""
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        logger.info(f"Category deleted: ID {category_id}")
        return True
    except sqlite3.Error as e:
        logger.error(f"Error deleting category: {e}")
        return False
    finally:
        conn.close()


# Statistics
def get_platforms() -> List[str]:
    """Get list of unique platforms"""
    try:
        conn = get_db_connection()
        platforms = conn.execute('SELECT DISTINCT platform FROM orders ORDER BY platform').fetchall()
        return [p[0] for p in platforms if p[0]]
    except sqlite3.Error as e:
        logger.error(f"Error getting platforms: {e}")
        return []
    finally:
        conn.close()


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
