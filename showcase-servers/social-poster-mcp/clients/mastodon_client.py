"""Mastodon client — OAuth2 bearer token."""

import os
import requests


class MastodonClient:
    def __init__(self):
        self.instance_url = os.getenv("MASTODON_INSTANCE_URL", "https://mastodon.social").rstrip("/")
        self.access_token = os.getenv("MASTODON_ACCESS_TOKEN", "")

    def _headers(self):
        return {"Authorization": f"Bearer {self.access_token}"}

    def post_status(self, text: str, visibility: str = "public", spoiler_text: str = "") -> dict:
        """Post a status (toot). Visibility: public, unlisted, private, direct."""
        data = {"status": text, "visibility": visibility}
        if spoiler_text:
            data["spoiler_text"] = spoiler_text
        resp = requests.post(
            f"{self.instance_url}/api/v1/statuses",
            headers=self._headers(),
            json=data,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
