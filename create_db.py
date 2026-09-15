import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
    order_id TEXT PRIMARY KEY,
    customer_name TEXT,
    product_name TEXT,
    status TEXT
)
""")

cursor.execute("""
INSERT OR IGNORE INTO orders
VALUES
('101','John','Laptop','Shipped')
""")

cursor.execute("""
INSERT OR IGNORE INTO orders
VALUES
('102','John','Mobile','Out for Delivery')
""")

cursor.execute("""
INSERT OR IGNORE INTO orders
VALUES
('103','John','Headphones','Delivered')
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tickets(
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_query TEXT,
    status TEXT
)
""")
# Add priority column if it does not already exist
try:
    cursor.execute("ALTER TABLE tickets ADD COLUMN priority TEXT DEFAULT 'Normal'")
except sqlite3.OperationalError:
    pass

# --------------------------------
# USERS TABLE
# --------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    profile_picture TEXT,
    email_verified INTEGER DEFAULT 0,
    phone_verified INTEGER DEFAULT 0
)
""")
# Add new profile columns to existing users table

try:
    cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE users ADD COLUMN profile_picture TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0"
    )
except sqlite3.OperationalError:
    pass

try:
    cursor.execute(
        "ALTER TABLE users ADD COLUMN phone_verified INTEGER DEFAULT 0"
    )
except sqlite3.OperationalError:
    pass

# Add user_id column to tickets
try:
    cursor.execute(
        "ALTER TABLE tickets ADD COLUMN user_id INTEGER"
    )
except sqlite3.OperationalError:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS pending_registrations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    email_otp TEXT,
    email_verified INTEGER DEFAULT 0,
    phone_verified INTEGER DEFAULT 0
)
""")

# --------------------------------
# TICKET REPLIES TABLE
# --------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS ticket_replies(
    reply_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    user_id INTEGER,
    sender_role TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# --------------------------------
# SETTINGS TABLE
# --------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_notifications INTEGER DEFAULT 1,
    high_priority_alerts INTEGER DEFAULT 1,
    ai_agent_activity INTEGER DEFAULT 1
)
""")

# Create default settings if no record exists
cursor.execute("SELECT COUNT(*) FROM settings")

if cursor.fetchone()[0] == 0:

    cursor.execute("""
        INSERT INTO settings
        (ticket_notifications, high_priority_alerts, ai_agent_activity)
        VALUES (1, 1, 1)
    """)

conn.commit()
conn.close()

print("Database Created Successfully")

