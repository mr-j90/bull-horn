import hashlib
import hmac
import logging
import time
import base64
import secrets
from urllib.parse import quote

import httpx

from app.config import settings
from app.services.base import PlatformClient

logger = logging.getLogger(__name__)

X_TWEET_URL = "https://api.twitter.com/2/tweets"


class XClient(PlatformClient):
    def __init__(self) -> None:
        self.api_key = settings.x_api_key
        self.api_secret = settings.x_api_secret
        self.access_token = settings.x_access_token
        self.access_secret = settings.x_access_secret

    def _generate_oauth_signature(
        self, method: str, url: str, params: dict
    ) -> str:
        param_string = "&".join(
            f"{quote(k, safe='')}" + "=" + f"{quote(v, safe='')}"
            for k, v in sorted(params.items())
        )
        base_string = (
            f"{method.upper()}&{quote(url, safe='')}&{quote(param_string, safe='')}"
        )
        signing_key = f"{quote(self.api_secret, safe='')}&{quote(self.access_secret, safe='')}"
        signature = hmac.new(
            signing_key.encode(), base_string.encode(), hashlib.sha1
        )
        return base64.b64encode(signature.digest()).decode()

    def _build_auth_header(self, method: str, url: str) -> str:
        oauth_params = {
            "oauth_consumer_key": self.api_key,
            "oauth_nonce": secrets.token_hex(16),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_token": self.access_token,
            "oauth_version": "1.0",
        }

        signature = self._generate_oauth_signature(method, url, oauth_params)
        oauth_params["oauth_signature"] = signature

        header_parts = ", ".join(
            f'{quote(k, safe="")}="{quote(v, safe="")}"'
            for k, v in sorted(oauth_params.items())
        )
        return f"OAuth {header_parts}"

    async def publish(self, text: str, image_url: str | None = None) -> dict:
        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            logger.warning("X/Twitter credentials not fully configured")
            return {"success": False, "platform_post_id": None, "error": "X/Twitter credentials not configured"}

        try:
            auth_header = self._build_auth_header("POST", X_TWEET_URL)

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    X_TWEET_URL,
                    json={"text": text},
                    headers={
                        "Authorization": auth_header,
                        "Content-Type": "application/json",
                    },
                )

                if resp.status_code == 401:
                    logger.warning("X/Twitter credentials invalid or expired")
                    return {"success": False, "platform_post_id": None, "error": "X/Twitter credentials invalid"}

                resp.raise_for_status()
                tweet_data = resp.json().get("data", {})
                tweet_id = tweet_data.get("id")
                logger.info("Published to X: %s", tweet_id)
                return {"success": True, "platform_post_id": tweet_id, "error": None}

        except httpx.HTTPStatusError as e:
            error_msg = f"X API error: {e.response.status_code} {e.response.text}"
            logger.error(error_msg)
            return {"success": False, "platform_post_id": None, "error": error_msg}
        except Exception as e:
            error_msg = f"X publish failed: {e}"
            logger.error(error_msg)
            return {"success": False, "platform_post_id": None, "error": error_msg}
