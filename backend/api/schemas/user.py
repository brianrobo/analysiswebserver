"""
User schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

from api.db.models import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.MEMBER
    team_id: Optional[int] = None


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    team_id: Optional[int] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserInDB(User):
    """Schema for user with hashed password (internal use)"""
    hashed_password: str
