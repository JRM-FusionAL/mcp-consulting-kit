"""Social Poster MCP — Business logic and Pydantic models."""

from pydantic import BaseModel
from typing import Optional

from clients.reddit_client import RedditClient
from clients.twitter_client import TwitterClient
from clients.devto_client import DevtoClient
from clients.linkedin_client import LinkedInClient
from clients.mastodon_client import MastodonClient
from clients.bluesky_client import BlueskyClient
from clients.hashnode_client import HashnodeClient


# ── Request Models ──

class RedditPostRequest(BaseModel):
    subreddit: str
    title: str
    text: str = ""
    url: str = ""

class RedditCommentRequest(BaseModel):
    thing_id: str  # e.g. t3_abc123
    text: str

class TweetRequest(BaseModel):
    text: str
    reply_to: str = ""

class TweetThreadRequest(BaseModel):
    tweets: list[str]

class DevtoArticleRequest(BaseModel):
    title: str
    body_markdown: str
    tags: list[str] = []
    published: bool = False
    series: str = ""
    canonical_url: str = ""

class LinkedInTextPostRequest(BaseModel):
    text: str

class LinkedInLinkPostRequest(BaseModel):
    text: str
    url: str
    title: str = ""
    description: str = ""

class MastodonPostRequest(BaseModel):
    text: str
    visibility: str = "public"

class BlueskyPostRequest(BaseModel):
    text: str

class HashnodeArticleRequest(BaseModel):
    title: str
    content_markdown: str
    tags: list[dict] = []

class CrossPostRequest(BaseModel):
    """Post to multiple platforms at once."""
    text: str
    title: str = ""
    platforms: list[str] = []  # e.g. ["reddit", "twitter", "mastodon", "bluesky", "linkedin"]
    subreddit: str = ""  # Required if reddit in platforms
    body_markdown: str = ""  # Used for devto/hashnode if different from text
    tags: list[str] = []


# ── Functions ──

def post_to_reddit(payload: RedditPostRequest) -> dict:
    client = RedditClient()
    if payload.url:
        return client.submit_link(payload.subreddit, payload.title, payload.url)
    return client.submit_text(payload.subreddit, payload.title, payload.text)

def comment_on_reddit(payload: RedditCommentRequest) -> dict:
    client = RedditClient()
    return client.comment(payload.thing_id, payload.text)

def post_tweet(payload: TweetRequest) -> dict:
    client = TwitterClient()
    return client.post_tweet(payload.text, reply_to=payload.reply_to)

def post_tweet_thread(payload: TweetThreadRequest) -> list[dict]:
    client = TwitterClient()
    return client.post_thread(payload.tweets)

def create_devto_article(payload: DevtoArticleRequest) -> dict:
    client = DevtoClient()
    return client.create_article(
        title=payload.title,
        body_markdown=payload.body_markdown,
        tags=payload.tags if payload.tags else None,
        published=payload.published,
        series=payload.series,
        canonical_url=payload.canonical_url,
    )

def post_to_linkedin(payload: LinkedInTextPostRequest) -> dict:
    client = LinkedInClient()
    return client.create_text_post(payload.text)

def post_link_to_linkedin(payload: LinkedInLinkPostRequest) -> dict:
    client = LinkedInClient()
    return client.create_link_post(
        text=payload.text, url=payload.url,
        title=payload.title, description=payload.description,
    )

def post_to_mastodon(payload: MastodonPostRequest) -> dict:
    client = MastodonClient()
    return client.post_status(payload.text, visibility=payload.visibility)

def post_to_bluesky(payload: BlueskyPostRequest) -> dict:
    client = BlueskyClient()
    return client.create_post(payload.text)

def create_hashnode_article(payload: HashnodeArticleRequest) -> dict:
    client = HashnodeClient()
    return client.create_article(
        title=payload.title,
        content_markdown=payload.content_markdown,
        tags=payload.tags if payload.tags else None,
    )

def cross_post(payload: CrossPostRequest) -> dict:
    """Post to multiple platforms at once. Returns results per platform."""
    results = {}
    platforms = [p.lower().strip() for p in payload.platforms]

    if "twitter" in platforms or "x" in platforms:
        try:
            results["twitter"] = post_tweet(TweetRequest(text=payload.text))
        except Exception as e:
            results["twitter"] = {"error": str(e)}

    if "reddit" in platforms and payload.subreddit:
        try:
            results["reddit"] = post_to_reddit(
                RedditPostRequest(
                    subreddit=payload.subreddit,
                    title=payload.title or payload.text[:100],
                    text=payload.text,
                )
            )
        except Exception as e:
            results["reddit"] = {"error": str(e)}

    if "linkedin" in platforms:
        try:
            results["linkedin"] = post_to_linkedin(
                LinkedInTextPostRequest(text=payload.text)
            )
        except Exception as e:
            results["linkedin"] = {"error": str(e)}

    if "mastodon" in platforms:
        try:
            results["mastodon"] = post_to_mastodon(
                MastodonPostRequest(text=payload.text)
            )
        except Exception as e:
            results["mastodon"] = {"error": str(e)}

    if "bluesky" in platforms:
        try:
            results["bluesky"] = post_to_bluesky(
                BlueskyPostRequest(text=payload.text)
            )
        except Exception as e:
            results["bluesky"] = {"error": str(e)}

    if "devto" in platforms:
        try:
            body = payload.body_markdown or payload.text
            results["devto"] = create_devto_article(
                DevtoArticleRequest(
                    title=payload.title or "Untitled",
                    body_markdown=body,
                    tags=payload.tags,
                    published=True,
                )
            )
        except Exception as e:
            results["devto"] = {"error": str(e)}

    if "hashnode" in platforms:
        try:
            body = payload.body_markdown or payload.text
            results["hashnode"] = create_hashnode_article(
                HashnodeArticleRequest(
                    title=payload.title or "Untitled",
                    content_markdown=body,
                )
            )
        except Exception as e:
            results["hashnode"] = {"error": str(e)}

    return results
