import argparse
import getpass
import os
import sys

# Ensure app package is in Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.utils.activity_logger import publish_event


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


def main():
    parser = argparse.ArgumentParser(description="Create initial Admin account for RecruitAI.")
    parser.add_argument("--name", help="Admin full name")
    parser.add_argument("--email", help="Admin email address")
    parser.add_argument("--password", help="Admin password")
    args = parser.parse_args()

    name = args.name or os.getenv("ADMIN_NAME")
    email = args.email or os.getenv("ADMIN_EMAIL")
    password = args.password or os.getenv("ADMIN_PASSWORD")

    if not name:
        name = input("Enter Admin Full Name: ").strip()
    if not email:
        email = input("Enter Admin Email: ").strip()
    if not password:
        password = getpass.getpass("Enter Admin Password: ").strip()

    name = name.strip()
    email = email.strip().lower()

    if not name:
        print("Error: Name cannot be empty.", file=sys.stderr)
        sys.exit(1)

    if not email or "@" not in email:
        print("Error: Invalid email address.", file=sys.stderr)
        sys.exit(1)

    valid, err_msg = validate_password_strength(password)
    if not valid:
        print(f"Error: {err_msg}", file=sys.stderr)
        sys.exit(1)

    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            if existing_user.role == "admin":
                print(f"Admin account for '{email}' already exists. No action taken.")
                sys.exit(0)
            else:
                print(f"Error: Account '{email}' exists with role '{existing_user.role}'. Cannot convert to Admin.", file=sys.stderr)
                sys.exit(1)

        admin_user = User(
            full_name=name,
            email=email,
            hashed_password=get_password_hash(password),
            role="admin",
            is_active=True,
            must_change_password=False,
            token_version=1,
            created_by_admin_id=None,
        )
        db.add(admin_user)
        db.flush()

        publish_event(db, "admin_bootstrapped", None, admin_user.id, {
            "email": email,
            "full_name": name
        })
        db.commit()
        db.refresh(admin_user)

        print(f"Successfully created Admin account for '{email}'. (ID: {admin_user.id})")
        sys.exit(0)

    except Exception as e:
        db.rollback()
        print(f"Error creating Admin account: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
