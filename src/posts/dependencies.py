from fastapi import Depends

from src.database import get_db
from src.auth.dependencies import get_current_user
from src.posts.service import PostService
from src.posts.exceptions import PostNotFoundException


async def get_post_for_creator(post_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    post = await PostService.get_post_by_id(db, post_id)
    if not post:
        raise PostNotFoundException(post_id)
    return post
