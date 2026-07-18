from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator, ConfigDict
from typing import Optional


class RegisterRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=10, max_length=128)
    role: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip().lower() != "candidate":
            raise ValueError("Public registration is restricted to candidate role only.")
        return v

    @model_validator(mode="before")
    @classmethod
    def check_name_fields(cls, data: any) -> any:
        if isinstance(data, dict):
            if "name" in data and "full_name" not in data:
                data["full_name"] = data["name"]
            elif "full_name" in data and "name" not in data:
                data["name"] = data["full_name"]
            if not data.get("full_name"):
                raise ValueError("Name field is required.")
        return data


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=10, max_length=128)
    confirm_new_password: str

    model_config = ConfigDict(extra="forbid")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    must_change_password: bool
    last_login_at: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    must_change_password: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_login_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
