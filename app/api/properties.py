from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.app.crud.property import (
    PropertyError,
    create_property,
    delete_property,
    get_property,
    list_properties,
    update_property,
)
from backend.app.db.session import get_db
from backend.app.schemas.property import PropertyCreate, PropertyRead, PropertyUpdate

router = APIRouter(prefix="/api/v1/properties", tags=["properties"])


@router.get("", response_model=list[PropertyRead])
def list_properties_endpoint(db: Session = Depends(get_db)) -> list[PropertyRead]:
    return list_properties(db)


@router.post("", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property_endpoint(payload: PropertyCreate, db: Session = Depends(get_db)) -> PropertyRead:
    try:
        property_obj = create_property(
            db,
            name=payload.name,
            description=payload.description,
            type=payload.type.value,
        )
    except PropertyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return property_obj


@router.patch("/{property_id}", response_model=PropertyRead)
def update_property_endpoint(
    property_id: int,
    payload: PropertyUpdate,
    db: Session = Depends(get_db),
) -> PropertyRead:
    property_obj = get_property(db, property_id)
    if property_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    updates = payload.model_dump(exclude_unset=True)
    # Convert enum to string value
    if "type" in updates and updates["type"] is not None:
        updates["type"] = updates["type"].value

    try:
        property_obj = update_property(db, property_obj, updates)
    except PropertyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return property_obj


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property_endpoint(
    property_id: int,
    db: Session = Depends(get_db),
) -> Response:
    property_obj = get_property(db, property_id)
    if property_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    try:
        delete_property(db, property_obj)
    except PropertyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
