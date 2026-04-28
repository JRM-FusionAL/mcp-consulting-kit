import os
import httpx

SLACK_BASE_URL = "https://slack.com/api"

class SlackClient:
    def __init__(self) -> None:
        token = os.getenv("SLACK_BOT_TOKEN")
        if not token:
            raise RuntimeError("SLACK_BOT_TOKEN not set")
        self.token = token
        self.client = httpx.Client(timeout=10.0)

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def post_message(self, channel: str, text: str):
        resp = self.client.post(
            f"{SLACK_BASE_URL}/chat.postMessage",
            headers=self._headers(),
            json={"channel": channel, "text": text},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack error: {data}")
        return data

    def list_channels(self):
        resp = self.client.get(
            f"{SLACK_BASE_URL}/conversations.list",
            headers=self._headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack error: {data}")
        return data.get("channels", [])

    def search_messages(self, query: str):
        resp = self.client.get(
            f"{SLACK_BASE_URL}/search.messages",
            headers=self._headers(),
            params={"query": query},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack error: {data}")
        return data.get("messages", {}).get("matches", [])
