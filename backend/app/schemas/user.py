from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class KYCSubmit(BaseModel):
    document_type: str = Field(..., description="national_id, passport, driver_license")
    document_number: str
    document_file: Optional[str] = None
    address: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    role: str
    kyc_level: int
    kyc_status: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Alias for UserCreate - used for registration
User = UserCreate


class UserWithKYC(UserResponse):
    kyc_document_type: Optional[str]
    kyc_document_number: Optional[str]
    kyc_submitted_at: Optional[datetime]
    kyc_reviewed_at: Optional[datetime]
    kyc_rejection_reason: Optional[str]
