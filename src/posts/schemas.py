from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PostBase(BaseModel):
    title: str = Field(..., max_length=100)
    content: str = Field(..., max_length=5000)


class PostCreate(PostBase):
    image_url: Optional[str] = None


class PostResponse(PostBase):
    id: int
    image_url: Optional[str] = None
    creator_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
