from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import PlainTextResponse, JSONResponse
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
    rate_limit_exceeded_handler
)

# Create FastAPI app with custom docs URLs
app = FastAPI(
    title="ZebraFetch API",
    version="1.0.0",
    description="Dockerized REST API for barcode extraction from PDF documents.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Load settings
settings = get_settings()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, payload_too_large_handler)
app.add_exception_handler(status.HTTP_429_TOO_MANY_REQUESTS, rate_limit_exceeded_handler)

# Metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status']
)

# Include routers
app.include_router(scan.router)
app.include_router(jobs.router)

@app.get("/healthz")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

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