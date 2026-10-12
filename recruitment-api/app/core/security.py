import os
import secrets
from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

# FIXED: Securely pull from environment, with a fallback ONLY for local dev
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY in {"change_this_secret", "dev_fallback_secret_change_me_in_prod"}:
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise RuntimeError("Set a strong SECRET_KEY before starting in production.")
    SECRET_KEY = secrets.token_urlsafe(48)
elif os.getenv("APP_ENV", "development").lower() == "production" and len(SECRET_KEY) < 32:
    raise RuntimeError("Production SECRET_KEY must contain at least 32 characters.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    if len(plain_password.encode("utf-8")) > 72:
        return False
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"require": ["exp"]})
        return payload
    except InvalidTokenError:
        return None


def validate_password_strength(password: str) -> tuple[bool, str]:
    if not password or len(password) < 10:
        return False, "Password must be at least 10 characters long."
    if len(password) > 128 or len(password.encode("utf-8")) > 72:
        return False, "Password must not exceed 72 UTF-8 bytes."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    if not any(not c.isalnum() for c in password):
        return False, "Password must contain at least one special character."
    return True, ""
