from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1 import api_router
from app.config import settings
from app.database.session import SessionLocal
from app.ledger.service import LedgerService
from app.network.sync import start_background_sync


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure genesis block exists
    db = SessionLocal()
    try:
        LedgerService(db).ensure_genesis()
        db.commit()
    finally:
        db.close()
    start_background_sync()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Pakistan Trust Network API",
        description=(
            "Open-source trust infrastructure for issuing, storing and verifying "
            "tamper-evident educational and professional credentials.\n\n"
            "**Not affiliated with or endorsed by any government organization.**\n\n"
            "Architecture: proof on-chain, data off-chain."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "ptn-api", "version": "0.1.0"}

    @app.get("/")
    def root():
        return {
            "name": "Pakistan Trust Network",
            "tagline": "Issue. Own. Verify.",
            "docs": "/api/docs",
            "disclaimer": "Open-source reference implementation. Not a government endorsement.",
        }

    app.include_router(api_router)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        if settings.ptn_debug:
            return JSONResponse(status_code=500, content={"detail": str(exc)})
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return app


app = create_app()
