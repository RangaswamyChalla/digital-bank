import uuid
import random
from decimal import Decimal
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountCreate, AccountResponse
from app.services.notification import NotificationService


class AccountService:
    @staticmethod
    def generate_account_number() -> str:
        """Generate a unique 10-digit account number"""
        return ''.join([str(random.randint(0, 9)) for _ in range(10)])

    @staticmethod
    async def create_account(db: AsyncSession, user_id: uuid.UUID, account_data: AccountCreate) -> Account:
        # Verify user exists and KYC is at least level 1
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.kyc_level < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KYC verification required before creating an account"
            )

        # Generate unique account number
        account_number = AccountService.generate_account_number()
        while True:
            result = await db.execute(select(Account).where(Account.account_number == account_number))
            if not result.scalar_one_or_none():
                break
            account_number = AccountService.generate_account_number()

        # Create account
        account = Account(
            user_id=user_id,
            account_number=account_number,
            account_type=account_data.account_type,
            balance=account_data.initial_deposit,
            currency="USD",
            status="active"
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)

        # Send notification
        await NotificationService.create_notification(
            db,
            user_id,
            "account_created",
            "Account Created",
            f"Your {account_data.account_type} account has been created. Account number: {account_number}"
        )

        return account

    @staticmethod
    async def get_user_accounts(db: AsyncSession, user_id: uuid.UUID) -> List[Account]:
        result = await db.execute(
            select(Account).where(Account.user_id == user_id)
        )
        return result.scalars().all()

    @staticmethod
    async def get_account_by_id(db: AsyncSession, account_id: uuid.UUID, user_id: uuid.UUID = None) -> Account:
        query = select(Account).where(Account.id == account_id)
        if user_id:
            query = query.where(Account.user_id == user_id)

        result = await db.execute(query)
        account = result.scalar_one_or_none()

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        return account

    @staticmethod
    async def get_account_by_number(db: AsyncSession, account_number: str) -> Account:
        result = await db.execute(select(Account).where(Account.account_number == account_number))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_total_balance(db: AsyncSession, user_id: uuid.UUID) -> Decimal:
        result = await db.execute(
            select(Account).where(Account.user_id == user_id, Account.status == "active")
        )
        accounts = result.scalars().all()
        return sum(account.balance for account in accounts)