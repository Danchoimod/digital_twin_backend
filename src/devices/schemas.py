from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class DeviceBase(BaseModel):
    name: str = Field(..., max_length=100, description="Friendly name of the device")
    type: str = Field("sensor", max_length=50, description="Device type, e.g., sensor, actuator")
    location: Optional[str] = Field(None, max_length=100, description="Deployment location")


class DeviceCreate(DeviceBase):
    device_id: str = Field(..., max_length=50, description="Unique string identifier for the device")


class DeviceResponse(DeviceBase):
    id: str
    device_id: str
    token: str = Field(..., description="Secret authentication token for the device")
    status: str = Field("active", description="Device status, e.g., active, inactive")
    creator_id: str
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceVerifyRequest(BaseModel):
    device_id: str = Field(..., max_length=50)
    token: str = Field(..., max_length=100)

