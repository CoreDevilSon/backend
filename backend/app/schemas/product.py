from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=4096)
    photos: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("name cannot be empty")
        return name

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        description = value.strip()
        if not description:
            raise ValueError("description cannot be empty")
        return description

    @field_validator("photos")
    @classmethod
    def validate_photos(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value and value.strip()]
        if len(cleaned) > 20:
            raise ValueError("maximum 20 photos are allowed")
        return cleaned


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=4096)
    photos: list[str] | None = Field(default=None, max_length=20)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        name = value.strip()
        if not name:
            raise ValueError("name cannot be empty")
        return name

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        description = value.strip()
        if not description:
            raise ValueError("description cannot be empty")
        return description

    @field_validator("photos")
    @classmethod
    def validate_photos(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        cleaned = [value.strip() for value in values if value and value.strip()]
        if len(cleaned) > 20:
            raise ValueError("maximum 20 photos are allowed")
        return cleaned


class ProductRead(BaseModel):
    id: int
    name: str
    description: str
    photos: list[str]
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
