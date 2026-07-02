from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
import io

from src.database import get_db
from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.posts.schemas import PostCreate, PostResponse
from src.posts.service import PostService
from src.posts.exceptions import PostNotFoundException
from src.pagination import Page
from src.gcp.utils import upload_to_gcs

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return PostService.create_post(db, post_in, current_user.id)


@router.get("/", response_model=Page[PostResponse])
def list_posts(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    skip = (page - 1) * size
    items, total = PostService.list_posts(db, skip=skip, limit=size)
    pages = (total + size - 1) // size if total > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = PostService.get_post_by_id(db, post_id)
    if not post:
        raise PostNotFoundException(post_id)
    return post


@router.post("/{post_id}/upload-cover")
def upload_cover_image(
    post_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = PostService.get_post_by_id(db, post_id)
    if not post:
        raise PostNotFoundException(post_id)
    
    # Read file content to memory stream
    contents = file.file.read()
    stream = io.BytesIO(contents)
    
    # Upload to GCP Storage
    filename = f"posts/{post_id}/{file.filename}"
    public_url = upload_to_gcs(stream, filename)
    
    # Save back to database
    post.image_url = public_url
    db.commit()
    db.refresh(post)
    
    return {"message": "Cover image uploaded successfully", "url": public_url}
