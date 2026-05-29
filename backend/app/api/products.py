from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.crud.product import (
    ProductError,
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
)
from backend.app.db.session import get_db
from backend.app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def list_products_endpoint(db: Session = Depends(get_db)) -> list[dict]:
    return list_products(db)


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product_endpoint(payload: ProductCreate, db: Session = Depends(get_db)) -> dict:
    try:
        product = create_product(
            db,
            name=payload.name,
            description=payload.description,
            photos=payload.photos,
        )
    except ProductError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return product


@router.patch("/{product_id}", response_model=ProductRead)
def update_product_endpoint(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
) -> dict:
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    updates = payload.model_dump(exclude_unset=True)

    try:
        product_data = update_product(db, product, updates)
    except ProductError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return product_data


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_endpoint(product_id: int, db: Session = Depends(get_db)) -> Response:
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    try:
        delete_product(db, product)
    except ProductError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
