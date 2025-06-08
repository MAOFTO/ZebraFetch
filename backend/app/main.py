"""Main application module."""

import asyncio
import logging
from typing import Dict, Union, Awaitable
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, make_asgi_app
from fastapi.exceptions import RequestValidationError

from .config import get_settings
from .db import init_db, cleanup_expired_jobs
from .exceptions import (
    validation_exception_handler as old_validation_handler,
    http_exception_handler as old_http_handler,
    payload_too_large_handler,
    rate_limit_exceeded_handler,
    ZebraFetchException,
)
from .routes import jobs, scan

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ZebraFetch API",
    description="PDF processing and barcode scanning service",
    version="1.0.0",
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=True,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)

# Add exception handlers
app.add_exception_handler(RequestValidationError, old_validation_handler)  # type: ignore
app.add_exception_handler(StarletteHTTPException, old_http_handler)  # type: ignore
app.add_exception_handler(413, payload_too_large_handler)  # type: ignore
app.add_exception_handler(429, rate_limit_exceeded_handler)  # type: ignore

# Metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP Requests", ["method", "endpoint", "status"]
)

# Setup Prometheus metrics if enabled
if settings.metrics_enabled:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Include routers
app.include_router(scan.router)
app.include_router(jobs.router)


@app.get("/health")  # type: ignore
async def health_check() -> Dict[str, str]:
    """Check API health."""
    return {"status": "healthy"}


@app.get("/")  # type: ignore
async def root() -> Dict[str, str]:
    """Get API information."""
    return {
        "name": "ZebraFetch API",
        "version": "1.0.0",
        "description": "PDF processing and barcode scanning service",
    }


@app.on_event("startup")  # type: ignore
async def startup_event() -> None:
    """Initialize application on startup."""
    await init_db()
    asyncio.create_task(periodic_cleanup())


async def periodic_cleanup() -> None:
    """Periodically clean up expired jobs."""
    while True:
        try:
            await cleanup_expired_jobs()
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")
        await asyncio.sleep(settings.cleanup_interval)


@app.exception_handler(ZebraFetchException)  # type: ignore
async def zebrafetch_exception_handler(
    request: Request, exc: Exception
) -> Union[Response, Awaitable[Response]]:
    """Handle ZebraFetch exceptions."""
    if isinstance(exc, ZebraFetchException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )
    raise exc
