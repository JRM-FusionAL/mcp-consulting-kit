"""Dev.to client — API key authentication."""

import os
import requests


class DevtoClient:
    BASE_URL = "https://dev.to/api"

    def __init__(self):
        self.api_key = os.getenv("DEVTO_API_KEY", "")

    def _headers(self):
        return {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_article(
        self, title: str, body_markdown: str, tags: list[str] = None,
        published: bool = False, series: str = "", canonical_url: str = "",
    ) -> dict:
        """Create or draft an article on Dev.to."""
        article = {"title": title, "body_markdown": body_markdown}
        if tags:
            article["tags"] = tags[:4]  # Dev.to max 4 tags
        if published:
            article["published"] = True
        if series:
            article["series"] = series
        if canonical_url:
            article["canonical_url"] = canonical_url

        resp = requests.post(
            f"{self.BASE_URL}/articles",
            headers=self._headers(),
            json={"article": article},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def update_article(self, article_id: int, **kwargs) -> dict:
        """Update an existing article."""
        resp = requests.put(
            f"{self.BASE_URL}/articles/{article_id}",
            headers=self._headers(),
            json={"article": kwargs},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def list_my_articles(self, per_page: int = 10) -> list[dict]:
        """List your own articles."""
        resp = requests.get(
            f"{self.BASE_URL}/articles/me",
            headers=self._headers(),
            params={"per_page": per_page},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
