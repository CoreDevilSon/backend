from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.product import Product
from backend.app.models.product_photo import ProductPhoto


class ProductError(ValueError):
    pass


def _apply_product_photos(db: Session, product_id: int, photos: list[str]) -> None:
    db.query(ProductPhoto).filter(ProductPhoto.product_id == product_id).delete()
    for index, photo_url in enumerate(photos):
        db.add(
            ProductPhoto(
                product_id=product_id,
                photo_url=photo_url,
                position=index,
            )
        )


def _to_product_read(product: Product) -> dict[str, Any]:
    sorted_photos = sorted(product.photos, key=lambda photo: photo.position)
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "photos": [photo.photo_url for photo in sorted_photos],
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def list_products(db: Session) -> list[dict[str, Any]]:
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    return [_to_product_read(product) for product in products]


def create_product(
    db: Session,
    *,
    name: str,
    description: str,
    photos: list[str],
) -> dict[str, Any]:
    product = Product(name=name, description=description)
    db.add(product)

    try:
        db.flush()
        _apply_product_photos(db, product.id, photos)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "UNIQUE constraint failed" in str(exc) or "unique constraint" in str(exc).lower():
            raise ProductError(f"A product with name '{name}' already exists") from exc
        raise ProductError(str(exc)) from exc

    db.refresh(product)
    return _to_product_read(product)


def update_product(db: Session, product: Product, updates: dict[str, Any]) -> dict[str, Any]:
    photos: list[str] | None = updates.pop("photos", None)

    for key, value in updates.items():
        if value is not None:
            setattr(product, key, value)

    try:
        if photos is not None:
            _apply_product_photos(db, product.id, photos)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "UNIQUE constraint failed" in str(exc) or "unique constraint" in str(exc).lower():
            raise ProductError(f"A product with name '{updates.get('name')}' already exists") from exc
        raise ProductError(str(exc)) from exc

    db.refresh(product)
    return _to_product_read(product)


def delete_product(db: Session, product: Product) -> None:
    try:
        db.delete(product)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ProductError(str(exc)) from exc
