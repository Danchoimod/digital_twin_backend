from pydantic import BaseModel
from typing import Optional


class GCSUploadResponse(BaseModel):
    filename: str
    bucket: str
    public_url: str
    size_bytes: int


class PubSubMessagePayload(BaseModel):
    event_type: str
    data: dict
    attributes: Optional[dict] = None
