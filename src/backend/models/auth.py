# auth_models.py
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class Roles(str, Enum):
    admin = "admin"
    user = "user"


class UserIn(BaseModel):
    pseudo: str = Field(min_length=1, max_length=255, examples=["Test_user"])
    password: str = Field(min_length=1, max_length=255, exemples=["Pass123"])
    role: Roles = Roles.user


class UserPatch(BaseModel):
    pseudo: Optional[str] = Field(default=None, min_length=1, max_length=255)
    password: Optional[str] = Field(default=None, min_length=1, max_length=255)
    role: Optional[Roles] = None


class UserOut(BaseModel):
    id: int
    pseudo: str
    role: Roles


class LoginIn(BaseModel):
    pseudo: str = Field(min_length=1, max_length=255, examples=["Test_user"])
    password: str = Field(min_length=1, max_length=255, exemples=["Pass123"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserOut]
