"""schemas/user_schema.py — Pydantic models for User entities."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    username:  str        = Field(..., min_length=3, max_length=50,
                                  pattern=r"^[a-zA-Z0-9_]+$")
    email:     EmailStr
    password:  str        = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)
    phone:     Optional[str] = Field(None, max_length=15)


class UserLogin(BaseModel):
    email:    EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    phone:     Optional[str] = Field(None, max_length=15)


class UserOut(BaseModel):
    id:         int
    username:   str
    email:      str
    full_name:  Optional[str]
    role:       str
    is_active:  bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserOut


class TokenPayload(BaseModel):
    sub:  str
    role: str
    exp:  int
