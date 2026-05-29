from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.property import Property


class PropertyError(ValueError):
    pass


def get_property(db: Session, property_id: int) -> Property | None:
    return db.get(Property, property_id)


def list_properties(db: Session) -> list[Property]:
    return db.query(Property).order_by(Property.created_at.desc()).all()


def create_property(
    db: Session,
    *,
    name: str,
    description: str,
    type: str,
) -> Property:
    property_obj = Property(
        name=name,
        description=description,
        type=type,
    )
    db.add(property_obj)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "UNIQUE constraint failed" in str(exc) or "unique constraint" in str(exc).lower():
            raise PropertyError(f"A property with name '{name}' already exists") from exc
        raise PropertyError(str(exc)) from exc

    db.refresh(property_obj)
    return property_obj


def update_property(db: Session, property_obj: Property, updates: dict[str, Any]) -> Property:
    for key, value in updates.items():
        if value is not None:
            setattr(property_obj, key, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "UNIQUE constraint failed" in str(exc) or "unique constraint" in str(exc).lower():
            raise PropertyError(f"A property with name '{updates.get('name')}' already exists") from exc
        raise PropertyError(str(exc)) from exc

    db.refresh(property_obj)
    return property_obj


def delete_property(db: Session, property_obj: Property) -> None:
    try:
        db.delete(property_obj)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise PropertyError(str(exc)) from exc
