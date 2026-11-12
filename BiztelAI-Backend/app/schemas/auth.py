"""Authentication and authorization schemas."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserRegisterRequest(StrictSchema):
    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters")
    full_name: str = Field(min_length=2, max_length=120)
    department: Optional[str] = Field(default=None, max_length=100)
    role: Optional[str] = Field(default="operator", description="admin, supervisor, operator, or auditor")


class UserLoginRequest(StrictSchema):
    email: EmailStr
    password: str


class TokenRefreshRequest(StrictSchema):
    refresh_token: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    department: Optional[str] = None
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in_minutes: int
    user: UserResponse

