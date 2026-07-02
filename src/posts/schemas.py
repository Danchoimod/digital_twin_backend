from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class PostBase(BaseModel):
    title: str = Field(..., max_length=100)
    content: str = Field(..., max_length=5000)


class PostCreate(PostBase):
    image_url: Optional[str] = None


class PostResponse(PostBase):
    id: str
    image_url: Optional[str] = None
    creator_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
