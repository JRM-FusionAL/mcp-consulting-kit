import os
import sys
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from mcp_tools import handle_nl_query

PORT = int(os.getenv("PORT", "8101"))

app = FastAPI(title="Business Intelligence MCP")

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

class NLQueryRequest(BaseModel):
    query: str
    schema_hint: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/nl-query")
def nl_query(
    req: NLQueryRequest,
    _auth: None = Depends(verify_api_key),
    _rate_limit: None = Depends(enforce_rate_limit),
):
    try:
        result = handle_nl_query(req)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
