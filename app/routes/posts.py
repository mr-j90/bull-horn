import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.models import Post, PostCreate, PostStatus, PostUpdate
from app.queue import add_post, delete_post, get_post, load_posts, update_post
from app.scheduler import publish_post

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=list[Post])
async def list_posts(status: Optional[str] = None) -> list[Post]:
    posts = load_posts()
    if status:
        posts = [p for p in posts if p.status.value == status]
    return posts


@router.get("/{post_id}", response_model=Post)
async def get_single_post(post_id: str) -> Post:
    post = get_post(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")
    return post


@router.post("", response_model=Post, status_code=201)
async def create_post(body: PostCreate) -> Post:
    existing = get_post(body.id)
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Post {body.id} already exists")
    post = Post(**body.model_dump())
    return add_post(post)


@router.put("/{post_id}", response_model=Post)
async def update_existing_post(post_id: str, body: PostUpdate) -> Post:
    existing = get_post(post_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return existing
    return update_post(post_id, updates)


@router.delete("/{post_id}", status_code=204)
async def remove_post(post_id: str) -> None:
    if not delete_post(post_id):
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")


@router.post("/{post_id}/publish")
async def trigger_publish(post_id: str) -> dict:
    post = get_post(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")
    if post.status != PostStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Post {post_id} is not pending (status: {post.status.value})")
    result = await publish_post(post_id)
    return result


@router.post("/{post_id}/skip", response_model=Post)
async def skip_post(post_id: str) -> Post:
    post = get_post(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")
    return update_post(post_id, {"status": PostStatus.SKIPPED})
