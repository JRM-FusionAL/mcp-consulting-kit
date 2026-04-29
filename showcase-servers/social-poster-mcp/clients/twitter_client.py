"""X/Twitter client — OAuth 1.0a authentication."""

import os
from requests_oauthlib import OAuth1Session


class TwitterClient:
    BASE_URL = "https://api.twitter.com/2"

    def __init__(self):
        self.api_key = os.getenv("TWITTER_API_KEY", "")
        self.api_secret = os.getenv("TWITTER_API_SECRET", "")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

    def _session(self) -> OAuth1Session:
        return OAuth1Session(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
        )

    def post_tweet(self, text: str, reply_to: str = "") -> dict:
        """Post a tweet. Optionally reply to a tweet ID."""
        payload = {"text": text}
        if reply_to:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to}
        session = self._session()
        resp = session.post(f"{self.BASE_URL}/tweets", json=payload)
        resp.raise_for_status()
        return resp.json()

    def post_thread(self, tweets: list[str]) -> list[dict]:
        """Post a thread — list of tweet texts in order."""
        results = []
        reply_to_id = ""
        for text in tweets:
            result = self.post_tweet(text, reply_to=reply_to_id)
            results.append(result)
            reply_to_id = result.get("data", {}).get("id", "")
        return results
