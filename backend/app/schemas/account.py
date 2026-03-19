from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class AccountBase(BaseModel):
    account_type: str = Field(..., description="savings, checking, fixed_deposit")
    initial_deposit: Decimal = Field(..., ge=10, description="Minimum initial deposit")


class AccountCreate(AccountBase):
    pass


class AccountResponse(BaseModel):
    id: str
    account_number: str
    account_type: str
    balance: Decimal
    currency: Optional[str] = "USD"
    status: str
    created_at: datetime
    user_id: str

    class Config:
        from_attributes = True


# Alias
Account = AccountCreate


class AccountDetail(AccountResponse):
    user_email: Optional[str] = None
    user_name: Optional[str] = None
