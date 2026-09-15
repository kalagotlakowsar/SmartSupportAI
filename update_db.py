import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("""
ALTER TABLE tickets
ADD COLUMN assigned_agent TEXT
""")

conn.commit()
conn.close()

print("assigned_agent column added successfully")