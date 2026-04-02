from abc import ABC, abstractmethod


class PlatformClient(ABC):
    @abstractmethod
    async def publish(self, text: str, image_url: str | None = None) -> dict:
        """Publish a post. Returns {"success": bool, "platform_post_id": str | None, "error": str | None}"""
        ...
