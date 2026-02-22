import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uni_platform.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS uni_daily (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_date TEXT NOT NULL,
        currency_code INTEGER NOT NULL,
        exchange_rate REAL NOT NULL,
        created_at DATETIME DEFAULT (datetime('now', 'localtime')),
        UNIQUE(record_date, currency_code)
    );

    CREATE TABLE IF NOT EXISTS uni_emp (
        emp_id TEXT PRIMARY KEY CHECK(length(emp_id) = 3),
        department TEXT,
        position TEXT,
        emp_name TEXT NOT NULL,
        contact TEXT,
        account TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        hire_date TEXT,
        rule TEXT NOT NULL,
        remark TEXT,
        created_at DATETIME DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS uni_cli (
        cli_id TEXT PRIMARY KEY,
        cli_name TEXT NOT NULL,
        region TEXT NOT NULL DEFAULT '韩国',
        credit_level TEXT DEFAULT 'A',
        margin_rate REAL DEFAULT 10.0,
        emp_id TEXT NOT NULL,
        website TEXT,
        payment_terms TEXT,
        email TEXT,
        phone TEXT,
        remark TEXT,
        created_at DATETIME DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (emp_id) REFERENCES uni_emp(emp_id) ON UPDATE CASCADE
    );

    CREATE TABLE IF NOT EXISTS uni_quote (
        quote_id TEXT PRIMARY KEY,
        quote_date TEXT,
        cli_id TEXT NOT NULL,
        inquiry_mpn TEXT NOT NULL,
        quoted_mpn TEXT,
        inquiry_brand TEXT,
        inquiry_qty INTEGER,
        target_price_rmb REAL,
        cost_price_rmb REAL,
        remark TEXT,
        created_at DATETIME DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (cli_id) REFERENCES uni_cli(cli_id) ON UPDATE CASCADE
    );

    CREATE TABLE IF NOT EXISTS uni_vendor (
        vendor_id TEXT PRIMARY KEY,
        vendor_name TEXT NOT NULL,
        address TEXT,
        qq TEXT,
        wechat TEXT,
        email TEXT,
        remark TEXT,
        created_at DATETIME DEFAULT (datetime('now', 'localtime'))
    );

    CREATE TABLE IF NOT EXISTS uni_offer (
        offer_id TEXT PRIMARY KEY,
        offer_date TEXT,
        quote_id TEXT,
        inquiry_mpn TEXT,
        quoted_mpn TEXT,
        inquiry_brand TEXT,
        quoted_brand TEXT,
        inquiry_qty INTEGER,
        actual_qty INTEGER,
        quoted_qty INTEGER,
        cost_price_rmb REAL,
        offer_price_rmb REAL,
        platform TEXT,
        vendor_id TEXT,
        date_code TEXT,
        delivery_date TEXT,
        emp_id TEXT NOT NULL,
        offer_statement TEXT,
        remark TEXT,
        created_at DATETIME DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (quote_id) REFERENCES uni_quote(quote_id),
        FOREIGN KEY (vendor_id) REFERENCES uni_vendor(vendor_id),
        FOREIGN KEY (emp_id) REFERENCES uni_emp(emp_id)
    );

    CREATE TABLE IF NOT EXISTS uni_order (
        order_id TEXT PRIMARY KEY,
        order_date TEXT,
        cli_id TEXT NOT NULL,
        offer_id TEXT NOT NULL,
        is_finished INTEGER DEFAULT 0 CHECK(is_finished IN (0,1)),
        is_paid INTEGER DEFAULT 0 CHECK(is_paid IN (0,1)),
        paid_amount REAL DEFAULT 0.0,
        remark TEXT,
        created_at DATETIME DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (cli_id) REFERENCES uni_cli(cli_id),
        FOREIGN KEY (offer_id) REFERENCES uni_offer(offer_id)
    );

    CREATE TABLE IF NOT EXISTS uni_buy (
        buy_id TEXT PRIMARY KEY,
        buy_date TEXT,
        order_id TEXT,
        vendor_id TEXT,
        buy_mpn TEXT,
        buy_brand TEXT,
        buy_price_rmb REAL,
        buy_qty INTEGER,
        sales_price_rmb REAL,
        total_amount REAL,
        is_source_confirmed INTEGER DEFAULT 0 CHECK(is_source_confirmed IN (0,1)),
        is_ordered INTEGER DEFAULT 0 CHECK(is_ordered IN (0,1)),
        is_instock INTEGER DEFAULT 0 CHECK(is_instock IN (0,1)),
        is_shipped INTEGER DEFAULT 0 CHECK(is_shipped IN (0,1)),
        remark TEXT,
        created_at DATETIME DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (order_id) REFERENCES uni_order(order_id),
        FOREIGN KEY (vendor_id) REFERENCES uni_vendor(vendor_id)
    );
    """
    with get_db_connection() as conn:
        conn.executescript(schema)
        conn.commit()

def get_paginated_list(table_name, page=1, page_size=10, search_kwargs=None):
    """
    Generic pagination and fuzzy search
    search_kwargs: {column_name: value}
    """
    offset = (page - 1) * page_size
    query = f"SELECT * FROM {table_name}"
    params = []

    if search_kwargs:
        conditions = []
        for col, val in search_kwargs.items():
            conditions.append(f"{col} LIKE ?")
            params.append(f"%{val}%")
        query += " WHERE " + " AND ".join(conditions)

    count_query = f"SELECT COUNT(*) FROM ({query})"
    query += f" ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}"

    with get_db_connection() as conn:
        total_count = conn.execute(count_query, params).fetchone()[0]
        items = conn.execute(query, params).fetchall()
        
    return {
        "items": [dict(row) for row in items],
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
