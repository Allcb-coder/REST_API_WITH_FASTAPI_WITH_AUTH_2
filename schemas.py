from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

    @validator('password')
    def password_length(cls, v):
        # Warn but don't block - auth.py will handle truncation
        if len(v.encode('utf-8')) > 72:
            print(f"Warning: Password will be truncated from {len(v.encode('utf-8'))} to 72 bytes")
        return v

    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)


class UserResponse(UserBase):
    id: int
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


# Advertisement Schemas
class AdvertisementBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    price: float = Field(..., gt=0)


class AdvertisementCreate(AdvertisementBase):
    pass


class AdvertisementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    price: Optional[float] = Field(None, gt=0)


class AdvertisementResponse(AdvertisementBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Authentication Schemas
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"