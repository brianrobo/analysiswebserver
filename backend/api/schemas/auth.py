"""
Authentication schemas
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserLogin(BaseModel):
    """Schema for user login request"""
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserRegister(BaseModel):
    """Schema for user registration request"""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    team_id: Optional[int] = None


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded JWT token data"""
    email: Optional[str] = None
