"""Hashnode client — GraphQL API with API key."""

import os
import requests


class HashnodeClient:
    BASE_URL = "https://gql.hashnode.com"

    def __init__(self):
        self.api_key = os.getenv("HASHNODE_API_KEY", "")
        self.publication_id = os.getenv("HASHNODE_PUBLICATION_ID", "")

    def _headers(self):
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

    def create_article(self, title: str, content_markdown: str, tags: list[dict] = None) -> dict:
        """Publish an article to your Hashnode publication."""
        mutation = """
        mutation PublishPost($input: PublishPostInput!) {
            publishPost(input: $input) {
                post { id title slug url }
            }
        }
        """
        variables = {
            "input": {
                "publicationId": self.publication_id,
                "title": title,
                "contentMarkdown": content_markdown,
            }
        }
        if tags:
            variables["input"]["tags"] = tags

        resp = requests.post(
            self.BASE_URL,
            headers=self._headers(),
            json={"query": mutation, "variables": variables},
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()
        if "errors" in result:
            raise Exception(f"Hashnode API error: {result['errors']}")
        return result.get("data", {}).get("publishPost", {}).get("post", {})
