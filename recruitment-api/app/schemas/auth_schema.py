from pydantic import BaseModel, EmailStr, Field, model_validator, ConfigDict
from typing import Optional


class RegisterRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    role: str

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


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    full_name: str
    role: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str

    model_config = ConfigDict(from_attributes=True)
