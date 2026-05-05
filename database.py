import sqlite3
import shutil
from pathlib import Path

import bcrypt

from utils import get_now_text, get_today_text


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "evoucher.db"


def hash_password(password):
    """
    Membuat password hash menggunakan bcrypt.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def get_connection():
    """
    Membuat koneksi SQLite.
    """
    DATA_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    return conn


def init_db():
    """
    Membuat semua tabel final jika belum ada.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS divisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            division_name TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            division_id INTEGER,
            phone TEXT,
            email TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (division_id) REFERENCES divisions(id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'kasir', 'pegawai')),
            employee_id INTEGER,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            last_login_at TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS merchants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_name TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS food_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS food_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (category_id) REFERENCES food_categories(id),
            UNIQUE(category_id, item_name)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            period_month TEXT NOT NULL,
            amount_allocated INTEGER NOT NULL,
            generated_by INTEGER,
            generated_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (generated_by) REFERENCES users(id),
            UNIQUE(employee_id, period_month)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS voucher_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            merchant_id INTEGER NOT NULL,
            period_month TEXT NOT NULL,
            transaction_date TEXT NOT NULL,
            total_amount INTEGER NOT NULL,
            voucher_amount INTEGER NOT NULL,
            cash_amount INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            voided_at TEXT,
            voided_by INTEGER,
            void_reason TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (merchant_id) REFERENCES merchants(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (voided_by) REFERENCES users(id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS voucher_transaction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            food_item_id INTEGER,
            item_name_snapshot TEXT NOT NULL,
            price_snapshot INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            subtotal INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES voucher_transactions(id),
            FOREIGN KEY (food_item_id) REFERENCES food_items(id)
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            table_name TEXT,
            record_id INTEGER,
            description TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )

    conn.commit()
    conn.close()


def insert_audit_log(user_id, action, table_name=None, record_id=None, description=None):
    """
    Mencatat aktivitas penting.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO audit_logs
        (user_id, action, table_name, record_id, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, action, table_name, record_id, description, get_now_text())
    )

    conn.commit()
    conn.close()


def seed_settings():
    conn = get_connection()
    cursor = conn.cursor()

    settings = [
        ("company_name", "Kantor Demo"),
        ("monthly_voucher_amount", "75000"),
        ("allow_free_amount", "true"),
        ("allow_split_payment", "false"),
        ("default_merchant_name", "Kantin Kantor"),
    ]

    for key, value in settings:
        cursor.execute(
            """
            INSERT OR IGNORE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            """,
            (key, value, get_now_text())
        )

    conn.commit()
    conn.close()


def seed_divisions():
    conn = get_connection()
    cursor = conn.cursor()

    divisions = [
        "Keuangan",
        "SDM",
        "IT",
        "Umum",
        "Operasional",
    ]

    for division_name in divisions:
        cursor.execute(
            """
            INSERT OR IGNORE INTO divisions
            (division_name, is_active, created_at)
            VALUES (?, ?, ?)
            """,
            (division_name, 1, get_now_text())
        )

    conn.commit()
    conn.close()


def get_division_id_by_name(division_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM divisions
        WHERE division_name = ?
        """,
        (division_name,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return row["id"]


def seed_employees():
    conn = get_connection()
    cursor = conn.cursor()

    sample_employees = [
        ("EMP001", "Budi Santoso", "IT", "081111111001", "budi@example.com", 1),
        ("EMP002", "Siti Aminah", "SDM", "081111111002", "siti@example.com", 1),
        ("EMP003", "Andi Wijaya", "Keuangan", "081111111003", "andi@example.com", 1),
        ("EMP004", "Rina Kurnia", "Umum", "081111111004", "rina@example.com", 1),
        ("EMP005", "Dewi Lestari", "Operasional", "081111111005", "dewi@example.com", 1),
        ("EMP006", "Joko Permana", "Umum", "081111111006", "joko@example.com", 0),
    ]

    for employee_code, full_name, division_name, phone, email, is_active in sample_employees:
        division_id = get_division_id_by_name(division_name)

        cursor.execute(
            """
            INSERT OR IGNORE INTO employees
            (employee_code, full_name, division_id, phone, email, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_code,
                full_name,
                division_id,
                phone,
                email,
                is_active,
                get_now_text(),
            )
        )

    conn.commit()
    conn.close()


def get_employee_id_by_code(employee_code):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM employees
        WHERE employee_code = ?
        """,
        (employee_code,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return row["id"]


def seed_merchants():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO merchants
        (merchant_name, is_active, created_at)
        VALUES (?, ?, ?)
        """,
        ("Kantin Kantor", 1, get_now_text())
    )

    conn.commit()
    conn.close()


def seed_food_categories():
    conn = get_connection()
    cursor = conn.cursor()

    categories = [
        "Makanan Berat",
        "Minuman",
        "Snack",
        "Lauk Tambahan",
        "Lain-lain",
    ]

    for category_name in categories:
        cursor.execute(
            """
            INSERT OR IGNORE INTO food_categories
            (category_name, is_active, created_at)
            VALUES (?, ?, ?)
            """,
            (category_name, 1, get_now_text())
        )

    conn.commit()
    conn.close()


def get_food_category_id_by_name(category_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM food_categories
        WHERE category_name = ?
        """,
        (category_name,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return row["id"]


def seed_food_items():
    conn = get_connection()
    cursor = conn.cursor()

    sample_items = [
        ("Makanan Berat", "Nasi Ayam", 15000),
        ("Makanan Berat", "Nasi Ikan", 18000),
        ("Makanan Berat", "Nasi Telur", 12000),
        ("Minuman", "Es Teh", 5000),
        ("Minuman", "Kopi", 6000),
        ("Snack", "Gorengan", 3000),
        ("Snack", "Roti", 7000),
        ("Lauk Tambahan", "Tambahan Ayam", 10000),
        ("Lain-lain", "Item Manual", 0),
    ]

    for category_name, item_name, price in sample_items:
        category_id = get_food_category_id_by_name(category_name)

        if category_id is None:
            continue

        cursor.execute(
            """
            INSERT OR IGNORE INTO food_items
            (category_id, item_name, price, is_active, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (category_id, item_name, price, 1, get_now_text())
        )

    conn.commit()
    conn.close()


def seed_users():
    conn = get_connection()
    cursor = conn.cursor()

    emp001_id = get_employee_id_by_code("EMP001")
    emp002_id = get_employee_id_by_code("EMP002")

    users = [
        ("admin", "admin123", "admin", None),
        ("kasir", "kasir123", "kasir", None),
        ("emp001", "emp001123", "pegawai", emp001_id),
        ("emp002", "emp002123", "pegawai", emp002_id),
    ]

    for username, plain_password, role, employee_id in users:
        # Jika role pegawai tetapi employee_id tidak ditemukan,
        # user tetap dibuat tanpa relasi pegawai agar tidak gagal di cloud.
        if role == "pegawai" and employee_id is None:
            employee_id = None

        cursor.execute(
            """
            INSERT OR IGNORE INTO users
            (username, password_hash, role, employee_id, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                hash_password(plain_password),
                role,
                employee_id,
                1,
                get_now_text(),
            )
        )

    conn.commit()
    conn.close()


def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            username,
            password_hash,
            role,
            employee_id,
            is_active,
            created_at,
            updated_at,
            last_login_at
        FROM users
        WHERE username = ?
        """,
        (username,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            username,
            role,
            employee_id,
            is_active,
            created_at,
            updated_at,
            last_login_at
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def update_last_login(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET last_login_at = ?
        WHERE id = ?
        """,
        (get_now_text(), user_id)
    )

    conn.commit()
    conn.close()


def get_database_summary():
    conn = get_connection()
    cursor = conn.cursor()

    tables = [
        "users",
        "divisions",
        "employees",
        "merchants",
        "food_categories",
        "food_items",
        "monthly_allocations",
        "voucher_transactions",
        "voucher_transaction_items",
        "settings",
        "audit_logs",
    ]

    summary = []

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) AS total FROM {table}")
        total = cursor.fetchone()["total"]

        summary.append(
            {
                "table_name": table,
                "total_rows": total,
            }
        )

    conn.close()
    return summary


def setup_database():
    """
    Fungsi utama yang dipanggil saat aplikasi berjalan.
    """
    init_db()
    seed_settings()
    seed_divisions()
    seed_employees()
    seed_merchants()
    seed_food_categories()
    seed_food_items()
    seed_users()

# =========================================================
# ADMIN DASHBOARD HELPERS
# =========================================================

def get_admin_dashboard_summary():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total FROM divisions WHERE is_active = 1")
    active_divisions = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM employees WHERE is_active = 1")
    active_employees = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM employees WHERE is_active = 0")
    inactive_employees = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM food_categories WHERE is_active = 1")
    active_categories = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM food_items WHERE is_active = 1")
    active_food_items = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM users WHERE is_active = 1")
    active_users = cursor.fetchone()["total"]

    conn.close()

    return {
        "active_divisions": active_divisions,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "active_categories": active_categories,
        "active_food_items": active_food_items,
        "active_users": active_users,
    }


# =========================================================
# DIVISIONS CRUD
# =========================================================

def get_divisions(include_inactive=True):
    conn = get_connection()
    cursor = conn.cursor()

    if include_inactive:
        cursor.execute(
            """
            SELECT id, division_name, is_active, created_at, updated_at
            FROM divisions
            ORDER BY division_name ASC
            """
        )
    else:
        cursor.execute(
            """
            SELECT id, division_name, is_active, created_at, updated_at
            FROM divisions
            WHERE is_active = 1
            ORDER BY division_name ASC
            """
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def division_name_exists(division_name, exclude_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if exclude_id is None:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM divisions
            WHERE LOWER(division_name) = LOWER(?)
            """,
            (division_name,)
        )
    else:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM divisions
            WHERE LOWER(division_name) = LOWER(?)
            AND id != ?
            """,
            (division_name, exclude_id)
        )

    total = cursor.fetchone()["total"]
    conn.close()

    return total > 0


def add_division(division_name, created_by=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO divisions
        (division_name, is_active, created_at)
        VALUES (?, ?, ?)
        """,
        (division_name, 1, get_now_text())
    )

    division_id = cursor.lastrowid
    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=created_by,
        action="ADD_DIVISION",
        table_name="divisions",
        record_id=division_id,
        description=f"Menambahkan divisi {division_name}"
    )

    return division_id


def update_division(division_id, division_name, is_active, updated_by=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE divisions
        SET division_name = ?, is_active = ?, updated_at = ?
        WHERE id = ?
        """,
        (division_name, is_active, get_now_text(), division_id)
    )

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=updated_by,
        action="UPDATE_DIVISION",
        table_name="divisions",
        record_id=division_id,
        description=f"Mengubah divisi menjadi {division_name}"
    )


# =========================================================
# EMPLOYEES CRUD
# =========================================================

def get_employees_with_division(include_inactive=True):
    conn = get_connection()
    cursor = conn.cursor()

    if include_inactive:
        cursor.execute(
            """
            SELECT
                e.id,
                e.employee_code,
                e.full_name,
                e.division_id,
                d.division_name,
                e.phone,
                e.email,
                e.is_active,
                e.created_at,
                e.updated_at
            FROM employees e
            LEFT JOIN divisions d ON d.id = e.division_id
            ORDER BY e.employee_code ASC
            """
        )
    else:
        cursor.execute(
            """
            SELECT
                e.id,
                e.employee_code,
                e.full_name,
                e.division_id,
                d.division_name,
                e.phone,
                e.email,
                e.is_active,
                e.created_at,
                e.updated_at
            FROM employees e
            LEFT JOIN divisions d ON d.id = e.division_id
            WHERE e.is_active = 1
            ORDER BY e.employee_code ASC
            """
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def employee_code_exists_final(employee_code, exclude_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if exclude_id is None:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM employees
            WHERE LOWER(employee_code) = LOWER(?)
            """,
            (employee_code,)
        )
    else:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM employees
            WHERE LOWER(employee_code) = LOWER(?)
            AND id != ?
            """,
            (employee_code, exclude_id)
        )

    total = cursor.fetchone()["total"]
    conn.close()

    return total > 0


def add_employee_final(employee_code, full_name, division_id, phone, email, is_active, created_by=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO employees
        (employee_code, full_name, division_id, phone, email, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            employee_code,
            full_name,
            division_id,
            phone,
            email,
            is_active,
            get_now_text(),
        )
    )

    employee_id = cursor.lastrowid
    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=created_by,
        action="ADD_EMPLOYEE",
        table_name="employees",
        record_id=employee_id,
        description=f"Menambahkan pegawai {employee_code} - {full_name}"
    )

    return employee_id


def update_employee_final(employee_id, employee_code, full_name, division_id, phone, email, is_active, updated_by=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE employees
        SET
            employee_code = ?,
            full_name = ?,
            division_id = ?,
            phone = ?,
            email = ?,
            is_active = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            employee_code,
            full_name,
            division_id,
            phone,
            email,
            is_active,
            get_now_text(),
            employee_id,
        )
    )

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=updated_by,
        action="UPDATE_EMPLOYEE",
        table_name="employees",
        record_id=employee_id,
        description=f"Mengubah pegawai {employee_code} - {full_name}"
    )


# =========================================================
# FOOD CATEGORIES CRUD
# =========================================================

def get_food_categories(include_inactive=True):
    conn = get_connection()
    cursor = conn.cursor()

    if include_inactive:
        cursor.execute(
            """
            SELECT id, category_name, is_active, created_at, updated_at
            FROM food_categories
            ORDER BY category_name ASC
            """
        )
    else:
        cursor.execute(
            """
            SELECT id, category_name, is_active, created_at, updated_at
            FROM food_categories
            WHERE is_active = 1
            ORDER BY category_name ASC
            """
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def food_category_name_exists(category_name, exclude_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if exclude_id is None:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM food_categories
            WHERE LOWER(category_name) = LOWER(?)
            """,
            (category_name,)
        )
    else:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM food_categories
            WHERE LOWER(category_name) = LOWER(?)
            AND id != ?
            """,
            (category_name, exclude_id)
        )

    total = cursor.fetchone()["total"]
    conn.close()

    return total > 0


def add_food_category(category_name, created_by=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO food_categories
        (category_name, is_active, created_at)
        VALUES (?, ?, ?)
        """,
        (category_name, 1, get_now_text())
    )

    category_id = cursor.lastrowid
    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=created_by,
        action="ADD_FOOD_CATEGORY",
        table_name="food_categories",
        record_id=category_id,
        description=f"Menambahkan kategori menu {category_name}"
    )

    return category_id


def update_food_category(category_id, category_name, is_active, updated_by=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE food_categories
        SET category_name = ?, is_active = ?, updated_at = ?
        WHERE id = ?
        """,
        (category_name, is_active, get_now_text(), category_id)
    )

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=updated_by,
        action="UPDATE_FOOD_CATEGORY",
        table_name="food_categories",
        record_id=category_id,
        description=f"Mengubah kategori menu menjadi {category_name}"
    )


# =========================================================
# FOOD ITEMS CRUD
# =========================================================

def get_food_items_with_category(include_inactive=True):
    conn = get_connection()
    cursor = conn.cursor()

    if include_inactive:
        cursor.execute(
            """
            SELECT
                fi.id,
                fi.category_id,
                fc.category_name,
                fi.item_name,
                fi.price,
                fi.is_active,
                fi.created_at,
                fi.updated_at
            FROM food_items fi
            JOIN food_categories fc ON fc.id = fi.category_id
            ORDER BY fc.category_name ASC, fi.item_name ASC
            """
        )
    else:
        cursor.execute(
            """
            SELECT
                fi.id,
                fi.category_id,
                fc.category_name,
                fi.item_name,
                fi.price,
                fi.is_active,
                fi.created_at,
                fi.updated_at
            FROM food_items fi
            JOIN food_categories fc ON fc.id = fi.category_id
            WHERE fi.is_active = 1
            ORDER BY fc.category_name ASC, fi.item_name ASC
            """
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def food_item_exists(category_id, item_name, exclude_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if exclude_id is None:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM food_items
            WHERE category_id = ?
            AND LOWER(item_name) = LOWER(?)
            """,
            (category_id, item_name)
        )
    else:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM food_items
            WHERE category_id = ?
            AND LOWER(item_name) = LOWER(?)
            AND id != ?
            """,
            (category_id, item_name, exclude_id)
        )

    total = cursor.fetchone()["total"]
    conn.close()

    return total > 0


def add_food_item(category_id, item_name, price, is_active, created_by=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO food_items
        (category_id, item_name, price, is_active, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (category_id, item_name, price, is_active, get_now_text())
    )

    item_id = cursor.lastrowid
    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=created_by,
        action="ADD_FOOD_ITEM",
        table_name="food_items",
        record_id=item_id,
        description=f"Menambahkan menu {item_name}"
    )

    return item_id


def update_food_item(item_id, category_id, item_name, price, is_active, updated_by=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE food_items
        SET
            category_id = ?,
            item_name = ?,
            price = ?,
            is_active = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            category_id,
            item_name,
            price,
            is_active,
            get_now_text(),
            item_id,
        )
    )

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=updated_by,
        action="UPDATE_FOOD_ITEM",
        table_name="food_items",
        record_id=item_id,
        description=f"Mengubah menu {item_name}"
    )

