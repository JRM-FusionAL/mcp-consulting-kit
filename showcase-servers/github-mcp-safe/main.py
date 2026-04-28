"""
GitHub MCP Safe — Showcase Server
Production-grade rate-limited GitHub MCP server for the mcp-consulting-kit stack.

Port: 8105
Transport: Streamable HTTP at /mcp
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# --- Security module path resolution (shared with other showcase servers) ---
_SECURITY_CANDIDATES = [
    Path(__file__).parent.parent / "common",
    Path.home() / "Projects" / "mcp-consulting-kit" / "showcase-servers" / "common",
]
for _candidate in _SECURITY_CANDIDATES:
    if _candidate.exists() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))
        break

try:
    from security import configure_cors, configure_observability, initialize_rate_limit_store
    _SECURITY_ENABLED = True
except ImportError:
    _SECURITY_ENABLED = False

from mcp_transport import mcp

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("github-mcp-safe")


@asynccontextmanager
async def _lifespan(app):
    app.state._mcp_session_context = mcp.session_manager.run()
    await app.state._mcp_session_context.__aenter__()
    yield
    ctx = getattr(app.state, "_mcp_session_context", None)
    if ctx is not None:
        await ctx.__aexit__(None, None, None)

app = FastAPI(
    title="GitHub MCP Safe",
    description="Production-grade rate-limited GitHub MCP server",
    version="1.0.0",
    lifespan=_lifespan,
)

if _SECURITY_ENABLED:
    configure_cors(app)
    configure_observability(app)
    initialize_rate_limit_store(app)

mcp.settings.streamable_http_path = "/"
mcp_app = mcp.streamable_http_app()
app.mount("/mcp", mcp_app)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "github-mcp-safe", "port": 8105}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8105"))
    uvicorn.run(app, host="0.0.0.0", port=port, forwarded_allow_ips="*")
