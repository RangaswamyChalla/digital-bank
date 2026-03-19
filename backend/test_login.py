#!/usr/bin/env python
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.auth import AuthService
from app.schemas.auth import LoginRequest
from app.database import AsyncSessionLocal, init_db

async def test_login():
    try:
        await init_db()

        async with AsyncSessionLocal() as db:
            request = LoginRequest(
                email="admin@digitalbank.com",
                password="AdminPass123"
            )
            token = await AuthService.login(db, request)
            print(f"Login successful!")
            print(f"Access token: {token.access_token[:50]}...")
            print(f"Refresh token: {token.refresh_token[:50]}...")
            return True
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_login())
    sys.exit(0 if success else 1)