# =========================================================
# POS / KASIR HELPERS
# =========================================================

def get_setting_value(key, default_value=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT value
        FROM settings
        WHERE key = ?
        """,
        (key,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return default_value

    return row["value"]


def get_monthly_voucher_amount():
    value = get_setting_value("monthly_voucher_amount", "75000")
    return int(value)


def get_active_merchant():
    """
    Untuk tahap awal hanya memakai 1 merchant aktif.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, merchant_name
        FROM merchants
        WHERE is_active = 1
        ORDER BY id ASC
        LIMIT 1
        """
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def get_pos_active_employees():
    """
    Mengambil pegawai aktif untuk dropdown kasir.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            e.id,
            e.employee_code,
            e.full_name,
            e.division_id,
            d.division_name,
            e.is_active
        FROM employees e
        LEFT JOIN divisions d ON d.id = e.division_id
        WHERE e.is_active = 1
        ORDER BY e.employee_code ASC
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_pos_food_categories():
    """
    Mengambil kategori menu aktif.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, category_name
        FROM food_categories
        WHERE is_active = 1
        ORDER BY category_name ASC
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_pos_food_items(category_id=None):
    """
    Mengambil item menu aktif untuk POS.
    Jika category_id diisi, hanya menampilkan menu kategori tersebut.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if category_id:
        cursor.execute(
            """
            SELECT
                fi.id,
                fi.category_id,
                fc.category_name,
                fi.item_name,
                fi.price
            FROM food_items fi
            JOIN food_categories fc ON fc.id = fi.category_id
            WHERE fi.is_active = 1
            AND fc.is_active = 1
            AND fi.category_id = ?
            ORDER BY fi.item_name ASC
            """,
            (category_id,)
        )
    else:
        cursor.execute(
            """
            SELECT
                fi.id,
                fi.category_id,
                fc.category_name,
                fi.item_name,
                fi.price
            FROM food_items fi
            JOIN food_categories fc ON fc.id = fi.category_id
            WHERE fi.is_active = 1
            AND fc.is_active = 1
            ORDER BY fc.category_name ASC, fi.item_name ASC
            """
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_employee_voucher_balance(employee_id, period_month):
    """
    Saldo = alokasi aktif - total voucher_amount transaksi valid.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount_allocated), 0) AS total_allocation
        FROM monthly_allocations
        WHERE employee_id = ?
        AND period_month = ?
        AND status = 'active'
        """,
        (employee_id, period_month)
    )
    total_allocation = cursor.fetchone()["total_allocation"]

    cursor.execute(
        """
        SELECT COALESCE(SUM(voucher_amount), 0) AS total_used
        FROM voucher_transactions
        WHERE employee_id = ?
        AND period_month = ?
        AND voided_at IS NULL
        """,
        (employee_id, period_month)
    )
    total_used = cursor.fetchone()["total_used"]

    conn.close()

    balance = total_allocation - total_used

    return {
        "allocation": total_allocation,
        "used": total_used,
        "balance": balance,
        "has_allocation": total_allocation > 0,
    }


def generate_monthly_allocations_for_active_employees(period_month, generated_by=None):
    """
    Generate voucher bulanan untuk semua pegawai aktif.
    Fungsi ini disediakan agar POS bisa dites meskipun halaman generate voucher belum dibuat.
    Nanti fungsi ini tetap dipakai di halaman Generate Voucher.
    """
    amount = get_monthly_voucher_amount()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM employees
        WHERE is_active = 1
        ORDER BY employee_code ASC
        """
    )
    employees = cursor.fetchall()

    created = 0
    skipped = 0

    for employee in employees:
        employee_id = employee["id"]

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM monthly_allocations
            WHERE employee_id = ?
            AND period_month = ?
            """,
            (employee_id, period_month)
        )

        exists = cursor.fetchone()["total"] > 0

        if exists:
            skipped += 1
            continue

        cursor.execute(
            """
            INSERT INTO monthly_allocations
            (employee_id, period_month, amount_allocated, generated_by, generated_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                employee_id,
                period_month,
                amount,
                generated_by,
                get_now_text(),
                "active",
            )
        )

        created += 1

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=generated_by,
        action="GENERATE_MONTHLY_ALLOCATIONS",
        table_name="monthly_allocations",
        record_id=None,
        description=f"Generate voucher periode {period_month}. Created={created}, skipped={skipped}"
    )

    return {
        "created": created,
        "skipped": skipped,
        "amount": amount,
        "active_employees": len(employees),
    }

def get_employee_by_id(employee_id):
    """
    Mengambil satu data pegawai berdasarkan ID.
    Dipakai untuk validasi transaksi POS dan halaman lain.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            employee_code,
            full_name,
            division_id,
            phone,
            email,
            is_active,
            created_at,
            updated_at
        FROM employees
        WHERE id = ?
        """,
        (employee_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def create_pos_voucher_transaction(
    employee_id,
    merchant_id,
    period_month,
    cart_items,
    notes="",
    created_by=None,
):
    """
    Menyimpan transaksi POS:
    - Header masuk ke voucher_transactions
    - Detail item masuk ke voucher_transaction_items

    Mendukung split payment jika setting allow_split_payment = true.

    Jika split payment OFF:
        total_amount harus <= saldo voucher

    Jika split payment ON:
        voucher_amount = min(total_amount, saldo)
        cash_amount = total_amount - voucher_amount
    """
    if not cart_items:
        return {
            "success": False,
            "message": "Keranjang masih kosong."
        }

    employee = get_employee_by_id(employee_id)

    if employee is None:
        return {
            "success": False,
            "message": "Pegawai tidak ditemukan."
        }

    if employee["is_active"] != 1:
        return {
            "success": False,
            "message": "Pegawai nonaktif tidak dapat menggunakan voucher."
        }

    total_amount = 0

    for item in cart_items:
        quantity = int(item["quantity"])
        price = int(item["price"])
        subtotal = int(item["subtotal"])

        if quantity <= 0:
            return {
                "success": False,
                "message": "Quantity item harus lebih dari 0."
            }

        if price < 0:
            return {
                "success": False,
                "message": "Harga item tidak boleh negatif."
            }

        if subtotal != price * quantity:
            return {
                "success": False,
                "message": "Subtotal item tidak valid."
            }

        total_amount += subtotal

    if total_amount <= 0:
        return {
            "success": False,
            "message": "Total transaksi harus lebih dari 0."
        }

    balance_info = get_employee_voucher_balance(employee_id, period_month)

    if not balance_info["has_allocation"]:
        return {
            "success": False,
            "message": "Pegawai belum memiliki alokasi voucher untuk periode ini."
        }

    current_balance = int(balance_info["balance"])
    allow_split_payment = get_setting_bool("allow_split_payment", False)

    if current_balance <= 0:
        return {
            "success": False,
            "message": "Saldo voucher pegawai sudah habis."
        }

    if allow_split_payment:
        voucher_amount = min(total_amount, current_balance)
        cash_amount = total_amount - voucher_amount
    else:
        if total_amount > current_balance:
            return {
                "success": False,
                "message": "Saldo voucher tidak cukup untuk transaksi ini."
            }

        voucher_amount = total_amount
        cash_amount = 0

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN")

        cursor.execute(
            """
            INSERT INTO voucher_transactions
            (
                employee_id,
                merchant_id,
                period_month,
                transaction_date,
                total_amount,
                voucher_amount,
                cash_amount,
                notes,
                created_by,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_id,
                merchant_id,
                period_month,
                get_today_text(),
                total_amount,
                voucher_amount,
                cash_amount,
                notes,
                created_by,
                get_now_text(),
            )
        )

        transaction_id = cursor.lastrowid

        for item in cart_items:
            cursor.execute(
                """
                INSERT INTO voucher_transaction_items
                (
                    transaction_id,
                    food_item_id,
                    item_name_snapshot,
                    price_snapshot,
                    quantity,
                    subtotal,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_id,
                    item.get("food_item_id"),
                    item["item_name"],
                    int(item["price"]),
                    int(item["quantity"]),
                    int(item["subtotal"]),
                    get_now_text(),
                )
            )

        conn.commit()

    except Exception as error:
        conn.rollback()
        conn.close()

        return {
            "success": False,
            "message": f"Gagal menyimpan transaksi: {error}"
        }

    conn.close()

    insert_audit_log(
        user_id=created_by,
        action="CREATE_POS_TRANSACTION",
        table_name="voucher_transactions",
        record_id=transaction_id,
        description=(
            f"Transaksi POS periode {period_month}, "
            f"total={total_amount}, voucher={voucher_amount}, tunai={cash_amount}"
        )
    )

    if cash_amount > 0:
        message = (
            "Transaksi POS berhasil disimpan dengan split payment. "
            f"Voucher: {voucher_amount}, Tunai: {cash_amount}."
        )
    else:
        message = "Transaksi POS berhasil disimpan."

    return {
        "success": True,
        "message": message,
        "transaction_id": transaction_id,
        "total_amount": total_amount,
        "voucher_amount": voucher_amount,
        "cash_amount": cash_amount,
    }


def get_today_pos_transactions(created_by=None):
    """
    Mengambil transaksi hari ini.
    Jika created_by diisi, hanya transaksi yang dibuat user tersebut.
    """
    conn = get_connection()
    cursor = conn.cursor()

    today = get_today_text()

    if created_by is None:
        cursor.execute(
            """
            SELECT
                vt.id,
                vt.transaction_date,
                vt.period_month,
                e.employee_code,
                e.full_name,
                m.merchant_name,
                vt.total_amount,
                vt.voucher_amount,
                vt.cash_amount,
                vt.notes,
                vt.created_at,
                vt.voided_at
            FROM voucher_transactions vt
            JOIN employees e ON e.id = vt.employee_id
            JOIN merchants m ON m.id = vt.merchant_id
            WHERE vt.transaction_date = ?
            ORDER BY vt.created_at DESC
            """,
            (today,)
        )
    else:
        cursor.execute(
            """
            SELECT
                vt.id,
                vt.transaction_date,
                vt.period_month,
                e.employee_code,
                e.full_name,
                m.merchant_name,
                vt.total_amount,
                vt.voucher_amount,
                vt.cash_amount,
                vt.notes,
                vt.created_at,
                vt.voided_at
            FROM voucher_transactions vt
            JOIN employees e ON e.id = vt.employee_id
            JOIN merchants m ON m.id = vt.merchant_id
            WHERE vt.transaction_date = ?
            AND vt.created_by = ?
            ORDER BY vt.created_at DESC
            """,
            (today, created_by)
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

# =========================================================
# SALDO, RIWAYAT, DASHBOARD, LAPORAN
# =========================================================

def get_employee_detail_with_division(employee_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            e.id,
            e.employee_code,
            e.full_name,
            e.division_id,
            d.division_name,
            e.phone,
            e.email,
            e.is_active,
            e.created_at,
            e.updated_at
        FROM employees e
        LEFT JOIN divisions d ON d.id = e.division_id
        WHERE e.id = ?
        """,
        (employee_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def get_employee_transaction_history(employee_id, period_month=None):
    """
    Riwayat transaksi satu pegawai.
    Jika period_month diisi, hanya periode tersebut.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if period_month:
        cursor.execute(
            """
            SELECT
                vt.id,
                vt.period_month,
                vt.transaction_date,
                vt.total_amount,
                vt.voucher_amount,
                vt.cash_amount,
                vt.notes,
                vt.created_at,
                vt.voided_at,
                vt.void_reason,
                m.merchant_name
            FROM voucher_transactions vt
            JOIN merchants m ON m.id = vt.merchant_id
            WHERE vt.employee_id = ?
            AND vt.period_month = ?
            ORDER BY vt.created_at DESC
            """,
            (employee_id, period_month)
        )
    else:
        cursor.execute(
            """
            SELECT
                vt.id,
                vt.period_month,
                vt.transaction_date,
                vt.total_amount,
                vt.voucher_amount,
                vt.cash_amount,
                vt.notes,
                vt.created_at,
                vt.voided_at,
                vt.void_reason,
                m.merchant_name
            FROM voucher_transactions vt
            JOIN merchants m ON m.id = vt.merchant_id
            WHERE vt.employee_id = ?
            ORDER BY vt.created_at DESC
            """,
            (employee_id,)
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_transaction_items(transaction_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            transaction_id,
            food_item_id,
            item_name_snapshot,
            price_snapshot,
            quantity,
            subtotal,
            created_at
        FROM voucher_transaction_items
        WHERE transaction_id = ?
        ORDER BY id ASC
        """,
        (transaction_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_employee_voucher_summary_final(employee_id, period_month):
    """
    Ringkasan saldo pegawai pada satu periode.
    """
    employee = get_employee_detail_with_division(employee_id)
    balance = get_employee_voucher_balance(employee_id, period_month)
    transactions = get_employee_transaction_history(employee_id, period_month)

    valid_count = 0
    void_count = 0

    for trx in transactions:
        if trx["voided_at"] is None:
            valid_count += 1
        else:
            void_count += 1

    return {
        "employee": employee,
        "period_month": period_month,
        "allocation": balance["allocation"],
        "used": balance["used"],
        "balance": balance["balance"],
        "has_allocation": balance["has_allocation"],
        "valid_transaction_count": valid_count,
        "void_transaction_count": void_count,
    }


def get_period_transaction_dashboard(period_month):
    """
    Dashboard transaksi untuk periode tertentu.
    Hanya transaksi valid yang dihitung untuk nilai utama.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS total_transactions
        FROM voucher_transactions
        WHERE period_month = ?
        AND voided_at IS NULL
        """,
        (period_month,)
    )
    total_transactions = cursor.fetchone()["total_transactions"]

    cursor.execute(
        """
        SELECT COALESCE(SUM(total_amount), 0) AS total_sales
        FROM voucher_transactions
        WHERE period_month = ?
        AND voided_at IS NULL
        """,
        (period_month,)
    )
    total_sales = cursor.fetchone()["total_sales"]

    cursor.execute(
        """
        SELECT COALESCE(SUM(voucher_amount), 0) AS total_voucher
        FROM voucher_transactions
        WHERE period_month = ?
        AND voided_at IS NULL
        """,
        (period_month,)
    )
    total_voucher = cursor.fetchone()["total_voucher"]

    cursor.execute(
        """
        SELECT COALESCE(SUM(cash_amount), 0) AS total_cash
        FROM voucher_transactions
        WHERE period_month = ?
        AND voided_at IS NULL
        """,
        (period_month,)
    )
    total_cash = cursor.fetchone()["total_cash"]

    cursor.execute(
        """
        SELECT COUNT(DISTINCT employee_id) AS employees_used
        FROM voucher_transactions
        WHERE period_month = ?
        AND voided_at IS NULL
        """,
        (period_month,)
    )
    employees_used = cursor.fetchone()["employees_used"]

    cursor.execute(
        """
        SELECT COUNT(*) AS void_transactions
        FROM voucher_transactions
        WHERE period_month = ?
        AND voided_at IS NOT NULL
        """,
        (period_month,)
    )
    void_transactions = cursor.fetchone()["void_transactions"]

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount_allocated), 0) AS total_allocation
        FROM monthly_allocations
        WHERE period_month = ?
        AND status = 'active'
        """,
        (period_month,)
    )
    total_allocation = cursor.fetchone()["total_allocation"]

    conn.close()

    remaining_total = total_allocation - total_voucher

    return {
        "total_transactions": total_transactions,
        "total_sales": total_sales,
        "total_voucher": total_voucher,
        "total_cash": total_cash,
        "employees_used": employees_used,
        "void_transactions": void_transactions,
        "total_allocation": total_allocation,
        "remaining_total": remaining_total,
    }


def get_transactions_by_period(period_month):
    """
    Semua transaksi pada periode tertentu, termasuk void.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            vt.id,
            vt.period_month,
            vt.transaction_date,
            e.employee_code,
            e.full_name,
            d.division_name,
            m.merchant_name,
            vt.total_amount,
            vt.voucher_amount,
            vt.cash_amount,
            vt.notes,
            vt.created_at,
            vt.voided_at,
            vt.void_reason,
            u.username AS created_by_username
        FROM voucher_transactions vt
        JOIN employees e ON e.id = vt.employee_id
        LEFT JOIN divisions d ON d.id = e.division_id
        JOIN merchants m ON m.id = vt.merchant_id
        LEFT JOIN users u ON u.id = vt.created_by
        WHERE vt.period_month = ?
        ORDER BY vt.created_at DESC
        """,
        (period_month,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_daily_usage_report(period_month):
    """
    Rekap penggunaan voucher per hari.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            transaction_date,
            COUNT(*) AS total_transactions,
            COUNT(DISTINCT employee_id) AS total_employees,
            COALESCE(SUM(voucher_amount), 0) AS total_voucher
        FROM voucher_transactions
        WHERE period_month = ?
        AND voided_at IS NULL
        GROUP BY transaction_date
        ORDER BY transaction_date ASC
        """,
        (period_month,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_division_usage_report(period_month):
    """
    Rekap penggunaan voucher per divisi.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            COALESCE(d.division_name, '-') AS division_name,
            COUNT(*) AS total_transactions,
            COUNT(DISTINCT vt.employee_id) AS total_employees,
            COALESCE(SUM(vt.voucher_amount), 0) AS total_voucher
        FROM voucher_transactions vt
        JOIN employees e ON e.id = vt.employee_id
        LEFT JOIN divisions d ON d.id = e.division_id
        WHERE vt.period_month = ?
        AND vt.voided_at IS NULL
        GROUP BY d.division_name
        ORDER BY total_voucher DESC
        """,
        (period_month,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_menu_usage_report(period_month):
    """
    Rekap menu paling banyak terjual berdasarkan detail item.
    Hanya transaksi valid.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            vti.item_name_snapshot,
            COALESCE(SUM(vti.quantity), 0) AS total_quantity,
            COALESCE(SUM(vti.subtotal), 0) AS total_subtotal
        FROM voucher_transaction_items vti
        JOIN voucher_transactions vt ON vt.id = vti.transaction_id
        WHERE vt.period_month = ?
        AND vt.voided_at IS NULL
        GROUP BY vti.item_name_snapshot
        ORDER BY total_quantity DESC, total_subtotal DESC
        """,
        (period_month,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_merchant_payment_report(period_month):
    """
    Laporan pembayaran pedagang.
    Yang dibayar kantor adalah total voucher_amount valid.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            m.id AS merchant_id,
            m.merchant_name,
            COUNT(vt.id) AS total_transactions,
            COUNT(DISTINCT vt.employee_id) AS total_employees,
            COALESCE(SUM(vt.total_amount), 0) AS total_sales,
            COALESCE(SUM(vt.voucher_amount), 0) AS total_voucher_payment,
            COALESCE(SUM(vt.cash_amount), 0) AS total_cash
        FROM merchants m
        LEFT JOIN voucher_transactions vt
            ON vt.merchant_id = m.id
            AND vt.period_month = ?
            AND vt.voided_at IS NULL
        WHERE m.is_active = 1
        GROUP BY m.id, m.merchant_name
        ORDER BY m.merchant_name ASC
        """,
        (period_month,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_employee_balance_report(period_month):
    """
    Laporan saldo semua pegawai yang punya alokasi pada periode tertentu.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            e.employee_code,
            e.full_name,
            COALESCE(d.division_name, '-') AS division_name,
            ma.amount_allocated,
            COALESCE(SUM(vt.voucher_amount), 0) AS used_amount,
            ma.amount_allocated - COALESCE(SUM(vt.voucher_amount), 0) AS remaining_balance
        FROM monthly_allocations ma
        JOIN employees e ON e.id = ma.employee_id
        LEFT JOIN divisions d ON d.id = e.division_id
        LEFT JOIN voucher_transactions vt
            ON vt.employee_id = ma.employee_id
            AND vt.period_month = ma.period_month
            AND vt.voided_at IS NULL
        WHERE ma.period_month = ?
        AND ma.status = 'active'
        GROUP BY
            e.employee_code,
            e.full_name,
            d.division_name,
            ma.amount_allocated
        ORDER BY e.employee_code ASC
        """,
        (period_month,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

# =========================================================
# VOID TRANSAKSI
# =========================================================

def get_voidable_transactions(period_month=None):
    """
    Mengambil transaksi yang bisa di-void.
    Transaksi yang sudah void tetap ditampilkan agar admin bisa melihat statusnya.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if period_month:
        cursor.execute(
            """
            SELECT
                vt.id,
                vt.period_month,
                vt.transaction_date,
                e.employee_code,
                e.full_name,
                COALESCE(d.division_name, '-') AS division_name,
                m.merchant_name,
                vt.total_amount,
                vt.voucher_amount,
                vt.cash_amount,
                vt.notes,
                vt.created_at,
                vt.voided_at,
                vt.void_reason,
                created_user.username AS created_by_username,
                void_user.username AS voided_by_username
            FROM voucher_transactions vt
            JOIN employees e ON e.id = vt.employee_id
            LEFT JOIN divisions d ON d.id = e.division_id
            JOIN merchants m ON m.id = vt.merchant_id
            LEFT JOIN users created_user ON created_user.id = vt.created_by
            LEFT JOIN users void_user ON void_user.id = vt.voided_by
            WHERE vt.period_month = ?
            ORDER BY vt.created_at DESC
            """,
            (period_month,)
        )
    else:
        cursor.execute(
            """
            SELECT
                vt.id,
                vt.period_month,
                vt.transaction_date,
                e.employee_code,
                e.full_name,
                COALESCE(d.division_name, '-') AS division_name,
                m.merchant_name,
                vt.total_amount,
                vt.voucher_amount,
                vt.cash_amount,
                vt.notes,
                vt.created_at,
                vt.voided_at,
                vt.void_reason,
                created_user.username AS created_by_username,
                void_user.username AS voided_by_username
            FROM voucher_transactions vt
            JOIN employees e ON e.id = vt.employee_id
            LEFT JOIN divisions d ON d.id = e.division_id
            JOIN merchants m ON m.id = vt.merchant_id
            LEFT JOIN users created_user ON created_user.id = vt.created_by
            LEFT JOIN users void_user ON void_user.id = vt.voided_by
            ORDER BY vt.created_at DESC
            """
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_transaction_by_id(transaction_id):
    """
    Mengambil satu transaksi berdasarkan ID.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            vt.id,
            vt.employee_id,
            vt.merchant_id,
            vt.period_month,
            vt.transaction_date,
            e.employee_code,
            e.full_name,
            COALESCE(d.division_name, '-') AS division_name,
            m.merchant_name,
            vt.total_amount,
            vt.voucher_amount,
            vt.cash_amount,
            vt.notes,
            vt.created_by,
            vt.created_at,
            vt.voided_at,
            vt.voided_by,
            vt.void_reason
        FROM voucher_transactions vt
        JOIN employees e ON e.id = vt.employee_id
        LEFT JOIN divisions d ON d.id = e.division_id
        JOIN merchants m ON m.id = vt.merchant_id
        WHERE vt.id = ?
        """,
        (transaction_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return dict(row)


def void_transaction(transaction_id, void_reason, voided_by=None):
    """
    Membatalkan transaksi dengan alasan.
    Data transaksi tidak dihapus.
    """
    transaction = get_transaction_by_id(transaction_id)

    if transaction is None:
        return {
            "success": False,
            "message": "Transaksi tidak ditemukan."
        }

    if transaction["voided_at"] is not None:
        return {
            "success": False,
            "message": "Transaksi ini sudah pernah di-void."
        }

    reason_clean = void_reason.strip()

    if reason_clean == "":
        return {
            "success": False,
            "message": "Alasan void wajib diisi."
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE voucher_transactions
        SET
            voided_at = ?,
            voided_by = ?,
            void_reason = ?
        WHERE id = ?
        """,
        (
            get_now_text(),
            voided_by,
            reason_clean,
            transaction_id,
        )
    )

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=voided_by,
        action="VOID_TRANSACTION",
        table_name="voucher_transactions",
        record_id=transaction_id,
        description=(
            f"Void transaksi ID {transaction_id}. "
            f"Pegawai: {transaction['employee_code']} - {transaction['full_name']}. "
            f"Nominal voucher: {transaction['voucher_amount']}. "
            f"Alasan: {reason_clean}"
        )
    )

    return {
        "success": True,
        "message": "Transaksi berhasil di-void."
    }


def get_void_transaction_summary(period_month):
    """
    Ringkasan transaksi valid dan void pada periode tertentu.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS total_valid
        FROM voucher_transactions
        WHERE period_month = ?
        AND voided_at IS NULL
        """,
        (period_month,)
    )
    total_valid = cursor.fetchone()["total_valid"]

    cursor.execute(
        """
        SELECT COUNT(*) AS total_void
        FROM voucher_transactions
        WHERE period_month = ?
        AND voided_at IS NOT NULL
        """,
        (period_month,)
    )
    total_void = cursor.fetchone()["total_void"]

    cursor.execute(
        """
        SELECT COALESCE(SUM(voucher_amount), 0) AS total_valid_voucher
        FROM voucher_transactions
        WHERE period_month = ?
        AND voided_at IS NULL
        """,
        (period_month,)
    )
    total_valid_voucher = cursor.fetchone()["total_valid_voucher"]

    cursor.execute(
        """
        SELECT COALESCE(SUM(voucher_amount), 0) AS total_void_voucher
        FROM voucher_transactions
        WHERE period_month = ?
        AND voided_at IS NOT NULL
        """,
        (period_month,)
    )
    total_void_voucher = cursor.fetchone()["total_void_voucher"]

    conn.close()

    return {
        "total_valid": total_valid,
        "total_void": total_void,
        "total_valid_voucher": total_valid_voucher,
        "total_void_voucher": total_void_voucher,
    }
# =========================================================
# BACKUP DATABASE
# =========================================================

def create_database_backup():
    """
    Membuat backup file SQLite ke folder data/backups.
    Return path file backup.
    """
    BACKUP_DIR = DATA_DIR / "backups"
    BACKUP_DIR.mkdir(exist_ok=True)

    timestamp = get_now_text().replace(":", "-")
    backup_path = BACKUP_DIR / f"evoucher_backup_{timestamp}.db"

    if not DB_PATH.exists():
        return {
            "success": False,
            "message": "File database belum ditemukan.",
            "backup_path": None,
        }

    shutil.copy2(DB_PATH, backup_path)

    return {
        "success": True,
        "message": "Backup database berhasil dibuat.",
        "backup_path": backup_path,
    }


def get_backup_files():
    """
    Mengambil daftar file backup database.
    """
    BACKUP_DIR = DATA_DIR / "backups"
    BACKUP_DIR.mkdir(exist_ok=True)

    backup_files = []

    for file_path in sorted(BACKUP_DIR.glob("*.db"), reverse=True):
        backup_files.append(
            {
                "filename": file_path.name,
                "path": str(file_path),
                "size_kb": round(file_path.stat().st_size / 1024, 2),
                "modified_at": file_path.stat().st_mtime,
            }
        )

    return backup_files

# =========================================================
# SETTINGS DAN GENERATE VOUCHER RESMI
# =========================================================

def get_all_settings():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT key, value, updated_at
        FROM settings
        ORDER BY key ASC
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def update_setting(key, value, updated_by=None):
    """
    Update atau insert setting aplikasi.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key)
        DO UPDATE SET
            value = excluded.value,
            updated_at = excluded.updated_at
        """,
        (key, str(value), get_now_text())
    )

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=updated_by,
        action="UPDATE_SETTING",
        table_name="settings",
        record_id=None,
        description=f"Mengubah setting {key} menjadi {value}"
    )


def get_setting_bool(key, default_value=False):
    value = get_setting_value(key, None)

    if value is None:
        return default_value

    return str(value).lower() in ["true", "1", "yes", "y"]


def get_setting_int(key, default_value=0):
    value = get_setting_value(key, None)

    if value is None:
        return default_value

    try:
        return int(value)
    except ValueError:
        return default_value


def get_active_employee_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM employees
        WHERE is_active = 1
        """
    )

    total = cursor.fetchone()["total"]
    conn.close()

    return total


def get_monthly_allocation_summary(period_month):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) AS total_allocations
        FROM monthly_allocations
        WHERE period_month = ?
        AND status = 'active'
        """,
        (period_month,)
    )
    total_allocations = cursor.fetchone()["total_allocations"]

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount_allocated), 0) AS total_amount
        FROM monthly_allocations
        WHERE period_month = ?
        AND status = 'active'
        """,
        (period_month,)
    )
    total_amount = cursor.fetchone()["total_amount"]

    cursor.execute(
        """
        SELECT COUNT(*) AS total_active_employees
        FROM employees
        WHERE is_active = 1
        """
    )
    total_active_employees = cursor.fetchone()["total_active_employees"]

    conn.close()

    return {
        "period_month": period_month,
        "total_allocations": total_allocations,
        "total_amount": total_amount,
        "total_active_employees": total_active_employees,
        "not_allocated_count": total_active_employees - total_allocations,
    }


