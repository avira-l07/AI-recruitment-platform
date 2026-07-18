import logging
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.core.database import get_db
from app.core.rate_limit import rate_limiter
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.models.candidate import Candidate
from app.schemas.auth_schema import RegisterRequest, LoginRequest, ChangePasswordRequest
from app.core.dependencies import get_current_user
from app.utils.activity_logger import publish_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def validate_password_strength(password: str) -> tuple[bool, str]:
    if not password or len(password) < 10:
        return False, "Password must be at least 10 characters long."
    if len(password) > 128:
        return False, "Password must not exceed 128 characters."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    if not any(not c.isalnum() for c in password):
        return False, "Password must contain at least one special character."
    return True, ""


@router.post("/register", dependencies=[Depends(rate_limiter.dependency(5, 3600, "register"))])
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    role = "candidate"
    email = req.email.strip().lower()

    existing_user = db.query(User).filter(func.lower(User.email) == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered.")

    full_name = (req.full_name or req.name or "").strip()
    if not full_name:
        raise HTTPException(status_code=422, detail="Name field is required.")

    valid, err_msg = validate_password_strength(req.password)
    if not valid:
        raise HTTPException(status_code=422, detail=err_msg)

    try:
        new_user = User(
            email=email,
            hashed_password=get_password_hash(req.password),
            role=role,
            full_name=full_name,
            is_active=True,
            must_change_password=False,
            token_version=1,
        )
        db.add(new_user)
        db.flush()

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
    user = db.query(User).filter(func.lower(User.email) == email).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.is_active:
        publish_event(db, "login_blocked_inactive", None, user.id, {"email": user.email})
        db.commit()
        raise HTTPException(status_code=403, detail="Account is inactive.")

    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    publish_event(db, "login_succeeded", None, user.id, {"email": user.email})
    db.commit()
    db.refresh(user)

    token = create_access_token({
        "sub": str(user.id),
        "user_id": user.id,
        "role": user.role,
        "token_version": user.token_version
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "id": user.id,
        "full_name": user.full_name,
        "name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "must_change_password": user.must_change_password,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "must_change_password": current_user.must_change_password,
        "created_at": current_user.created_at.isoformat() if hasattr(current_user.created_at, "isoformat") else str(current_user.created_at),
        "updated_at": current_user.updated_at.isoformat() if hasattr(current_user.updated_at, "isoformat") else str(current_user.updated_at),
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
    }


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password.")

    if req.new_password != req.confirm_new_password:
        raise HTTPException(status_code=422, detail="New password and confirmation do not match.")

    valid, err_msg = validate_password_strength(req.new_password)
    if not valid:
        raise HTTPException(status_code=422, detail=err_msg)

    if verify_password(req.new_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="New password cannot be the same as the current password.")

    current_user.hashed_password = get_password_hash(req.new_password)
    current_user.must_change_password = False
    current_user.token_version = (current_user.token_version or 1) + 1
    current_user.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    publish_event(db, "password_changed", None, current_user.id, {
        "user_id": current_user.id,
        "email": current_user.email
    })
    db.commit()
    db.refresh(current_user)

    token = create_access_token({
        "sub": str(current_user.id),
        "user_id": current_user.id,
        "role": current_user.role,
        "token_version": current_user.token_version
    })

    return {
        "message": "Password changed successfully.",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "must_change_password": current_user.must_change_password,
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        }
    }


@router.get("/verify")
def verify_token_status(current_user: User = Depends(get_current_user)):
    return {"status": "valid", "user_id": current_user.id, "role": current_user.role}
