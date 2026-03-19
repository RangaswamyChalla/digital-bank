from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID


class TransferRequest(BaseModel):
    from_account_id: UUID
    to_account_number: str = Field(..., min_length=10, max_length=10)
    amount: Decimal = Field(..., gt=0)
    transfer_type: str = Field(..., description="internal, external")
    reference: Optional[str] = None
    description: Optional[str] = None


class TransactionBase(BaseModel):
    amount: Decimal
    transaction_type: str
    transfer_type: str


class TransactionCreate(TransactionBase):
    from_account_id: Optional[UUID] = None
    to_account_id: Optional[UUID] = None
    from_account_number: str
    to_account_number: str
    reference: Optional[str] = None
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    id: UUID
    from_account_number: Optional[str]
    to_account_number: Optional[str]
    amount: Decimal
    currency: str
    transaction_type: str
    transfer_type: str
    reference: Optional[str]
    status: str
    description: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]
    failure_reason: Optional[str]

    class Config:
        from_attributes = True


# Alias for consistency with other schemas
Transaction = TransactionResponse


class TransactionWithAccounts(TransactionResponse):
    from_account_type: Optional[str] = None
    to_account_type: Optional[str] = None