def get_monthly_allocations_with_employee(period_month=None):
    conn = get_connection()
    cursor = conn.cursor()

    if period_month:
        cursor.execute(
            """
            SELECT
                ma.id,
                ma.period_month,
                e.employee_code,
                e.full_name,
                COALESCE(d.division_name, '-') AS division_name,
                ma.amount_allocated,
                ma.status,
                ma.generated_at,
                u.username AS generated_by_username
            FROM monthly_allocations ma
            JOIN employees e ON e.id = ma.employee_id
            LEFT JOIN divisions d ON d.id = e.division_id
            LEFT JOIN users u ON u.id = ma.generated_by
            WHERE ma.period_month = ?
            ORDER BY e.employee_code ASC
            """,
            (period_month,)
        )
    else:
        cursor.execute(
            """
            SELECT
                ma.id,
                ma.period_month,
                e.employee_code,
                e.full_name,
                COALESCE(d.division_name, '-') AS division_name,
                ma.amount_allocated,
                ma.status,
                ma.generated_at,
                u.username AS generated_by_username
            FROM monthly_allocations ma
            JOIN employees e ON e.id = ma.employee_id
            LEFT JOIN divisions d ON d.id = e.division_id
            LEFT JOIN users u ON u.id = ma.generated_by
            ORDER BY ma.period_month DESC, e.employee_code ASC
            """
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def generate_monthly_voucher_official(period_month, generated_by=None):
    """
    Generate voucher bulanan resmi untuk semua pegawai aktif.
    Nominal diambil dari settings.monthly_voucher_amount.
    Sistem mencegah alokasi dobel berdasarkan UNIQUE(employee_id, period_month).
    """
    amount = get_setting_int("monthly_voucher_amount", 75000)

    if amount <= 0:
        return {
            "success": False,
            "message": "Nominal voucher bulanan harus lebih dari 0.",
            "created": 0,
            "skipped": 0,
            "active_employees": 0,
            "amount": amount,
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM employees
        WHERE is_active = 1
        ORDER BY employee_code ASC
        """
    )

    active_employees = cursor.fetchall()

    created = 0
    skipped = 0

    try:
        cursor.execute("BEGIN")

        for employee in active_employees:
            employee_id = employee["id"]

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM monthly_allocations
                WHERE employee_id = ?
                AND period_month = ?
                """,
                (employee_id, period_month)
            )

            exists = cursor.fetchone()["total"] > 0

            if exists:
                skipped += 1
                continue

            cursor.execute(
                """
                INSERT INTO monthly_allocations
                (
                    employee_id,
                    period_month,
                    amount_allocated,
                    generated_by,
                    generated_at,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    employee_id,
                    period_month,
                    amount,
                    generated_by,
                    get_now_text(),
                    "active",
                )
            )

            created += 1

        conn.commit()

    except Exception as error:
        conn.rollback()
        conn.close()

        return {
            "success": False,
            "message": f"Gagal generate voucher: {error}",
            "created": created,
            "skipped": skipped,
            "active_employees": len(active_employees),
            "amount": amount,
        }

    conn.close()

    insert_audit_log(
        user_id=generated_by,
        action="GENERATE_VOUCHER_OFFICIAL",
        table_name="monthly_allocations",
        record_id=None,
        description=(
            f"Generate voucher resmi periode {period_month}. "
            f"Pegawai aktif={len(active_employees)}, "
            f"created={created}, skipped={skipped}, amount={amount}"
        )
    )

    return {
        "success": True,
        "message": "Generate voucher bulanan selesai.",
        "created": created,
        "skipped": skipped,
        "active_employees": len(active_employees),
        "amount": amount,
    }

# =========================================================
# USER MANAGEMENT DAN GANTI PASSWORD
# =========================================================

def password_to_hash(password):
    """
    Membuat hash password baru menggunakan bcrypt.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def get_users_with_employee():
    """
    Mengambil daftar user beserta data pegawai jika terhubung.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            u.id,
            u.username,
            u.role,
            u.employee_id,
            e.employee_code,
            e.full_name,
            COALESCE(d.division_name, '-') AS division_name,
            u.is_active,
            u.created_at,
            u.updated_at,
            u.last_login_at
        FROM users u
        LEFT JOIN employees e ON e.id = u.employee_id
        LEFT JOIN divisions d ON d.id = e.division_id
        ORDER BY u.role ASC, u.username ASC
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def username_exists(username, exclude_id=None):
    """
    Mengecek username duplikat.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if exclude_id is None:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM users
            WHERE LOWER(username) = LOWER(?)
            """,
            (username,)
        )
    else:
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM users
            WHERE LOWER(username) = LOWER(?)
            AND id != ?
            """,
            (username, exclude_id)
        )

    total = cursor.fetchone()["total"]
    conn.close()

    return total > 0


def create_user(username, password, role, employee_id=None, is_active=1, created_by=None):
    """
    Membuat user baru.
    """
    username_clean = username.strip().lower()

    if username_clean == "":
        return {
            "success": False,
            "message": "Username tidak boleh kosong."
        }

    if password == "":
        return {
            "success": False,
            "message": "Password tidak boleh kosong."
        }

    if role not in ["admin", "kasir", "pegawai"]:
        return {
            "success": False,
            "message": "Role tidak valid."
        }

    if role == "pegawai" and employee_id is None:
        return {
            "success": False,
            "message": "User role pegawai harus dihubungkan ke data pegawai."
        }

    if role in ["admin", "kasir"]:
        employee_id = None

    if username_exists(username_clean):
        return {
            "success": False,
            "message": "Username sudah digunakan."
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users
        (username, password_hash, role, employee_id, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            username_clean,
            password_to_hash(password),
            role,
            employee_id,
            is_active,
            get_now_text(),
        )
    )

    user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=created_by,
        action="CREATE_USER",
        table_name="users",
        record_id=user_id,
        description=f"Membuat user {username_clean} dengan role {role}"
    )

    return {
        "success": True,
        "message": "User berhasil dibuat.",
        "user_id": user_id,
    }


