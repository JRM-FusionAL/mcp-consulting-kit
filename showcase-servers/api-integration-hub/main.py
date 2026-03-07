import os
import sys
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from showcase_servers.common.security_baseline import apply_security_baseline
from mcp_tools import (
    SlackMessageRequest,
    GitHubIssueRequest,
    StripeCustomerLookupRequest,
    send_slack_message,
    create_issue_and_optionally_notify,
    lookup_stripe_customer,
)
app = FastAPI(
    docs_url=None,   # set to "/docs" only for internal envs
    redoc_url=None
)

apply_security_baseline(app)

PORT = int(os.getenv("PORT", "8102"))

app = FastAPI(title="API Integration Hub MCP")

COMMON_PATH = Path(__file__).resolve().parents[1] / "common"
if str(COMMON_PATH) not in sys.path:
    sys.path.insert(0, str(COMMON_PATH))

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

@app.post("/slack/send")
def slack_send(
    req: SlackMessageRequest,
    _auth: None = Depends(verify_api_key),
    _rate_limit: None = Depends(enforce_rate_limit),
):
    try:
        return send_slack_message(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/github/create-issue")
async def github_create_issue(
    req: GitHubIssueRequest,
    _auth: None = Depends(verify_api_key),
    _rate_limit: None = Depends(enforce_rate_limit),
):
    try:
        return await create_issue_and_optionally_notify(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/stripe/customer")
def stripe_customer(
    req: StripeCustomerLookupRequest,
    _auth: None = Depends(verify_api_key),
    _rate_limit: None = Depends(enforce_rate_limit),
):
    try:
        return lookup_stripe_customer(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
from fastapi import FastAPI
from showcase_servers.common.security_baseline import apply_security_baseline
