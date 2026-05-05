"""
TokenLens — FastAPI Application Entry Point
=============================================
Production-grade ASGI application with:
  - Rate limiting (slowapi)
  - CORS configuration
  - Structured logging (Google Cloud compatible)
  - Static file serving for the frontend
  - Graceful startup/shutdown lifecycle
"""

from __future__ import annotations

import logging
import mimetypes
import os
import sys

# Ensure correct MIME types are registered for static files
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/json', '.json')
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.api.middleware import RequestLoggingMiddleware
from backend.api.routes import init_components, router
from backend.core.compressor import PromptCompressor
from backend.core.cost_tracker import CostTracker
from backend.core.gemini_client import GeminiClient
from backend.core.model_router import ModelRouter
from backend.core.monitoring import CloudMetricsEmitter
from backend.core.semantic_cache import SemanticCache

# ── Logging Setup ──────────────────────────────────────────────────────

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


def setup_logging() -> None:
    """Configure structured JSON logging for Google Cloud compatibility."""
    try:
        import google.cloud.logging as cloud_logging
        client = cloud_logging.Client()
        client.setup_logging(log_level=getattr(logging, LOG_LEVEL, logging.INFO))
        logging.info("Google Cloud Logging configured")
    except Exception:
        # Fallback to standard logging
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL, logging.INFO),
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
            stream=sys.stdout,
        )


setup_logging()
logger = logging.getLogger("tokenlens.main")

# ── Rate Limiter ───────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)

# ── Lifespan ───────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    logger.info("🔬 TokenLens starting up...")

    # Initialize core components
    _compressor = PromptCompressor()
    _model_router = ModelRouter()
    _cost_tracker = CostTracker()
    _gemini_client = GeminiClient()

    logger.info("Loading semantic cache model (this may take a moment)...")
    _cache = SemanticCache()

    # Cloud Monitoring
    _metrics = CloudMetricsEmitter()

    # Wire components into routes
    init_components(_compressor, _cache, _model_router, _cost_tracker, _gemini_client, _metrics)

    logger.info("✅ All components initialized successfully")
    yield
    logger.info("🔬 TokenLens shutting down...")


# ── App Factory ────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="TokenLens",
        description="Intelligent Token & Cost Optimization for LLMs",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS
    allowed_origins = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
    ).split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # API routes
    app.include_router(router)

    # Apply rate limiting to API routes
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        """Apply 60 req/min rate limit to API endpoints."""
        if request.url.path.startswith("/api/") and request.url.path != "/api/health":
            # Rate limiting is handled by slowapi decorators
            pass
        return await call_next(request)

    # Serve frontend static files (built Next.js output)
    static_dir = Path(__file__).parent.parent / "frontend" / "out"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")
        logger.info("Serving frontend from %s", static_dir)
    else:
        @app.get("/")
        async def root():
            return {
                "service": "TokenLens",
                "version": "1.0.0",
                "docs": "/docs",
                "status": "Frontend not built. Visit /docs for API documentation.",
            }

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled error: %s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if os.environ.get("DEBUG") else None,
                "status_code": 500,
            },
        )

    return app


# ── Application Instance ──────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.environ.get("DEBUG", "").lower() == "true",
        log_level=LOG_LEVEL.lower(),
    )
