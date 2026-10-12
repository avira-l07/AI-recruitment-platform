from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_password_changed
from app.models.application import Application
from app.models.candidate import Candidate
from app.services.blind_screening import is_blind_mode_requested, sanitize_list_or_text
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _serialize_notification(item, db, user, request):
    result = {key: getattr(item, key) for key in (
        "id", "title", "message", "type", "related_entity_type", "related_entity_id", "is_read", "created_at", "read_at"
    )}
    if user.role == "hr" and is_blind_mode_requested(request, None, user):
        candidate_id = item.related_entity_id if item.related_entity_type == "candidate" else None
        if item.related_entity_type == "application":
            application = db.get(Application, item.related_entity_id)
            candidate_id = application.candidate_id if application else None
        candidate = db.get(Candidate, candidate_id) if candidate_id else None
        if candidate:
            result = sanitize_list_or_text(result, candidate_name=candidate.full_name, candidate_id=candidate.id, email=candidate.email, phone=candidate.phone)
    return result


@router.get("")
def get_notifications(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    total = query.count()
    items = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [_serialize_notification(item, db, current_user, request) for item in items],
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": ceil(total / page_size) if total else 0,
        "unread_count": db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        ).count(),
    }


@router.put("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = utc_now()
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    ).all()
    for notification in notifications:
        notification.is_read = True
        notification.read_at = now
    db.commit()
    return {"message": "All notifications marked as read.", "updated": len(notifications)}


@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notification.is_read = True
    notification.read_at = utc_now()
    db.commit()
    return {"message": "Notification marked as read."}
