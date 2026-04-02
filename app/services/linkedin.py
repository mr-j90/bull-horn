import logging

import httpx

from app.config import settings
from app.services.base import PlatformClient

logger = logging.getLogger(__name__)

LINKEDIN_API_URL = "https://api.linkedin.com/v2/ugcPosts"
LINKEDIN_ME_URL = "https://api.linkedin.com/v2/me"


class LinkedInClient(PlatformClient):
    def __init__(self) -> None:
        self.access_token = settings.linkedin_access_token

    async def _get_person_urn(self, client: httpx.AsyncClient) -> str:
        resp = await client.get(
            LINKEDIN_ME_URL,
            headers={"Authorization": f"Bearer {self.access_token}"},
        )
        resp.raise_for_status()
        return f"urn:li:person:{resp.json()['id']}"

    async def publish(self, text: str, image_url: str | None = None) -> dict:
        if not self.access_token:
            logger.warning("LinkedIn access token not configured")
            return {"success": False, "platform_post_id": None, "error": "LinkedIn access token not configured"}

        try:
            async with httpx.AsyncClient() as client:
                author = await self._get_person_urn(client)

                payload = {
                    "author": author,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {
                        "com.linkedin.ugc.ShareContent": {
                            "shareCommentary": {"text": text},
                            "shareMediaCategory": "NONE",
                        }
                    },
                    "visibility": {
                        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                    },
                }

                resp = await client.post(
                    LINKEDIN_API_URL,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "X-Restli-Protocol-Version": "2.0.0",
                    },
                )

                if resp.status_code == 401:
                    logger.warning("LinkedIn token expired or invalid")
                    return {"success": False, "platform_post_id": None, "error": "LinkedIn token expired or invalid"}

                resp.raise_for_status()
                post_id = resp.json().get("id")
                logger.info("Published to LinkedIn: %s", post_id)
                return {"success": True, "platform_post_id": post_id, "error": None}

        except httpx.HTTPStatusError as e:
            error_msg = f"LinkedIn API error: {e.response.status_code} {e.response.text}"
            logger.error(error_msg)
            return {"success": False, "platform_post_id": None, "error": error_msg}
        except Exception as e:
            error_msg = f"LinkedIn publish failed: {e}"
            logger.error(error_msg)
            return {"success": False, "platform_post_id": None, "error": error_msg}
