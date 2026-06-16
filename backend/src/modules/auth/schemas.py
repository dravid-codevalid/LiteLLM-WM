# File: schemas.py. Description: Authentication data transfer objects. Consists of: Pydantic schemas for registration, login requests, and user responses.
import re
import uuid
from pydantic import BaseModel, Field, field_validator


EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=15)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=20)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format")
        return v.lower()


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    is_owner: bool

    model_config = {"from_attributes": True}
