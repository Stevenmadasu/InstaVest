"""
InstaVest — Users Repository
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import User


def get_or_create_user(db: Session, *, email: str, name: str, firebase_uid: str = None, display_name: str = None) -> User:
    """Get existing user by email or create a new one."""
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        email=email,
        name=name,
        firebase_uid=firebase_uid,
        display_name=display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_firebase_uid(db: Session, firebase_uid: str) -> User | None:
    return db.query(User).filter(User.firebase_uid == firebase_uid).first()


def seed_default_user(db: Session) -> User:
    """Ensure a default development user exists (user_id=1)."""
    user = get_user_by_id(db, 1)
    if user:
        return user
    return get_or_create_user(db, email="dev@instavest.ai", name="Dev User", display_name="Dev")
