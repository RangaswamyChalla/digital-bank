#!/usr/bin/env python3
"""Create demo users, accounts, and transactions for a polished demo"""
import sqlite3
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Connect to database
conn = sqlite3.connect('./bank.db')
cursor = conn.cursor()

# Hash password using argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
password_hash = pwd_context.hash("Demo@123456")

# Demo users
demo_users = [
    {
        "email": "john.doe@demo.com",
        "full_name": "John Doe",
        "phone": "+1-555-0101",
        "role": "customer",
        "kyc_level": 3,
        "kyc_status": "approved"
    },
    {
        "email": "jane.smith@demo.com",
        "full_name": "Jane Smith",
        "phone": "+1-555-0102",
        "role": "customer",
        "kyc_level": 2,
        "kyc_status": "approved"
    },
    {
        "email": "demo.user@demo.com",
        "full_name": "Demo User",
        "phone": "+1-555-0100",
        "role": "customer",
        "kyc_level": 3,
        "kyc_status": "approved"
    }
]

created_users = []

for user_data in demo_users:
    cursor.execute("SELECT * FROM users WHERE email = ?", (user_data["email"],))
    existing = cursor.fetchone()

    if existing:
        print("[OK] User exists:", user_data["email"])
        cursor.execute("SELECT id FROM users WHERE email = ?", (user_data["email"],))
        user_id = cursor.fetchone()[0]
        created_users.append({"id": user_id, "email": user_data["email"]})
    else:
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email, password_hash, full_name, phone, role, kyc_level, kyc_status, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            user_id,
            user_data["email"],
            password_hash,
            user_data["full_name"],
            user_data["phone"],
            user_data["role"],
            user_data["kyc_level"],
            user_data["kyc_status"],
            True
        ))
        print("[OK] Created user:", user_data["email"])
        created_users.append({"id": user_id, "email": user_data["email"]})

conn.commit()

# Create accounts for demo users (only if they don't exist)
created_accounts = []

for user in created_users:
    for i, (acc_type, balance) in enumerate([("savings", 15000.00), ("checking", 3500.00)]):
        # Check if account exists for this user
        cursor.execute(
            "SELECT id, account_number, balance FROM accounts WHERE user_id = ? AND account_type = ?",
            (user["id"], acc_type)
        )
        existing_acc = cursor.fetchone()

        if existing_acc:
            print(f"[OK] {acc_type} account exists for {user['email']}")
            created_accounts.append({
                "id": existing_acc[0],
                "user_id": user["id"],
                "number": existing_acc[1],
                "type": acc_type,
                "balance": existing_acc[2]
            })
        else:
            account_id = str(uuid.uuid4())
            account_number = f"000{i+1}{user['id'][:8]}"

            cursor.execute("""
                INSERT INTO accounts (id, user_id, account_number, account_type, balance, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                account_id,
                user["id"],
                account_number,
                acc_type,
                balance,
                "active"
            ))
            print(f"[OK] Created {acc_type} account for {user['email']}")
            created_accounts.append({
                "id": account_id,
                "user_id": user["id"],
                "number": account_number,
                "type": acc_type,
                "balance": balance
            })

conn.commit()

# Create sample transactions (only if no transactions exist)
cursor.execute("SELECT COUNT(*) FROM transactions")
tx_count = cursor.fetchone()[0]

if tx_count == 0:
    sample_descriptions = [
        "Direct Deposit - Payroll",
        "ATM Withdrawal",
        "Online Transfer",
        "Bill Payment - Electric",
        "Bill Payment - Internet",
        "Restaurant - Dining",
        "Shopping - Online",
        "Transfer from Savings",
        "Interest Credit",
        "Wire Transfer Received"
    ]

    for i, account in enumerate(created_accounts[:4]):
        num_transactions = 8

        for j in range(num_transactions):
            tx_type = "credit" if j % 2 == 0 else "debit"
            amount = round(50 + (j * 17) % 500, 2)
            description = sample_descriptions[j % len(sample_descriptions)]

            days_ago = j * 3
            tx_date = datetime.now() - timedelta(days=days_ago)

            cursor.execute("""
                INSERT INTO transactions (id, from_account_id, to_account_id, from_account_number, to_account_number, amount, currency, transaction_type, transfer_type, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                created_accounts[0]["id"] if tx_type == "debit" else created_accounts[1]["id"],
                account["id"] if tx_type == "credit" else created_accounts[1]["id"],
                created_accounts[0]["number"] if tx_type == "debit" else created_accounts[1]["number"],
                account["number"] if tx_type == "credit" else created_accounts[1]["number"],
                amount,
                "USD",
                tx_type,
                "internal" if tx_type == "credit" else "transfer",
                description,
                "completed",
                tx_date.strftime("%Y-%m-%d %H:%M:%S")
            ))

    conn.commit()
    print(f"[OK] Created {len(created_accounts[:4]) * 8} sample transactions")
else:
    print(f"[OK] Transactions already exist ({tx_count}), skipping...")

conn.close()

print("")
print("=" * 50)
print("DEMO DATA SETUP COMPLETE")
print("=" * 50)
print("")
print("LOGIN CREDENTIALS:")
print("-" * 50)
print("Admin:    admin@digitalbank.com  / Admin@123456")
print("Demo:     demo.user@demo.com     / Demo@123456")
print("John:     john.doe@demo.com      / Demo@123456")
print("Jane:     jane.smith@demo.com   / Demo@123456")
print("-" * 50)