def update_user_basic(user_id, username, role, employee_id, is_active, updated_by=None):
    """
    Update username, role, employee link, dan status user.
    Password tidak diubah di fungsi ini.
    """
    existing_user = get_user_by_id(user_id)

    if existing_user is None:
        return {
            "success": False,
            "message": "User tidak ditemukan."
        }

    username_clean = username.strip().lower()

    if username_clean == "":
        return {
            "success": False,
            "message": "Username tidak boleh kosong."
        }

    if role not in ["admin", "kasir", "pegawai"]:
        return {
            "success": False,
            "message": "Role tidak valid."
        }

    if username_exists(username_clean, exclude_id=user_id):
        return {
            "success": False,
            "message": "Username sudah digunakan oleh user lain."
        }

    if role == "pegawai" and employee_id is None:
        return {
            "success": False,
            "message": "User role pegawai harus dihubungkan ke data pegawai."
        }

    if role in ["admin", "kasir"]:
        employee_id = None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET
            username = ?,
            role = ?,
            employee_id = ?,
            is_active = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            username_clean,
            role,
            employee_id,
            is_active,
            get_now_text(),
            user_id,
        )
    )

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=updated_by,
        action="UPDATE_USER",
        table_name="users",
        record_id=user_id,
        description=f"Mengubah user {username_clean}, role {role}, active={is_active}"
    )

    return {
        "success": True,
        "message": "User berhasil diupdate."
    }


