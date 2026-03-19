#!/usr/bin/env python3
"""Create an admin user in the database"""
import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.user import User
from app.services.auth import AuthService
from app.config import settings


async def create_admin():
    # Create engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
    )
    
    # Create session
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with AsyncSessionLocal() as session:
        # Admin credentials
        admin_email = "admin@digitalbank.com"
        admin_password = "Admin@123456"
        admin_name = "System Administrator"
        admin_phone = "+1-800-000-0000"
        
        # Check if admin already exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == admin_email))
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print(f"[OK] Admin user already exists: {admin_email}")
            print(f"[INFO] Email: {admin_email}")
            print(f"[INFO] Password: Check your setup notes")
        else:
            # Create admin user
            admin_user = User(
                id=uuid.uuid4(),
                email=admin_email,
                password_hash=AuthService.get_password_hash(admin_password),
                full_name=admin_name,
                phone=admin_phone,
                role="admin",
                kyc_level=3,
                kyc_status="approved",
                is_active=True
            )

            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

            print("[OK] Admin user created successfully!")
            print(f"\n[ADMIN CREDENTIALS]")
            print(f"  Email:    {admin_email}")
            print(f"  Password: {admin_password}")
            print(f"  Role:     admin")
            print(f"  KYC:      Level 3 (Approved)")


if __name__ == "__main__":
    asyncio.run(create_admin())
