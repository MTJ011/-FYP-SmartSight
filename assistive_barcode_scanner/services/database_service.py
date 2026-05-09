import sqlite3

DB_PATH = "database/prices.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            barcode TEXT PRIMARY KEY,
            name TEXT,
            brand TEXT,
            category TEXT,
            price INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def get_local_price(barcode):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT price, name, category FROM prices WHERE barcode=?", (barcode,))
    row = cur.fetchone()

    conn.close()

    if row:
        return row[0], row[1], row[2]

    return None, None, None


def save_local_price(barcode, name, brand, category, price):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO prices (barcode, name, brand, category, price)
        VALUES (?, ?, ?, ?, ?)
    """, (barcode, name, brand, category, price))

    conn.commit()
    conn.close()

    print(f"✅ Price saved: {barcode} - {name} = {price} PKR")