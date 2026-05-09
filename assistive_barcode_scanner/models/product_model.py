import sqlite3


def get_connection():
    conn = sqlite3.connect("database/products.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_product_by_barcode(barcode):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products WHERE barcode=?",
        (barcode,)
    )

    product = cursor.fetchone()
    conn.close()

    return product


def insert_product(barcode, name, category, price):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products (barcode, name, category, price)
        VALUES (?, ?, ?, ?)
        """,
        (barcode, name, category, price)
    )

    conn.commit()
    conn.close()