def reset_user_password(user_id, new_password, updated_by=None):
    """
    Admin reset password user.
    """
    existing_user = get_user_by_id(user_id)

    if existing_user is None:
        return {
            "success": False,
            "message": "User tidak ditemukan."
        }

    if new_password.strip() == "":
        return {
            "success": False,
            "message": "Password baru tidak boleh kosong."
        }

    if len(new_password) < 6:
        return {
            "success": False,
            "message": "Password minimal 6 karakter."
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET password_hash = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            password_to_hash(new_password),
            get_now_text(),
            user_id,
        )
    )

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=updated_by,
        action="RESET_PASSWORD",
        table_name="users",
        record_id=user_id,
        description=f"Reset password user ID {user_id}"
    )

    return {
        "success": True,
        "message": "Password user berhasil direset."
    }


def get_user_password_hash(user_id):
    """
    Mengambil password hash user untuk validasi ganti password.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT password_hash
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return row["password_hash"]


def verify_password_backend(plain_password, password_hash):
    """
    Verifikasi password di backend.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except Exception:
        return False


def change_own_password(user_id, old_password, new_password, confirm_password):
    """
    User mengganti password sendiri.
    """
    if old_password == "":
        return {
            "success": False,
            "message": "Password lama wajib diisi."
        }

    if new_password == "":
        return {
            "success": False,
            "message": "Password baru wajib diisi."
        }

    if len(new_password) < 6:
        return {
            "success": False,
            "message": "Password baru minimal 6 karakter."
        }

    if new_password != confirm_password:
        return {
            "success": False,
            "message": "Konfirmasi password tidak sama."
        }

    current_hash = get_user_password_hash(user_id)

    if current_hash is None:
        return {
            "success": False,
            "message": "User tidak ditemukan."
        }

    if not verify_password_backend(old_password, current_hash):
        return {
            "success": False,
            "message": "Password lama salah."
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET password_hash = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            password_to_hash(new_password),
            get_now_text(),
            user_id,
        )
    )

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=user_id,
        action="CHANGE_OWN_PASSWORD",
        table_name="users",
        record_id=user_id,
        description="User mengganti password sendiri"
    )

    return {
        "success": True,
        "message": "Password berhasil diganti. Silakan gunakan password baru pada login berikutnya."
    }


