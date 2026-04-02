import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.models import Platform, PostStatus
from app.queue import load_posts, update_post
from app.services.formatter import format_post
from app.services.linkedin import LinkedInClient
from app.services.x import XClient

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

linkedin_client = LinkedInClient()
x_client = XClient()

PLATFORM_CLIENTS = {
    Platform.LINKEDIN: linkedin_client,
    Platform.X: x_client,
}


async def publish_post(post_id: str) -> dict:
    """Publish a single post to all its target platforms. Returns result summary."""
    from app.queue import get_post

    post = get_post(post_id)
    if post is None:
        return {"error": f"Post {post_id} not found"}

    errors: list[str] = []
    any_success = False

    for platform in post.platforms:
        client = PLATFORM_CLIENTS.get(platform)
        if client is None:
            errors.append(f"No client for platform {platform}")
            continue

        text = format_post(post.content, post.hashtags, platform.value)
        logger.info("Publishing post %s to %s", post.id, platform.value)

        result = await client.publish(text, post.image)

        if result["success"]:
            any_success = True
            logger.info("Post %s published to %s: %s", post.id, platform.value, result["platform_post_id"])
        else:
            errors.append(f"{platform.value}: {result['error']}")
            logger.error("Post %s failed on %s: %s", post.id, platform.value, result["error"])

    now = datetime.now(timezone.utc)
    if errors:
        update_post(post.id, {
            "status": PostStatus.FAILED,
            "error": "; ".join(errors),
            "published_at": now if any_success else None,
        })
    else:
        update_post(post.id, {
            "status": PostStatus.PUBLISHED,
            "published_at": now,
            "error": None,
        })

    return {"post_id": post.id, "success": not errors, "errors": errors}


async def check_and_publish() -> None:
    """Scheduled job: find pending posts whose scheduled_date has passed and publish them."""
    logger.info("Scheduler running: checking for posts to publish")
    posts = load_posts()
    now = datetime.now(timezone.utc)

    pending = [
        p for p in posts
        if p.status == PostStatus.PENDING and p.scheduled_date.replace(tzinfo=timezone.utc) <= now
    ]
    pending.sort(key=lambda p: p.scheduled_date)

    if not pending:
        logger.info("No pending posts to publish")
        return

    logger.info("Found %d posts to publish", len(pending))
    for post in pending:
        await publish_post(post.id)


def setup_scheduler() -> AsyncIOScheduler:
    """Configure the scheduler with the cron expression from settings."""
    cron_parts = settings.scheduler_cron.split()
    trigger = CronTrigger(
        minute=cron_parts[0],
        hour=cron_parts[1],
        day=cron_parts[2],
        month=cron_parts[3],
        day_of_week=cron_parts[4],
    )
    scheduler.add_job(check_and_publish, trigger, id="publish_job", replace_existing=True)
    logger.info("Scheduler configured with cron: %s", settings.scheduler_cron)
    return scheduler
