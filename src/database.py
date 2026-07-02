from motor.motor_asyncio import AsyncIOMotorClient
from src.config import settings

# Create database client
client = AsyncIOMotorClient(settings.MONGODB_URL)
db = client[settings.MONGODB_DB_NAME]


async def get_db():
    """
    Database dependency yielding the MongoDB database instance.
    """
    yield db
