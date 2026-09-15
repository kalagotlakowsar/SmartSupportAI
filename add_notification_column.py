import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

try:

    cursor.execute("""
        ALTER TABLE tickets
        ADD COLUMN notification_read INTEGER DEFAULT 0
    """)

    print("Notification column added successfully.")

except sqlite3.OperationalError as e:

    if "duplicate column name" in str(e).lower():

        print("Notification column already exists.")

    else:

        print("Error:", e)

conn.commit()
conn.close()