"""Reddit client — OAuth2 script app authentication."""

import os
import requests


class RedditClient:
    BASE_URL = "https://oauth.reddit.com"
    AUTH_URL = "https://www.reddit.com/api/v1/access_token"

    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID", "")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        self.username = os.getenv("REDDIT_USERNAME", "")
        self.password = os.getenv("REDDIT_PASSWORD", "")
        self._token = None

    def _authenticate(self):
        if self._token:
            return self._token
        auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
        }
        headers = {"User-Agent": "FusionAL-SocialPoster/1.0"}
        resp = requests.post(self.AUTH_URL, auth=auth, data=data, headers=headers, timeout=15)
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self):
        token = self._authenticate()
        return {
            "Authorization": f"bearer {token}",
            "User-Agent": "FusionAL-SocialPoster/1.0",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def submit_text(self, subreddit: str, title: str, text: str) -> dict:
        """Submit a text post to a subreddit."""
        data = {
            "kind": "self",
            "sr": subreddit,
            "title": title,
            "text": text,
        }
        resp = requests.post(
            f"{self.BASE_URL}/api/submit",
            headers=self._headers(),
            data=data,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def submit_link(self, subreddit: str, title: str, url: str) -> dict:
        """Submit a link post to a subreddit."""
        data = {
            "kind": "link",
            "sr": subreddit,
            "title": title,
            "url": url,
        }
        resp = requests.post(
            f"{self.BASE_URL}/api/submit",
            headers=self._headers(),
            data=data,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def comment(self, thing_id: str, text: str) -> dict:
        """Post a comment on a thing (t3_ for posts, t1_ for comments)."""
        data = {"thing_id": thing_id, "text": text}
        resp = requests.post(
            f"{self.BASE_URL}/api/comment",
            headers=self._headers(),
            data=data,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
