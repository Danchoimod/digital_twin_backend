from src.auth.schemas import UserCreate
from src.auth.utils import hash_password


class AuthService:
    @staticmethod
    async def get_user_by_email(db, email: str):
        user = await db["users"].find_one({"email": email})
        if user:
            user["id"] = str(user["_id"])
        return user

    @staticmethod
    async def create_user(db, user_in: UserCreate):
        hashed = hash_password(user_in.password)
        user_doc = {
            "email": user_in.email,
            "hashed_password": hashed,
            "is_active": True
        }
        result = await db["users"].insert_one(user_doc)
        user_doc["id"] = str(result.inserted_id)
        user_doc["_id"] = result.inserted_id
        return user_doc
