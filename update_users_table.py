import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN email TEXT"
    )
except:
    pass

try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN phone TEXT"
    )
except:
    pass

try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0"
    )
except:
    pass

try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN profile_picture TEXT"
    )
except:
    pass

conn.commit()
conn.close()

print("Users table updated successfully")