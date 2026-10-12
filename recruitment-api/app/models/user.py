from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, text
from datetime import datetime, timezone
from app.core.database import Base
from app.core.time import utc_now

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    
    is_active = Column(Boolean, default=True, nullable=False, server_default=text("1"), index=True)
    must_change_password = Column(Boolean, default=False, nullable=False, server_default=text("0"))
    created_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    last_login_at = Column(DateTime, nullable=True)
    token_version = Column(Integer, default=1, nullable=False, server_default=text("1"))
