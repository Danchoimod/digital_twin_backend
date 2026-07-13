import secrets
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId

from src.devices.schemas import DeviceCreate
from src.devices.exceptions import DeviceAlreadyExistsException
from src.gcp.utils import publish_pubsub_message


class DeviceService:
    @staticmethod
    async def get_device_by_id(db, id: str):
        try:
            oid = ObjectId(id)
        except InvalidId:
            return None
        
        device = await db["devices"].find_one({"_id": oid})
        if device:
            device["id"] = str(device["_id"])
        return device

    @staticmethod
    async def get_device_by_device_id(db, device_id: str):
        device = await db["devices"].find_one({"device_id": device_id})
        if device:
            device["id"] = str(device["_id"])
        return device

    @staticmethod
    async def list_devices(db, creator_id: str, skip: int = 0, limit: int = 10):
        query = {"creator_id": creator_id}
        total = await db["devices"].count_documents(query)
        cursor = db["devices"].find(query).skip(skip).limit(limit)
        items = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            items.append(doc)
        return items, total

    @staticmethod
    async def create_device(db, device_in: DeviceCreate, creator_id: str):
        # Check if device_id is already taken
        existing = await db["devices"].find_one({"device_id": device_in.device_id})
        if existing:
            raise DeviceAlreadyExistsException(device_in.device_id)

        now = datetime.now(timezone.utc)
        # Generate a unique secure token for the device
        token = f"dev_tok_{secrets.token_hex(16)}"
        
        device_doc = {
            "device_id": device_in.device_id,
            "name": device_in.name,
            "type": device_in.type,
            "location": device_in.location,
            "metrics_metadata": device_in.metrics_metadata or {},
            "token": token,
            "status": "active",
            "creator_id": creator_id,
            "image_url": None,
            "created_at": now,
            "updated_at": now
        }
        
        result = await db["devices"].insert_one(device_doc)
        device_doc["id"] = str(result.inserted_id)
        device_doc["_id"] = result.inserted_id

        # Publish integration event to GCP Pub/Sub
        try:
            publish_pubsub_message(
                payload={
                    "event_type": "device_created",
                    "device_id": device_doc["device_id"],
                    "name": device_doc["name"],
                    "type": device_doc["type"],
                    "creator_id": creator_id,
                    "timestamp": now.timestamp()
                },
                attributes={"action": "register"}
            )
        except Exception:
            # Let creation succeed even if GCP Pub/Sub publishing fails
            pass

        return device_doc

    @staticmethod
    async def verify_device(db, device_id: str, token: str) -> bool:
        device = await db["devices"].find_one({"device_id": device_id})
        if not device:
            return False
        return device.get("token") == token

    @staticmethod
    async def update_device_metadata(db, id: str, metadata: dict):
        try:
            oid = ObjectId(id)
        except InvalidId:
            return None
        now = datetime.now(timezone.utc)
        await db["devices"].update_one(
            {"_id": oid},
            {"$set": {"metrics_metadata": metadata, "updated_at": now}}
        )
        return await DeviceService.get_device_by_id(db, id)

