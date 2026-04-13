import re
from pydantic import BaseModel, EmailStr, Field, field_validator


_PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]).{8,72}$"
)


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError(
                "Password must be 8-72 chars and contain uppercase, lowercase, "
                "digit, and special character."
            )
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_no_html(cls, v: str) -> str:
        if "<" in v or ">" in v:
            raise ValueError("Invalid characters in full_name")
        return v.strip()

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "email": "client@example.com",
                    "password": "Aa1!ClientPass99",
                    "full_name": "Client User",
                }
            ]
        }


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "email": "client@example.com",
                    "password": "Aa1!ClientPass99",
                }
            ]
        }


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=4096)

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "refresh_token": "paste_refresh_token_here",
                }
            ]
        }


class LogoutIn(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=20, max_length=4096)

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "refresh_token": "paste_refresh_token_here",
                }
            ]
        }


class MessageOut(BaseModel):
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Logged out",
            }
        }


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
                "token_type": "bearer",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
            }
        }


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    full_name: str
    is_active: bool

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "client@example.com",
                "role": "CLIENT",
                "full_name": "Client User",
                "is_active": True,
            }
        }
        from_attributes = True
