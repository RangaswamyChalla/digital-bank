import uuid
from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, case
from fastapi import HTTPException, status

from app.models.transaction import Transaction
from app.models.account import Account
from app.models.user import User
from app.schemas.transaction import TransferRequest, TransactionResponse
from app.services.notification import NotificationService


class TransactionService:
    DAILY_LIMIT = Decimal("50000")
    SUSPICIOUS_AMOUNT = Decimal("10000")

    @staticmethod
    async def create_transfer(
        db: AsyncSession,
        user_id: str,
        transfer_data: TransferRequest
    ) -> Transaction:
        # Get source account with row-level lock to prevent double-spending
        result = await db.execute(
            select(Account).where(
                Account.id == transfer_data.from_account_id,
                Account.user_id == user_id
            ).with_for_update()
        )
        from_account = result.scalar_one_or_none()

        if not from_account:
            raise HTTPException(status_code=404, detail="Source account not found")

        if from_account.status != "active":
            raise HTTPException(status_code=400, detail="Source account is not active")

        # Check balance
        if from_account.balance < transfer_data.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        # Get destination account with lock (if internal transfer)
        to_account = None
        if transfer_data.transfer_type == "internal":
            result = await db.execute(
                select(Account).where(
                    Account.account_number == transfer_data.to_account_number
                ).with_for_update()
            )
            to_account = result.scalar_one_or_none()
            if not to_account:
                raise HTTPException(status_code=404, detail="Destination account not found")

        # Check daily limit using atomic SUM aggregate (within locked transaction)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await db.execute(
            select(
                func.coalesce(func.sum(
                    case(
                        (Transaction.status == "completed", Transaction.amount),
                        else_=0
                    )
                ), 0)
            ).where(
                Transaction.from_account_id == from_account.id,
                Transaction.created_at >= today_start
            )
        )
        today_total = result.scalar() or Decimal("0")

        if today_total + transfer_data.amount > TransactionService.DAILY_LIMIT:
            raise HTTPException(
                status_code=400,
                detail=f"Daily transfer limit of ${TransactionService.DAILY_LIMIT} exceeded"
            )

        # Prevent same account transfer
        if transfer_data.transfer_type == "internal":
            if from_account.id == to_account.id:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot transfer to the same account"
                )

        # Check for suspicious amount
        is_suspicious = transfer_data.amount >= TransactionService.SUSPICIOUS_AMOUNT

        # Create transaction record
        transaction = Transaction(
            from_account_id=from_account.id,
            to_account_id=to_account.id if to_account else None,
            from_account_number=from_account.account_number,
            to_account_number=transfer_data.to_account_number,
            amount=transfer_data.amount,
            transaction_type="debit",
            transfer_type=transfer_data.transfer_type,
            reference=transfer_data.reference,
            description=transfer_data.description,
            status="pending"
        )
        db.add(transaction)

        try:
            # Deduct from source (within the locked transaction)
            from_account.balance -= transfer_data.amount

            # Credit to destination (if internal)
            if to_account:
                to_account.balance += transfer_data.amount

            # Mark transaction as completed
            transaction.status = "completed"
            transaction.completed_at = datetime.utcnow()

            await db.commit()
            await db.refresh(transaction)

            # Send notifications
            # Notification to sender
            await NotificationService.create_notification(
                db,
                user_id,
                "transfer_sent",
                "Transfer Sent",
                f"You sent ${transfer_data.amount} to account {transfer_data.to_account_number}"
            )

            # Notification to recipient (if internal)
            if to_account:
                await NotificationService.create_notification(
                    db,
                    to_account.user_id,
                    "transfer_received",
                    "Transfer Received",
                    f"You received ${transfer_data.amount} from account {from_account.account_number}"
                )

            return transaction

        except Exception as e:
            await db.rollback()
            transaction.status = "failed"
            transaction.failed_at = datetime.utcnow()
            transaction.failure_reason = str(e)
            try:
                await db.commit()
            except:
                await db.rollback()
            raise HTTPException(status_code=500, detail="Transfer failed")

    @staticmethod
    async def get_user_transactions(
        db: AsyncSession,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Transaction]:
        # Get user's account IDs
        result = await db.execute(
            select(Account.account_number).where(Account.user_id == user_id)
        )
        account_numbers = [row[0] for row in result.all()]

        if not account_numbers:
            return []

        # Get transactions involving user's accounts
        result = await db.execute(
            select(Transaction).where(
                or_(
                    Transaction.from_account_number.in_(account_numbers),
                    Transaction.to_account_number.in_(account_numbers)
                )
            ).order_by(Transaction.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def get_account_transactions(
        db: AsyncSession,
        account_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Transaction]:
        result = await db.execute(select(Transaction).where(Transaction.id == account_id))
        account = result.scalar_one_or_none()

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        result = await db.execute(
            select(Transaction).where(
                or_(
                    Transaction.from_account_number == account.account_number,
                    Transaction.to_account_number == account.account_number
                )
            ).order_by(Transaction.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def get_transaction_by_id(
        db: AsyncSession,
        transaction_id: str,
        user_id: str = None
    ) -> Transaction:
        query = select(Transaction).where(Transaction.id == transaction_id)
        result = await db.execute(query)
        transaction = result.scalar_one_or_none()

        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Verify user has access to this transaction
        if user_id:
            # Get user's account numbers
            result = await db.execute(
                select(Account.account_number).where(Account.user_id == user_id)
            )
            user_account_numbers = [row[0] for row in result.all()]

            # Check if transaction involves user's accounts
            if transaction.from_account_number not in user_account_numbers and transaction.to_account_number not in user_account_numbers:
                raise HTTPException(status_code=403, detail="Access denied")

        return transaction
