"""LinkedIn client — OAuth2 bearer token."""

import os
import requests


class LinkedInClient:
    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def get_profile(self) -> dict:
        """Get authenticated user's profile (needed for person URN)."""
        resp = requests.get(
            f"{self.BASE_URL}/userinfo",
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def create_text_post(self, text: str, visibility: str = "PUBLIC") -> dict:
        """Create a text post on LinkedIn."""
        profile = self.get_profile()
        person_urn = f"urn:li:person:{profile['sub']}"

        payload = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            },
        }
        resp = requests.post(
            f"{self.BASE_URL}/ugcPosts",
            headers=self._headers(),
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def create_link_post(self, text: str, url: str, title: str = "", description: str = "") -> dict:
        """Create a post with a link attachment."""
        profile = self.get_profile()
        person_urn = f"urn:li:person:{profile['sub']}"

        media = {"status": "READY", "originalUrl": url}
        if title:
            media["title"] = {"text": title}
        if description:
            media["description"] = {"text": description}

        payload = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "ARTICLE",
                    "media": [media],
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }
        resp = requests.post(
            f"{self.BASE_URL}/ugcPosts",
            headers=self._headers(),
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