def get_employees_without_user():
    """
    Mengambil pegawai aktif yang belum punya user role pegawai.
    Berguna saat membuat akun pegawai baru.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            e.id,
            e.employee_code,
            e.full_name,
            COALESCE(d.division_name, '-') AS division_name
        FROM employees e
        LEFT JOIN divisions d ON d.id = e.division_id
        WHERE e.is_active = 1
        AND e.id NOT IN (
            SELECT employee_id
            FROM users
            WHERE employee_id IS NOT NULL
        )
        ORDER BY e.employee_code ASC
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

# =========================================================
# IMPORT PEGAWAI DARI EXCEL
# =========================================================

def get_or_create_division_by_name(division_name, created_by=None):
    """
    Mengambil ID divisi berdasarkan nama.
    Jika belum ada, divisi otomatis dibuat.
    """
    division_name_clean = str(division_name).strip()

    if division_name_clean == "":
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM divisions
        WHERE LOWER(division_name) = LOWER(?)
        """,
        (division_name_clean,)
    )

    row = cursor.fetchone()

    if row is not None:
        conn.close()
        return row["id"]

    cursor.execute(
        """
        INSERT INTO divisions
        (division_name, is_active, created_at)
        VALUES (?, ?, ?)
        """,
        (division_name_clean, 1, get_now_text())
    )

    division_id = cursor.lastrowid

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=created_by,
        action="AUTO_CREATE_DIVISION_IMPORT",
        table_name="divisions",
        record_id=division_id,
        description=f"Auto create divisi dari import pegawai: {division_name_clean}"
    )

    return division_id


