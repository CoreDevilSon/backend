from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PropertyTypeEnum(str, Enum):
    boolean = "boolean"
    text = "text"
    number = "number"


class PropertyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=1024)
    type: PropertyTypeEnum

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
        desc = value.strip()
        if not desc:
            raise ValueError("description cannot be empty")
        return desc


class PropertyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=1024)
    type: PropertyTypeEnum | None = None

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
        desc = value.strip()
        if not desc:
            raise ValueError("description cannot be empty")
        return desc


class PropertyRead(BaseModel):
    id: int
    name: str
    description: str
    type: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
