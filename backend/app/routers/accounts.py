from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.database import get_db
from app.models.user import User
from app.schemas.account import AccountCreate, AccountResponse, AccountDetail
from app.schemas.transaction import TransactionResponse
from app.services.account import AccountService
from app.services.transaction import TransactionService
from app.routers.users import get_current_user

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new bank account"""
    return await AccountService.create_account(db, current_user.id, account_data)


@router.get("", response_model=List[AccountResponse])
async def get_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all accounts for current user"""
    return await AccountService.get_user_accounts(db, current_user.id)


@router.get("/balance")
async def get_total_balance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get total balance across all accounts"""
    balance = await AccountService.get_total_balance(db, current_user.id)
    return {"total_balance": float(balance), "currency": "USD"}


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get account details by ID"""
    from uuid import UUID
    account = await AccountService.get_account_by_id(
        db,
        UUID(account_id),
        current_user.id
    )
    return account


@router.get("/{account_id}/transactions", response_model=List[TransactionResponse])
async def get_account_transactions(
    account_id: str,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get transactions for a specific account"""
    from uuid import UUID
    return await TransactionService.get_account_transactions(
        db,
        UUID(account_id),
        limit,
        offset
    )