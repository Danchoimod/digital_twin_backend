from sqlalchemy.orm import Session
from src.posts.models import Post
from src.posts.schemas import PostCreate
from src.gcp.utils import publish_pubsub_message


class PostService:
    @staticmethod
    def get_post_by_id(db: Session, post_id: int):
        return db.query(Post).filter(Post.id == post_id).first()

    @staticmethod
    def list_posts(db: Session, skip: int = 0, limit: int = 10):
        total = db.query(Post).count()
        items = db.query(Post).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def create_post(db: Session, post_in: PostCreate, creator_id: int):
        db_post = Post(
            title=post_in.title,
            content=post_in.content,
            image_url=post_in.image_url,
            creator_id=creator_id,
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)

        # Publish integration event to GCP Pub/Sub
        try:
            publish_pubsub_message(
                payload={
                    "event_type": "post_created",
                    "post_id": db_post.id,
                    "title": db_post.title,
                    "creator_id": creator_id
                },
                attributes={"action": "create"}
            )
        except Exception:
            # We catch exceptions so that DB transaction success isn't aborted by mock/missing PubSub config
            pass

        return db_post
