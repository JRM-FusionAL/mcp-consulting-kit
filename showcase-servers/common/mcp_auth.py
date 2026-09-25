"""Apply the REST API-key policy to mounted MCP transports.

FastAPI dependencies on parent routes do not protect a mounted ASGI app.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


def protect_mcp(app: FastAPI, verify_api_key) -> None:
    @app.middleware("http")
    async def authenticate_mcp(request: Request, call_next):
        if request.url.path == "/mcp" or request.url.path.startswith("/mcp/"):
            key = request.headers.get("X-API-Key")
            if not key:
                scheme, _, bearer = request.headers.get("Authorization", "").partition(" ")
                if scheme.lower() == "bearer":
                    key = bearer.strip()
            try:
                verify_api_key(request, key)
            except HTTPException as exc:
                return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        return await call_next(request)
