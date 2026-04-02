from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Platform(str, Enum):
    LINKEDIN = "linkedin"
    X = "x"


class PostStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
    SKIPPED = "skipped"


class Post(BaseModel):
    id: str
    content: str
    hashtags: list[str] = []
    platforms: list[Platform]
    scheduled_date: datetime
    status: PostStatus = PostStatus.PENDING
    image: Optional[str] = None
    published_at: Optional[datetime] = None
    error: Optional[str] = None


class PostCreate(BaseModel):
    id: str
    content: str
    hashtags: list[str] = []
    platforms: list[Platform]
    scheduled_date: datetime
    image: Optional[str] = None


class PostUpdate(BaseModel):
    content: Optional[str] = None
    hashtags: Optional[list[str]] = None
    platforms: Optional[list[Platform]] = None
    scheduled_date: Optional[datetime] = None
    image: Optional[str] = None
