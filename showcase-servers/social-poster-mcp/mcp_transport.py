"""
Streamable HTTP MCP transport — Social Poster MCP

Exposes Reddit, X/Twitter, Dev.to, LinkedIn, Mastodon, Bluesky, Hashnode
as MCP tools. Includes a cross_post tool for multi-platform blitz.

Clients connect to: http://localhost:8105/mcp
"""

from mcp.server.fastmcp import FastMCP
from mcp_tools import (
    RedditPostRequest, RedditCommentRequest,
    TweetRequest, TweetThreadRequest,
    DevtoArticleRequest,
    LinkedInTextPostRequest, LinkedInLinkPostRequest,
    MastodonPostRequest, BlueskyPostRequest,
    HashnodeArticleRequest, CrossPostRequest,
    post_to_reddit, comment_on_reddit,
    post_tweet, post_tweet_thread,
    create_devto_article,
    post_to_linkedin, post_link_to_linkedin,
    post_to_mastodon, post_to_bluesky,
    create_hashnode_article, cross_post,
)

mcp = FastMCP("social-poster-mcp", streamable_http_path="/")


# ── Reddit ──

@mcp.tool(
    name="rd_post",
    description="Submit a text or link post to a subreddit. Provide url for link posts, text for self posts.",
)
def rd_post(subreddit: str, title: str, text: str = "", url: str = "") -> dict:
    return post_to_reddit(RedditPostRequest(subreddit=subreddit, title=title, text=text, url=url))


@mcp.tool(
    name="rd_comment",
    description="Post a comment on Reddit. thing_id format: t3_xxxxx (post) or t1_xxxxx (comment).",
)
def rd_comment(thing_id: str, text: str) -> dict:
    return comment_on_reddit(RedditCommentRequest(thing_id=thing_id, text=text))


# ── X / Twitter ──

@mcp.tool(
    name="x_post",
    description="Post a tweet. Optionally reply to a tweet by providing reply_to tweet ID.",
)
def x_post(text: str, reply_to: str = "") -> dict:
    return post_tweet(TweetRequest(text=text, reply_to=reply_to))


@mcp.tool(
    name="x_thread",
    description="Post a Twitter thread. Provide a list of tweet texts in order.",
)
def x_thread(tweets: list[str]) -> list[dict]:
    return post_tweet_thread(TweetThreadRequest(tweets=tweets))


# ── Dev.to ──

@mcp.tool(
    name="devto_pub",
    description="Publish or draft an article on Dev.to. Set published=true to go live immediately.",
)
def devto_pub(
    title: str, body_markdown: str, tags: list[str] = [],
    published: bool = False, series: str = "", canonical_url: str = "",
) -> dict:
    return create_devto_article(DevtoArticleRequest(
        title=title, body_markdown=body_markdown, tags=tags,
        published=published, series=series, canonical_url=canonical_url,
    ))


# ── LinkedIn ──

@mcp.tool(
    name="li_post",
    description="Create a text post on LinkedIn.",
)
def li_post(text: str) -> dict:
    return post_to_linkedin(LinkedInTextPostRequest(text=text))


@mcp.tool(
    name="li_link",
    description="Create a LinkedIn post with a link attachment.",
)
def li_link(text: str, url: str, title: str = "", description: str = "") -> dict:
    return post_link_to_linkedin(LinkedInLinkPostRequest(
        text=text, url=url, title=title, description=description,
    ))


# ── Mastodon ──

@mcp.tool(
    name="mast_post",
    description="Post a status (toot) on Mastodon. Visibility: public, unlisted, private, direct.",
)
def mast_post(text: str, visibility: str = "public") -> dict:
    return post_to_mastodon(MastodonPostRequest(text=text, visibility=visibility))


# ── Bluesky ──

@mcp.tool(
    name="bsky_post",
    description="Create a post on Bluesky (AT Protocol).",
)
def bsky_post(text: str) -> dict:
    return post_to_bluesky(BlueskyPostRequest(text=text))


# ── Hashnode ──

@mcp.tool(
    name="hash_pub",
    description="Publish an article to your Hashnode publication.",
)
def hash_pub(title: str, content_markdown: str, tags: list[dict] = []) -> dict:
    return create_hashnode_article(HashnodeArticleRequest(
        title=title, content_markdown=content_markdown, tags=tags,
    ))


# ── Cross-Post (Multi-Platform Blitz) ──

@mcp.tool(
    name="xpost",
    description=(
        "Post to multiple platforms at once. Platforms: twitter, reddit, linkedin, "
        "mastodon, bluesky, devto, hashnode. Provide subreddit if reddit is included. "
        "For devto/hashnode, body_markdown is used if provided, otherwise text is used."
    ),
)
def xpost(
    text: str, platforms: list[str], title: str = "",
    subreddit: str = "", body_markdown: str = "", tags: list[str] = [],
) -> dict:
    return cross_post(CrossPostRequest(
        text=text, platforms=platforms, title=title,
        subreddit=subreddit, body_markdown=body_markdown, tags=tags,
    ))


