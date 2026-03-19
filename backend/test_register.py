#!/usr/bin/env python
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.auth import AuthService
from app.schemas.auth import RegisterRequest
from app.database import AsyncSessionLocal, init_db

async def test_register():
    try:
        await init_db()

        async with AsyncSessionLocal() as db:
            request = RegisterRequest(
                email="admin@digitalbank.com",
                password="AdminPass123",
                full_name="Admin User",
                phone="+1234567890"
            )
            user = await AuthService.register(db, request)
            print(f"[SUCCESS] Registration successful! User ID: {user.id}")
            return True
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_register())
    sys.exit(0 if success else 1)
