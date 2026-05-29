from enum import Enum
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.app.crud.category import (
    attach_product_to_category,
    attach_property_to_category,
    CategoryError,
    create_category,
    detach_product_from_category,
    detach_property_from_category,
    delete_category,
    get_category,
    list_category_product_catalog,
    list_category_products,
    list_category_properties,
    list_category_tree,
    set_category_property_value,
    update_category,
)
from backend.app.crud.product import get_product
from backend.app.crud.property import get_property
from backend.app.db.session import get_db
from backend.app.schemas.category import (
    AttachPropertyRequest,
    CategoryProductCatalogRead,
    CategoryProductRead,
    CategoryCreate,
    CategoryPropertyRead,
    CategoryRead,
    CategoryTreeNode,
    CategoryUpdate,
)

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


class DeleteMode(str, Enum):
    reject = "reject"
    cascade = "cascade"
    reparent = "reparent"


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category_endpoint(payload: CategoryCreate, db: Session = Depends(get_db)) -> CategoryRead:
    try:
        category = create_category(
            db,
            name=payload.name,
            parent_id=payload.parent_id,
            main_picture_url=payload.main_picture_url,
        )
    except CategoryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return category


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category_endpoint(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
) -> CategoryRead:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    updates = payload.model_dump(exclude_unset=True)

    try:
        category = update_category(db, category, updates)
    except CategoryError as exc:
        error_text = str(exc)
        status_code = status.HTTP_409_CONFLICT if "descendant" in error_text else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=error_text) from exc

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_endpoint(
    category_id: int,
    mode: DeleteMode = Query(default=DeleteMode.reject),
    db: Session = Depends(get_db),
) -> Response:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    try:
        delete_category(db, category, mode.value)
    except CategoryError as exc:
        status_code = status.HTTP_409_CONFLICT if "has children" in str(exc) else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/tree", response_model=list[CategoryTreeNode])
def list_category_tree_endpoint(
    root_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[CategoryTreeNode]:
    return list_category_tree(db, root_id=root_id)


@router.get("/{category_id}/properties", response_model=list[CategoryPropertyRead])
def list_category_properties_endpoint(
    category_id: int,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    return list_category_properties(db, category_id)


@router.post("/{category_id}/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def attach_property_to_category_endpoint(
    category_id: int,
    property_id: int,
    payload: AttachPropertyRequest = Body(default_factory=AttachPropertyRequest),
    db: Session = Depends(get_db),
) -> Response:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    property_obj = get_property(db, property_id)
    if property_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    try:
        attach_property_to_category(db, category_id, property_id, value=payload.value)
    except CategoryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{category_id}/properties/{property_id}/value", status_code=status.HTTP_204_NO_CONTENT)
def set_property_value_endpoint(
    category_id: int,
    property_id: int,
    payload: AttachPropertyRequest,
    db: Session = Depends(get_db),
) -> Response:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    property_obj = get_property(db, property_id)
    if property_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    set_category_property_value(db, category_id, property_id, payload.value)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{category_id}/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def detach_property_from_category_endpoint(
    category_id: int,
    property_id: int,
    db: Session = Depends(get_db),
) -> Response:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    property_obj = get_property(db, property_id)
    if property_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    try:
        detach_property_from_category(db, category_id, property_id)
    except CategoryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{category_id}/products", response_model=list[CategoryProductRead])
def list_category_products_endpoint(
    category_id: int,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    return list_category_products(db, category_id)


@router.get("/{category_id}/products/catalog", response_model=list[CategoryProductCatalogRead])
def list_category_product_catalog_endpoint(
    category_id: int,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    return list_category_product_catalog(db, category_id)


@router.post("/{category_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def attach_product_to_category_endpoint(
    category_id: int,
    product_id: int,
    db: Session = Depends(get_db),
) -> Response:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    product_obj = get_product(db, product_id)
    if product_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    try:
        attach_product_to_category(db, category_id, product_id)
    except CategoryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{category_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def detach_product_from_category_endpoint(
    category_id: int,
    product_id: int,
    db: Session = Depends(get_db),
) -> Response:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    product_obj = get_product(db, product_id)
    if product_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    try:
        detach_product_from_category(db, category_id, product_id)
    except CategoryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
