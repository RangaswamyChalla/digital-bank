from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.transaction import TransferRequest, TransactionResponse
from app.services.transaction import TransactionService
from app.routers.users import get_current_user

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    transfer_data: TransferRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transfer money to another account"""
    return await TransactionService.create_transfer(db, current_user.id, transfer_data)


@router.get("", response_model=List[TransactionResponse])
async def get_transfers(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get transfer history for current user"""
    return await TransactionService.get_user_transactions(db, current_user.id, limit, offset)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transfer(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get transfer details by ID"""
    from uuid import UUID
    return await TransactionService.get_transaction_by_id(db, UUID(transaction_id), current_user.id)