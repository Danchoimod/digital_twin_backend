from fastapi import APIRouter, Depends, UploadFile, File, status
from bson import ObjectId
from bson.errors import InvalidId
import io

from src.database import get_db
from src.auth.dependencies import get_current_user
from src.posts.schemas import PostCreate, PostResponse
from src.posts.service import PostService
from src.posts.exceptions import PostNotFoundException
from src.pagination import Page
from src.gcp.utils import upload_to_gcs

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_in: PostCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await PostService.create_post(db, post_in, current_user["id"])


@router.get("/", response_model=Page[PostResponse])
async def list_posts(page: int = 1, size: int = 10, db=Depends(get_db)):
    skip = (page - 1) * size
    items, total = await PostService.list_posts(db, skip=skip, limit=size)
    pages = (total + size - 1) // size if total > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str, db=Depends(get_db)):
    post = await PostService.get_post_by_id(db, post_id)
    if not post:
        raise PostNotFoundException(post_id)
    return post


@router.post("/{post_id}/upload-cover")
async def upload_cover_image(
    post_id: str,
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    post = await PostService.get_post_by_id(db, post_id)
    if not post:
        raise PostNotFoundException(post_id)
    
    # Read file content to memory stream
    contents = await file.read()
    stream = io.BytesIO(contents)
    
    # Upload to GCP Storage
    filename = f"posts/{post_id}/{file.filename}"
    public_url = upload_to_gcs(stream, filename)
    
    # Save back to database
    try:
        oid = ObjectId(post_id)
    except InvalidId:
        raise PostNotFoundException(post_id)

    await db["posts"].update_one({"_id": oid}, {"$set": {"image_url": public_url}})
    
    return {"message": "Cover image uploaded successfully", "url": public_url}
