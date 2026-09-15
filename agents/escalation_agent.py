import sqlite3


def create_ticket(user_query, priority="Normal", user_id=None):

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tickets(
            user_query,
            status,
            priority,
            user_id
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_query,
            "Open",
            priority,
            user_id
        )
    )

    conn.commit()

    ticket_id = cursor.lastrowid

    conn.close()

    return ticket_id