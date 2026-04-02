import json
import logging
from pathlib import Path

from filelock import FileLock

from app.config import settings
from app.models import Post

logger = logging.getLogger(__name__)

_lock = FileLock(f"{settings.posts_file}.lock")


def _posts_path() -> Path:
    return Path(settings.posts_file)


def load_posts() -> list[Post]:
    path = _posts_path()
    if not path.exists():
        return []
    with _lock:
        data = json.loads(path.read_text())
    return [Post(**item) for item in data]


def save_posts(posts: list[Post]) -> None:
    path = _posts_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        path.write_text(json.dumps([p.model_dump(mode="json") for p in posts], indent=2))


def get_post(post_id: str) -> Post | None:
    posts = load_posts()
    for post in posts:
        if post.id == post_id:
            return post
    return None


def add_post(post: Post) -> Post:
    posts = load_posts()
    posts.append(post)
    save_posts(posts)
    logger.info("Added post %s to queue", post.id)
    return post


def update_post(post_id: str, updates: dict) -> Post:
    posts = load_posts()
    for i, post in enumerate(posts):
        if post.id == post_id:
            updated = post.model_copy(update=updates)
            posts[i] = updated
            save_posts(posts)
            logger.info("Updated post %s", post_id)
            return updated
    raise ValueError(f"Post {post_id} not found")


def delete_post(post_id: str) -> bool:
    posts = load_posts()
    original_len = len(posts)
    posts = [p for p in posts if p.id != post_id]
    if len(posts) == original_len:
        return False
    save_posts(posts)
    logger.info("Deleted post %s", post_id)
    return True
