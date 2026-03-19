#!/usr/bin/env python3
"""Create an admin user in SQLite database using passlib argon2"""
import sqlite3
import uuid
from passlib.context import CryptContext

# Admin credentials
admin_email = "admin@digitalbank.com"
admin_password = "Admin@123456"
admin_name = "System Administrator"
admin_phone = "+1-800-000-0000"

# Hash password using argon2 (same as the app)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
password_hash = pwd_context.hash(admin_password)

try:
    # Connect to database
    conn = sqlite3.connect('./bank.db')
    cursor = conn.cursor()

    # Check if admin already exists
    cursor.execute("SELECT * FROM users WHERE email = ?", (admin_email,))
    existing = cursor.fetchone()

    if existing:
        print("[OK] Admin user already exists:", admin_email)
    else:
        # Create admin user
        admin_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, phone, role, kyc_level, kyc_status, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            admin_id,
            admin_email,
            password_hash,
            admin_name,
            admin_phone,
            "admin",
            3,
            "approved",
            True
        ))

        conn.commit()
        print("[OK] Admin user created successfully!")
        print("")
        print("ADMIN CREDENTIALS:")
        print("  Email:    ", admin_email)
        print("  Password: Admin@123456")
        print("  Role:     admin")
        print("  KYC:      Level 3 (Approved)")
except Exception as e:
    print("[ERROR]", e)
finally:
    if 'conn' in locals():
        conn.close()
