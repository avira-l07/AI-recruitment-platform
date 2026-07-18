import math
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password
from app.core.dependencies import get_current_user, require_admin, require_password_changed
from app.models.user import User
from app.utils.activity_logger import publish_event
from app.api.auth import validate_password_strength

router = APIRouter(prefix="/admin", tags=["admin"])

ALLOWED_SORT_FIELDS = {
    "full_name",
    "email",
    "created_at",
    "updated_at",
    "last_login_at",
    "is_active",
}


class CreateHRAccountRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    temporary_password: str = Field(..., min_length=10, max_length=128)
    confirm_temporary_password: str

    model_config = ConfigDict(extra="forbid")


class UpdateHRStatusRequest(BaseModel):
    is_active: bool

    model_config = ConfigDict(extra="forbid")


class ResetHRPasswordRequest(BaseModel):
    temporary_password: str = Field(..., min_length=10, max_length=128)
    confirm_temporary_password: str

    model_config = ConfigDict(extra="forbid")


@router.post("/hr-accounts", status_code=status.HTTP_201_CREATED)
def create_hr_account(
    req: CreateHRAccountRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
    _: User = Depends(require_password_changed),
):
    full_name = req.full_name.strip()
    email = req.email.strip().lower()

    if not full_name:
        raise HTTPException(status_code=422, detail="Full name cannot be empty.")

    existing_user = db.query(User).filter(func.lower(User.email) == email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="This email is already registered.")

    if req.temporary_password != req.confirm_temporary_password:
        raise HTTPException(status_code=422, detail="Temporary password and confirmation do not match.")

    valid, err_msg = validate_password_strength(req.temporary_password)
    if not valid:
        raise HTTPException(status_code=422, detail=err_msg)

    hr_user = User(
        full_name=full_name,
        email=email,
        hashed_password=get_password_hash(req.temporary_password),
        role="hr",
        is_active=True,
        must_change_password=True,
        token_version=1,
        created_by_admin_id=current_admin.id,
    )
    db.add(hr_user)
    db.flush()

    publish_event(db, "hr_account_created", None, current_admin.id, {
        "actor_admin_id": current_admin.id,
        "target_hr_id": hr_user.id,
        "target_email": hr_user.email,
    })
    db.commit()
    db.refresh(hr_user)

    return {
        "message": "HR login account created successfully.",
        "hr": {
            "id": hr_user.id,
            "full_name": hr_user.full_name,
            "email": hr_user.email,
            "role": hr_user.role,
            "is_active": hr_user.is_active,
            "must_change_password": hr_user.must_change_password,
            "created_by_admin_id": hr_user.created_by_admin_id,
            "created_at": hr_user.created_at.isoformat() if hasattr(hr_user.created_at, "isoformat") else str(hr_user.created_at),
            "updated_at": hr_user.updated_at.isoformat() if hasattr(hr_user.updated_at, "isoformat") else str(hr_user.updated_at),
            "last_login_at": hr_user.last_login_at.isoformat() if hr_user.last_login_at else None,
        }
    }


@router.get("/hr-accounts")
def list_hr_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query("all"),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
    _: User = Depends(require_password_changed),
):
    if sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPException(status_code=422, detail=f"Invalid sort_by field. Allowed fields: {', '.join(sorted(ALLOWED_SORT_FIELDS))}")

    query = db.query(User).filter(User.role == "hr")

    if status == "active":
        query = query.filter(User.is_active == True)
    elif status == "inactive":
        query = query.filter(User.is_active == False)

    if search and search.strip():
        term = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(User.full_name).like(term),
                func.lower(User.email).like(term)
            )
        )

    sort_col = getattr(User, sort_by)
    if sort_order and sort_order.lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    items_models = query.offset((page - 1) * page_size).limit(page_size).all()

    items = [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "must_change_password": u.must_change_password,
            "created_by_admin_id": u.created_by_admin_id,
            "created_at": u.created_at.isoformat() if hasattr(u.created_at, "isoformat") else str(u.created_at),
            "updated_at": u.updated_at.isoformat() if hasattr(u.updated_at, "isoformat") else str(u.updated_at),
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in items_models
    ]

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }


@router.patch("/hr-accounts/{hr_id}/status")
def update_hr_status(
    hr_id: int,
    req: UpdateHRStatusRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
    _: User = Depends(require_password_changed),
):
    target = db.query(User).filter(User.id == hr_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="HR account not found.")

    if target.role != "hr":
        raise HTTPException(status_code=403, detail="Target user is not an HR account.")

    if target.is_active == req.is_active:
        return {
            "message": f"HR account is already {'active' if req.is_active else 'inactive'}.",
            "changed": False,
            "hr": {"id": target.id, "is_active": target.is_active}
        }

    target.is_active = req.is_active
    target.token_version = (target.token_version or 1) + 1
    target.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    event_name = "hr_account_activated" if req.is_active else "hr_account_deactivated"
    publish_event(db, event_name, None, current_admin.id, {
        "actor_admin_id": current_admin.id,
        "target_hr_id": target.id,
        "target_email": target.email,
        "is_active": req.is_active,
    })
    db.commit()
    db.refresh(target)

    return {
        "message": f"HR account {'activated' if req.is_active else 'deactivated'} successfully.",
        "changed": True,
        "hr": {"id": target.id, "is_active": target.is_active}
    }


@router.post("/hr-accounts/{hr_id}/reset-password")
def reset_hr_password(
    hr_id: int,
    req: ResetHRPasswordRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
    _: User = Depends(require_password_changed),
):
    target = db.query(User).filter(User.id == hr_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="HR account not found.")

    if target.role != "hr":
        raise HTTPException(status_code=403, detail="Target user is not an HR account.")

    if req.temporary_password != req.confirm_temporary_password:
        raise HTTPException(status_code=422, detail="Temporary password and confirmation do not match.")

    valid, err_msg = validate_password_strength(req.temporary_password)
    if not valid:
        raise HTTPException(status_code=422, detail=err_msg)

    if verify_password(req.temporary_password, target.hashed_password):
        raise HTTPException(status_code=400, detail="New password cannot be the same as the current password.")

    target.hashed_password = get_password_hash(req.temporary_password)
    target.must_change_password = True
    target.token_version = (target.token_version or 1) + 1
    target.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    publish_event(db, "hr_password_reset_by_admin", None, current_admin.id, {
        "actor_admin_id": current_admin.id,
        "target_hr_id": target.id,
        "target_email": target.email,
    })
    db.commit()
    db.refresh(target)

    return {
        "message": "HR password reset successfully. HR must change password upon next login.",
        "hr": {"id": target.id, "must_change_password": target.must_change_password}
    }
