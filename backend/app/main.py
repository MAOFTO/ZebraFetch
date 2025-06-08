"""Main FastAPI application module for ZebraFetch."""

from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, make_asgi_app
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import asyncio

from .config import get_settings
from .db import init_db, cleanup_expired_jobs
from .routes import scan, jobs
from .exceptions import (
    validation_exception_handler,
    http_exception_handler,
    payload_too_large_handler,
    rate_limit_exceeded_handler,
    ZebraFetchException,
)

# Create FastAPI app with custom docs URLs
app = FastAPI(
    title="ZebraFetch API",
    version="1.0.0",
    description=(
        "Dockerized REST API for barcode extraction "
        "from PDF documents."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Load settings
settings = get_settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=True,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)

# Add exception handlers
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)
app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler
)
app.add_exception_handler(
    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    payload_too_large_handler
)
app.add_exception_handler(
    status.HTTP_429_TOO_MANY_REQUESTS,
    rate_limit_exceeded_handler
)

# Metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP Requests",
    ["method", "endpoint", "status"]
)

# Setup Prometheus metrics if enabled
if settings.metrics_enabled:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Include routers
app.include_router(scan.router)
app.include_router(jobs.router)


@app.get("/health")
async def health_check():
    """Check the health status of the application."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Return basic API information."""
    return {
        "name": "ZebraFetch API",
        "version": "1.0.0",
        "description": "PDF processing and barcode scanning service",
    }


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Initialize database
    await init_db()

    # Initialize task group for async jobs
    jobs.init_task_group()

    # Start background task for cleaning up expired jobs
    asyncio.create_task(periodic_cleanup())


async def periodic_cleanup():
    """Periodically clean up expired jobs."""
    while True:
        await cleanup_expired_jobs()
        await asyncio.sleep(3600)  # Run every hour


@app.exception_handler(ZebraFetchException)
async def zebrafetch_exception_handler(request, exc):
    """Handle ZebraFetch exceptions and return appropriate HTTP responses."""
    return HTTPException(
        status_code=exc.status_code,
        detail=exc.detail,
        headers=exc.headers
    )
