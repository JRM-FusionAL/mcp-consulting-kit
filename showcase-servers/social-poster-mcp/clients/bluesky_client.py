"""Bluesky client — AT Protocol with app password."""

import os
import requests


class BlueskyClient:
    def __init__(self):
        self.handle = os.getenv("BLUESKY_HANDLE", "")
        self.app_password = os.getenv("BLUESKY_APP_PASSWORD", "")
        self.base_url = "https://bsky.social/xrpc"
        self._session = None

    def _authenticate(self):
        if self._session:
            return self._session
        resp = requests.post(
            f"{self.base_url}/com.atproto.server.createSession",
            json={"identifier": self.handle, "password": self.app_password},
            timeout=15,
        )
        resp.raise_for_status()
        self._session = resp.json()
        return self._session

    def _headers(self):
        session = self._authenticate()
        return {"Authorization": f"Bearer {session['accessJwt']}"}

    def create_post(self, text: str) -> dict:
        """Create a Bluesky post."""
        from datetime import datetime, timezone
        session = self._authenticate()
        record = {
            "$type": "app.bsky.feed.post",
            "text": text,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        resp = requests.post(
            f"{self.base_url}/com.atproto.repo.createRecord",
            headers=self._headers(),
            json={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": record,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
