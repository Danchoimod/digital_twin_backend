from fastapi import APIRouter, Depends, UploadFile, File, status
from bson import ObjectId
from bson.errors import InvalidId
import io

from src.database import get_db
from src.auth.dependencies import get_current_user
from src.devices.schemas import DeviceCreate, DeviceResponse, DeviceVerifyRequest
from src.devices.service import DeviceService
from src.devices.exceptions import DeviceNotFoundException
from src.pagination import Page
from src.gcp.utils import upload_to_gcs

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_in: DeviceCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await DeviceService.create_device(db, device_in, current_user["id"])


@router.get("/", response_model=Page[DeviceResponse])
async def list_devices(
    page: int = 1,
    size: int = 10,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    skip = (page - 1) * size
    items, total = await DeviceService.list_devices(db, creator_id=current_user["id"], skip=skip, limit=size)
    pages = (total + size - 1) // size if total > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get("/{id}", response_model=DeviceResponse)
async def get_device(id: str, db=Depends(get_db)):
    device = await DeviceService.get_device_by_id(db, id)
    if not device:
        raise DeviceNotFoundException(id)
    return device


@router.post("/{id}/upload-image")
async def upload_device_image(
    id: str,
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    device = await DeviceService.get_device_by_id(db, id)
    if not device:
        raise DeviceNotFoundException(id)
    
    # Read file content to memory stream
    contents = await file.read()
    stream = io.BytesIO(contents)
    
    # Upload to GCP Storage
    filename = f"devices/{id}/{file.filename}"
    public_url = upload_to_gcs(stream, filename)
    
    # Save back to database
    try:
        oid = ObjectId(id)
    except InvalidId:
        raise DeviceNotFoundException(id)

    await db["devices"].update_one({"_id": oid}, {"$set": {"image_url": public_url}})
    
    return {"message": "Device image uploaded successfully", "url": public_url}


@router.post("/verify")
async def verify_device(
    payload: DeviceVerifyRequest,
    db=Depends(get_db)
):
    """
    Endpoint for MQTT brokers / Plugins or Bridges to verify if a device is registered and authenticated.
    """
    is_valid = await DeviceService.verify_device(db, payload.device_id, payload.token)
    if not is_valid:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid Device ID or Token")
    return {"status": "verified"}

