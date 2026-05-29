from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    parent_id: int | None = None
    main_picture_url: str | None = Field(default=None, max_length=1024)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("name cannot be empty")
        return name


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    parent_id: int | None = None
    main_picture_url: str | None = Field(default=None, max_length=1024)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        name = value.strip()
        if not name:
            raise ValueError("name cannot be empty")
        return name


class CategoryRead(BaseModel):
    id: int
    name: str
    parent_id: int | None
    main_picture_url: str | None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CategoryTreeNode(BaseModel):
    id: int
    name: str
    parent_id: int | None
    main_picture_url: str | None
    children: list["CategoryTreeNode"] = Field(default_factory=list)


class CategoryPropertyRead(BaseModel):
    id: int
    name: str
    description: str
    type: str
    is_direct: bool
    source_category_id: int
    source_category_name: str
    value: str | None = None


class CategoryProductRead(BaseModel):
    id: int
    name: str
    description: str
    photos: list[str] = Field(default_factory=list)
    is_direct: bool = False
    source_category_id: int
    source_category_name: str


class CategoryProductCatalogRead(BaseModel):
    id: int
    name: str
    description: str
    photos: list[str] = Field(default_factory=list)
    attached_category_id: int | None = None
    attached_category_name: str | None = None
    is_available_for_category: bool


class AttachPropertyRequest(BaseModel):
    value: str | None = None


CategoryTreeNode.model_rebuild()
