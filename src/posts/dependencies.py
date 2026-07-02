from fastapi import Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.posts.service import PostService
from src.posts.exceptions import PostNotFoundException


def get_post_for_creator(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = PostService.get_post_by_id(db, post_id)
    if not post:
        raise PostNotFoundException(post_id)
    return post
