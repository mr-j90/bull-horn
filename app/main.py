import logging
from contextlib import asynccontextmanager
from datetime import timezone
from typing import AsyncIterator

from fastapi import FastAPI

from app.models import PostStatus
from app.queue import load_posts
from app.routes.posts import router as posts_router
from app.scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started")
    yield
    scheduler.shutdown()
    logger.info("Scheduler shut down")


app = FastAPI(title="Bullhorn", version="0.1.0", lifespan=lifespan)
app.include_router(posts_router)


@app.get("/health")
async def health() -> dict:
    posts = load_posts()
    pending = [p for p in posts if p.status == PostStatus.PENDING]
    pending.sort(key=lambda p: p.scheduled_date)
    next_scheduled = (
        pending[0].scheduled_date.replace(tzinfo=timezone.utc).isoformat()
        if pending
        else None
    )
    return {
        "status": "ok",
        "queue_size": len(posts),
        "next_scheduled": next_scheduled,
    }
