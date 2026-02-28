import os
import sys
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from mcp_tools import (
    SlackMessageRequest,
    GitHubIssueRequest,
    StripeCustomerLookupRequest,
    send_slack_message,
    create_issue_and_optionally_notify,
    lookup_stripe_customer,
)

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

# Mount Streamable HTTP MCP transport at /mcp
from mcp_transport import mcp
app.mount("/mcp", mcp.streamable_http_app())

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
def github_create_issue(
    req: GitHubIssueRequest,
    _auth: None = Depends(verify_api_key),
    _rate_limit: None = Depends(enforce_rate_limit),
):
    try:
        return create_issue_and_optionally_notify(req)
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
