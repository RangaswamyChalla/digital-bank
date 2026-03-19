#!/usr/bin/env python
from passlib.context import CryptContext

# Test argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

password = "AdminPass123"
print(f"Original password: {password}")

# Hash
hashed = pwd_context.hash(password)
print(f"Hashed password: {hashed[:50]}...")

# Verify correct password
result = pwd_context.verify(password, hashed)
print(f"Verify correct password: {result}")

# Verify wrong password
result_wrong = pwd_context.verify("WrongPassword", hashed)
print(f"Verify wrong password: {result_wrong}")
