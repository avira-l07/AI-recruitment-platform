from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.models.user import User
from app.models.candidate import Candidate
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    name: str 
    email: EmailStr
    password: str
    role: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register_user(req: UserCreate, db: Session = Depends(get_db)): 
    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed_pw = get_password_hash(req.password)
    
    try:
        new_user = User(
            email=req.email, 
            hashed_password=hashed_pw, 
            role=req.role, 
            full_name=req.name
        )
        db.add(new_user)
        db.flush() 

        if req.role == "candidate":
            new_candidate = Candidate(user_id=new_user.id)
            db.add(new_candidate)
        
        db.commit()
        db.refresh(new_user)
        
        return {"message": "User created successfully", "user_id": new_user.id}
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Database conflict: Email might already be registered."
        )
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login")
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"user_id": user.id, "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
        "name": user.full_name,
        "email": user.email,
    }