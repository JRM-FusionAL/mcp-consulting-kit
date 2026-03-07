from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response
import os
import time


def apply_security_baseline(app: FastAPI) -> FastAPI:
    # Disable docs in production by setting ENABLE_DOCS=false at app creation time
    # (keep this middleware-focused and reusable)

    allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[h.strip() for h in allowed_hosts if h.strip()],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in allowed_origins if o.strip()],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        start = time.time()
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none';"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Response-Time-ms"] = str(int((time.time() - start) * 1000))
        return response

    return app