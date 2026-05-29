import sys
from pathlib import Path

from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.crud.user import create_user, get_user_by_email
from app.db.session import SessionLocal


def seed_admin(db: Session) -> None:
    existing_admin = get_user_by_email(db, settings.admin_email)
    if existing_admin:
        print(f"Admin already exists: {settings.admin_email}")
        return

    create_user(
        db,
        email=settings.admin_email,
        full_name=settings.admin_full_name,
        password=settings.admin_password,
        is_superuser=True,
    )
    print(f"Admin user seeded: {settings.admin_email}")


def main() -> None:
    with SessionLocal() as db:
        seed_admin(db)


if __name__ == "__main__":
    main()
