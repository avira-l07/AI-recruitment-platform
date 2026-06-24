from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str

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

    class Config:
        from_attributes = True