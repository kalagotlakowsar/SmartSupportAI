import sqlite3
from werkzeug.security import generate_password_hash


username = input("Enter Admin username: ").strip()
email = input("Enter Admin email: ").strip()
phone = input("Enter Admin phone: ").strip()
password = input("Enter Admin password: ")


password_hash = generate_password_hash(password)


conn = sqlite3.connect("database.db")
cursor = conn.cursor()


try:

    cursor.execute(
        """
        INSERT INTO users
        (username, password, role, email, phone, email_verified)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            password_hash,
            "Admin",
            email,
            phone,
            1
        )
    )

    conn.commit()

    print()
    print("Admin account created successfully!")
    print("Username:", username)
    print("Role: Admin")

except sqlite3.IntegrityError:

    print()
    print("Username already exists.")


conn.close()