"""Securely create an HR account from the backend command line."""

import argparse
from getpass import getpass

from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv

load_dotenv()

import app.models  # noqa: F401 - register metadata
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash, validate_password_strength
from app.models.user import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a RecruitAI HR account.")
    parser.add_argument("--name", required=True, help="HR user's full name")
    parser.add_argument("--email", required=True, help="HR user's email address")
    args = parser.parse_args()

    password = getpass("Password (minimum 10 characters with uppercase, lowercase, number, and symbol): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    valid, message = validate_password_strength(password)
    if not valid:
        raise SystemExit(message)
    if not args.name.strip():
        raise SystemExit("HR name is required.")

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        email = args.email.strip().lower()
        if db.query(User).filter(User.email == email).first():
            raise SystemExit("An account with that email already exists.")
        db.add(
            User(
                full_name=args.name.strip(),
                email=email,
                hashed_password=get_password_hash(password),
                role="hr",
                must_change_password=True,
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise SystemExit("The HR account could not be created because the email already exists.")
    print("HR account created successfully.")


if __name__ == "__main__":
    main()
