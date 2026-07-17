from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_db
from app.models.user import User
from app.models.candidate import Candidate
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register_user(req: UserCreate, db: Session = Depends(get_db)):
    role = req.role.strip().lower()
    if role not in {"candidate", "hr"}:
        raise HTTPException(status_code=422, detail="Role must be either candidate or hr.")

    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    try:
        new_user = User(
            email=req.email,
            hashed_password=get_password_hash(req.password),
            role=role,
            full_name=req.name.strip(),
        )
        db.add(new_user)
        db.flush()

        if role == "candidate":
            candidate = Candidate(user_id=new_user.id, full_name=new_user.full_name, email=new_user.email)
            db.add(candidate)
            db.flush()
            from app.utils.activity_logger import publish_event
            publish_event(db, "candidate_registered", candidate.id, new_user.id, {
                "email": new_user.email,
                "full_name": new_user.full_name
            })

        db.commit()
        db.refresh(new_user)
        return {"message": "User created successfully", "user_id": new_user.id, "role": new_user.role}

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Database conflict: Email might already be registered.")
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
        "id": user.id,
        "role": user.role,
        "name": user.full_name,
        "fullName": user.full_name,
        "email": user.email,
    }


from app.api.dependencies import get_current_user

@router.get("/verify")
def verify_token_status(current_user = Depends(get_current_user)):
    return {"status": "valid", "user_id": current_user.id, "role": current_user.role}
