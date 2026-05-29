from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str
    is_superuser: bool = False


class UserRead(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
