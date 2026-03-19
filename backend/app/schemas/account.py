from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime
from uuid import UUID


class AccountBase(BaseModel):
    account_type: str = Field(..., description="savings, checking, fixed_deposit")
    initial_deposit: Decimal = Field(..., ge=10, description="Minimum initial deposit")


class AccountCreate(AccountBase):
    pass


class AccountResponse(BaseModel):
    id: UUID
    account_number: str
    account_type: str
    balance: Decimal
    currency: str
    status: str
    created_at: datetime
    user_id: UUID

    class Config:
        from_attributes = True


# Alias
Account = AccountCreate


class AccountDetail(AccountResponse):
    user_email: Optional[str] = None
    user_name: Optional[str] = None