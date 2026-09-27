import sqlite3
from typing import List, Dict, Any, Optional

DB_FILE = "shop.db"

def get_connection(db_file: str = DB_FILE) -> sqlite3.Connection:
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_file: str = DB_FILE) -> None:
    """បង្កើតតារាងទាំងអស់ក្នុង Database ប្រសិនបើមិនទាន់មាន"""
    with get_connection(db_file) as conn:
        cursor = conn.cursor()
        
        # Categories Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        
        # Products Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image_url TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
            )
        """)
        
        # Cart Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (user_id, product_id),
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        """)
        
        # Orders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                customer_name TEXT,
                phone TEXT,
                address TEXT,
                payment_method TEXT,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'រង់ចាំពិនិត្យ (Pending)',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Order Items Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER,
                product_name TEXT NOT NULL,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
            )
        """)

        # Settings Table (for storing dynamic admin_id, config, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()



# ==========================
# Category Functions
# ==========================

def get_all_categories() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]

def add_category(name: str) -> Optional[int]:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (name.strip(),))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def delete_category(category_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        return cursor.rowcount > 0


# ==========================
# Product Functions
# ==========================

def get_products_by_category(category_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, category_id, name, description, price, image_url 
            FROM products 
            WHERE category_id = ? AND is_active = 1
            ORDER BY id ASC
        """, (category_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_product(product_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.category_id, c.name as category_name, p.name, p.description, p.price, p.image_url 
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = ? AND p.is_active = 1
        """, (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_products() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.category_id, c.name as category_name, p.name, p.description, p.price, p.image_url
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1
            ORDER BY p.id ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

def add_product(category_id: int, name: str, description: str, price: float, image_url: Optional[str] = None) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (category_id, name, description, price, image_url)
            VALUES (?, ?, ?, ?, ?)
        """, (category_id, name.strip(), description.strip(), price, image_url))
        conn.commit()
        return cursor.lastrowid

def delete_product(product_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
        conn.commit()
        return cursor.rowcount > 0


# ==========================
# Cart Functions
# ==========================

def get_cart(user_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.product_id, p.name, p.price, c.quantity, (p.price * c.quantity) as subtotal, p.image_url
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ? AND p.is_active = 1
            ORDER BY c.product_id ASC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

def add_to_cart(user_id: int, product_id: int, quantity: int = 1) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cart (user_id, product_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id) 
            DO UPDATE SET quantity = quantity + excluded.quantity
        """, (user_id, product_id, quantity))
        conn.commit()

def update_cart_quantity(user_id: int, product_id: int, delta: int) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        row = cursor.fetchone()
        if not row:
            if delta > 0:
                add_to_cart(user_id, product_id, delta)
                return delta
            return 0
        new_qty = row["quantity"] + delta
        if new_qty <= 0:
            cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
            conn.commit()
            return 0
        else:
            cursor.execute("UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?", (new_qty, user_id, product_id))
            conn.commit()
            return new_qty

def remove_from_cart(user_id: int, product_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
        conn.commit()

def clear_cart(user_id: int) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()

def get_cart_total(user_id: int) -> float:
    items = get_cart(user_id)
    return sum(item["subtotal"] for item in items)


# ==========================
# Order Functions
# ==========================

def create_order(user_id: int, customer_name: str, phone: str, address: str, payment_method: str, delivery_fee: float = 1.50, status: str = "រង់ចាំពិនិត្យ") -> Optional[Dict[str, Any]]:
    cart_items = get_cart(user_id)
    if not cart_items:
        return None
    
    items_total = sum(item["subtotal"] for item in cart_items)
    total_amount = items_total + delivery_fee
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (user_id, customer_name, phone, address, payment_method, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, customer_name, phone, address, payment_method, total_amount, status))
        order_id = cursor.lastrowid
        
        for item in cart_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, item["product_id"], item["name"], item["price"], item["quantity"]))
        
        # Clear user cart after ordering
        cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        conn.commit()
        
        return {
            "order_id": order_id,
            "user_id": user_id,
            "customer_name": customer_name,
            "phone": phone,
            "address": address,
            "payment_method": payment_method,
            "items_total": items_total,
            "delivery_fee": delivery_fee,
            "total_amount": total_amount,
            "status": status,
            "items": cart_items
        }


def get_user_orders(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, total_amount, payment_method, status, created_at
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]

def get_order_details(order_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        if not order:
            return None
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
        items = cursor.fetchall()
        order_dict = dict(order)
        order_dict["items"] = [dict(item) for item in items]
        return order_dict

def update_order_status(order_id: int, new_status: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        conn.commit()
        return cursor.rowcount > 0

def get_recent_orders(limit: int = 10) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, customer_name, phone, total_amount, status, created_at
            FROM orders
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


# ==========================
# Settings Functions
# ==========================

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else default

def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
        conn.commit()

