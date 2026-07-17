import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.rate_limit import rate_limiter
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.models.candidate import Candidate
from app.schemas.auth_schema import RegisterRequest, LoginRequest
from app.core.dependencies import get_current_user
from app.utils.activity_logger import publish_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", dependencies=[Depends(rate_limiter.dependency(5, 3600, "register"))])
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    role = req.role.strip().lower()
    if role not in {"candidate", "hr"}:
        raise HTTPException(status_code=422, detail="Role must be either candidate or hr.")

    if role == "hr" and os.getenv("ALLOW_PUBLIC_HR_REGISTRATION", "false").lower() != "true":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public HR registration is disabled. Ask an administrator to create the HR account."
        )

    email = req.email.strip().lower()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered.")

    try:
        new_user = User(
            email=email,
            hashed_password=get_password_hash(req.password),
            role=role,
            full_name=req.full_name.strip(),
        )
        db.add(new_user)
        db.flush()

        if role == "candidate":
            candidate = Candidate(
                user_id=new_user.id,
                full_name=new_user.full_name,
                email=new_user.email
            )
            db.add(candidate)
            db.flush()
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
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again later.")


@router.post("/login", dependencies=[Depends(rate_limiter.dependency(5, 300, "login"))])
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
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


@router.get("/verify")
def verify_token_status(current_user = Depends(get_current_user)):
    return {"status": "valid", "user_id": current_user.id, "role": current_user.role}
