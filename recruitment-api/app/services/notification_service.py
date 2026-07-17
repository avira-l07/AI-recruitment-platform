from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "info",
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    db.add(notification)
    return notification


def notify_all_hr(
    db: Session,
    title: str,
    message: str,
    notification_type: str = "info",
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
) -> None:
    hr_users = db.query(User).filter(User.role == "hr").all()
    for user in hr_users:
        create_notification(
            db,
            user.id,
            title,
            message,
            notification_type,
            related_entity_type,
            related_entity_id,
        )
