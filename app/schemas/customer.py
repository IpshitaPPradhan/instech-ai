from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class CustomerOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