def import_employees_from_dataframe(df, imported_by=None):
    """
    Import pegawai dari pandas DataFrame.

    Kolom wajib:
    - employee_code
    - full_name
    - division_name

    Kolom opsional:
    - phone
    - email
    - is_active
    """
    required_columns = ["employee_code", "full_name", "division_name"]

    for column in required_columns:
        if column not in df.columns:
            return {
                "success": False,
                "message": f"Kolom wajib tidak ditemukan: {column}",
                "created": 0,
                "skipped": 0,
                "errors": [],
            }

    created = 0
    skipped = 0
    errors = []

    conn = get_connection()
    cursor = conn.cursor()

    for index, row in df.iterrows():
        excel_row_number = index + 2

        try:
            employee_code = str(row.get("employee_code", "")).strip().upper()
            full_name = str(row.get("full_name", "")).strip()
            division_name = str(row.get("division_name", "")).strip()
            phone = str(row.get("phone", "")).strip() if "phone" in df.columns else ""
            email = str(row.get("email", "")).strip() if "email" in df.columns else ""

            if "is_active" in df.columns:
                raw_active = row.get("is_active", 1)

                try:
                    is_active = int(raw_active)
                except Exception:
                    is_active = 1

                if is_active not in [0, 1]:
                    is_active = 1
            else:
                is_active = 1

            if employee_code == "" or employee_code.lower() == "nan":
                errors.append(f"Baris {excel_row_number}: employee_code kosong.")
                continue

            if full_name == "" or full_name.lower() == "nan":
                errors.append(f"Baris {excel_row_number}: full_name kosong.")
                continue

            if division_name == "" or division_name.lower() == "nan":
                errors.append(f"Baris {excel_row_number}: division_name kosong.")
                continue

            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM employees
                WHERE LOWER(employee_code) = LOWER(?)
                """,
                (employee_code,)
            )

            exists = cursor.fetchone()["total"] > 0

            if exists:
                skipped += 1
                continue

            division_id = get_or_create_division_by_name(
                division_name=division_name,
                created_by=imported_by,
            )

            if division_id is None:
                errors.append(f"Baris {excel_row_number}: divisi tidak valid.")
                continue

            cursor.execute(
                """
                INSERT INTO employees
                (
                    employee_code,
                    full_name,
                    division_id,
                    phone,
                    email,
                    is_active,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    employee_code,
                    full_name,
                    division_id,
                    phone,
                    email,
                    is_active,
                    get_now_text(),
                )
            )

            created += 1

        except Exception as error:
            errors.append(f"Baris {excel_row_number}: {error}")

    conn.commit()
    conn.close()

    insert_audit_log(
        user_id=imported_by,
        action="IMPORT_EMPLOYEES_EXCEL",
        table_name="employees",
        record_id=None,
        description=f"Import pegawai dari Excel. Created={created}, skipped={skipped}, errors={len(errors)}"
    )

    return {
        "success": True,
        "message": "Proses import pegawai selesai.",
        "created": created,
        "skipped": skipped,
        "errors": errors,
    }