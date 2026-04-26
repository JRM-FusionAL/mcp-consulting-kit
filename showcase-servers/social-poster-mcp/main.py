import os
import sys
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from showcase_servers.common.security_baseline import apply_security_baseline

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

PORT = int(os.getenv("PORT", "8105"))

app = FastAPI(title="Social Poster MCP")

COMMON_CANDIDATES = [
    Path(__file__).resolve().parents[1] / "common",
    Path(__file__).resolve().parent / "common",
]
for common_path in COMMON_CANDIDATES:
    if common_path.exists() and str(common_path) not in sys.path:
        sys.path.insert(0, str(common_path))
        break

from security import (
    configure_cors,
    configure_observability,
    enforce_rate_limit,
    initialize_rate_limit_store,
    verify_api_key,
)

configure_cors(app)
configure_observability(app)
initialize_rate_limit_store(app)

from mcp_transport import mcp
mcp.settings.streamable_http_path = "/"
mcp_app = mcp.streamable_http_app()
app.mount("/mcp", mcp_app)


@app.on_event("startup")
async def startup_mcp_app():
    app.state._mcp_session_context = mcp.session_manager.run()
    await app.state._mcp_session_context.__aenter__()


@app.on_event("shutdown")
async def shutdown_mcp_app():
    context_manager = getattr(app.state, "_mcp_session_context", None)
    if context_manager is not None:
        await context_manager.__aexit__(None, None, None)


@app.get("/health")
def health():
    return {"status": "ok", "mcp_endpoint": f"http://localhost:{PORT}/mcp"}


# ── REST Endpoints (non-MCP access) ──

@app.post("/reddit/post")
def rest_reddit_post(
    req: RedditPostRequest,
    _auth: None = Depends(verify_api_key),
    _rl: None = Depends(enforce_rate_limit),
):
    try:
        return post_to_reddit(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/reddit/comment")
def rest_reddit_comment(
    req: RedditCommentRequest,
    _auth: None = Depends(verify_api_key),
    _rl: None = Depends(enforce_rate_limit),
):
    try:
        return comment_on_reddit(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/twitter/post")
def rest_twitter_post(
    req: TweetRequest,
    _auth: None = Depends(verify_api_key),
    _rl: None = Depends(enforce_rate_limit),
):
    try:
        return post_tweet(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/twitter/thread")
def rest_twitter_thread(
    req: TweetThreadRequest,
    _auth: None = Depends(verify_api_key),
    _rl: None = Depends(enforce_rate_limit),
):
    try:
        return post_tweet_thread(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/devto/publish")
def rest_devto_publish(
    req: DevtoArticleRequest,
    _auth: None = Depends(verify_api_key),
    _rl: None = Depends(enforce_rate_limit),
):
    try:
        return create_devto_article(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/linkedin/post")
def rest_linkedin_post(
    req: LinkedInTextPostRequest,
    _auth: None = Depends(verify_api_key),
    _rl: None = Depends(enforce_rate_limit),
):
    try:
        return post_to_linkedin(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/mastodon/post")
def rest_mastodon_post(
    req: MastodonPostRequest,
    _auth: None = Depends(verify_api_key),
    _rl: None = Depends(enforce_rate_limit),
):
    try:
        return post_to_mastodon(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/bluesky/post")
def rest_bluesky_post(
    req: BlueskyPostRequest,
    _auth: None = Depends(verify_api_key),
    _rl: None = Depends(enforce_rate_limit),
):
    try:
        return post_to_bluesky(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/hashnode/publish")
def rest_hashnode_publish(
    req: HashnodeArticleRequest,
    _auth: None = Depends(verify_api_key),
    _rl: None = Depends(enforce_rate_limit),
):
    try:
        return create_hashnode_article(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/cross-post")
def rest_cross_post(
    req: CrossPostRequest,
    _auth: None = Depends(verify_api_key),
    _rl: None = Depends(enforce_rate_limit),
):
    try:
        return cross_post(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
