from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_user(
    db: Session,
    *,
    email: str,
    full_name: str,
    password: str,
    is_superuser: bool = False,
) -> User:
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        is_active=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
