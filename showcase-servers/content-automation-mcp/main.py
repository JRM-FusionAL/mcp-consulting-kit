import os
import sys
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from mcp_tools import (
    ScrapeRequest,
    RSSRequest,
    scrape_article,
    scrape_links,
    scrape_tables,
    parse_rss,
)

PORT = int(os.getenv("PORT", "8103"))

app = FastAPI(title="Content Automation MCP")

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

@app.post("/scrape/article")
def scrape_article_endpoint(
    req: ScrapeRequest,
    _auth: None = Depends(verify_api_key),
    _rate_limit: None = Depends(enforce_rate_limit),
):
    try:
        return scrape_article(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/scrape/links")
def scrape_links_endpoint(
    req: ScrapeRequest,
    _auth: None = Depends(verify_api_key),
    _rate_limit: None = Depends(enforce_rate_limit),
):
    try:
        return scrape_links(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/scrape/tables")
def scrape_tables_endpoint(
    req: ScrapeRequest,
    _auth: None = Depends(verify_api_key),
    _rate_limit: None = Depends(enforce_rate_limit),
):
    try:
        return scrape_tables(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/rss/parse")
def rss_parse_endpoint(
    req: RSSRequest,
    _auth: None = Depends(verify_api_key),
    _rate_limit: None = Depends(enforce_rate_limit),
):
    try:
        return parse_rss(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
