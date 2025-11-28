import sqlite3
from datetime import datetime

DB_NAME = "delivery_tracker.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
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
            alarm_enabled BOOLEAN DEFAULT 0,
            is_delivered BOOLEAN DEFAULT 0,
            position TEXT,
            notes TEXT
        )
    ''')
    # Add position column if it doesn't exist (for existing databases)
    cursor.execute("PRAGMA table_info(orders)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'position' not in columns:
        cursor.execute('ALTER TABLE orders ADD COLUMN position TEXT')
    conn.commit()
    conn.close()

def add_order(order_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (order_date, platform, seller, destination, description, link, quantity, estimated_delivery, alarm_enabled, is_delivered, position, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        order_data['order_date'],
        order_data['platform'],
        order_data.get('seller', ''),
        order_data.get('destination', ''),
        order_data['description'],
        order_data.get('link', ''),
        order_data.get('quantity', 1),
        order_data.get('estimated_delivery', ''),
        order_data.get('alarm_enabled', False),
        order_data.get('is_delivered', False),
        order_data.get('position', ''),
        order_data.get('notes', '')
    ))
    conn.commit()
    conn.close()

def get_orders():
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders ORDER BY estimated_delivery ASC').fetchall()
    conn.close()
    return [dict(order) for order in orders]

def update_order(order_id, order_data):
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
            notes = ?
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
        order_data.get('alarm_enabled', False),
        order_data.get('is_delivered', False),
        order_data.get('position', ''),
        order_data.get('notes', ''),
        order_id
    ))
    conn.commit()
    conn.close()

def delete_order(order_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
