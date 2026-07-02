from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId

from src.posts.schemas import PostCreate
from src.gcp.utils import publish_pubsub_message


class PostService:
    @staticmethod
    async def get_post_by_id(db, post_id: str):
        try:
            oid = ObjectId(post_id)
        except InvalidId:
            return None
        
        post = await db["posts"].find_one({"_id": oid})
        if post:
            post["id"] = str(post["_id"])
        return post

    @staticmethod
    async def list_posts(db, skip: int = 0, limit: int = 10):
        total = await db["posts"].count_documents({})
        cursor = db["posts"].find({}).skip(skip).limit(limit)
        items = []
        async for doc in cursor:
            doc["id"] = str(doc["_id"])
            items.append(doc)
        return items, total

    @staticmethod
    async def create_post(db, post_in: PostCreate, creator_id: str):
        now = datetime.now(timezone.utc)
        post_doc = {
            "title": post_in.title,
            "content": post_in.content,
            "image_url": post_in.image_url,
            "creator_id": creator_id,
            "created_at": now,
            "updated_at": now
        }
        result = await db["posts"].insert_one(post_doc)
        post_doc["id"] = str(result.inserted_id)
        post_doc["_id"] = result.inserted_id

        # Publish integration event to GCP Pub/Sub
        try:
            publish_pubsub_message(
                payload={
                    "event_type": "post_created",
                    "post_id": post_doc["id"],
                    "title": post_doc["title"],
                    "creator_id": creator_id
                },
                attributes={"action": "create"}
            )
        except Exception:
            pass

        return post_doc
