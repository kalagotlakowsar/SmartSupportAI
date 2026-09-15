import sqlite3


def get_order_details(order_id):

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT order_id, customer_name, product_name, status
        FROM orders
        WHERE order_id=?
        """,
        (order_id,)
    )

    result = cursor.fetchone()

    conn.close()

    return result