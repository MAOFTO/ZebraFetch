"""Custom exception classes for the ZebraFetch application."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def payload_too_large_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle payload too large errors."""
    return JSONResponse(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        content={"detail": "File too large"},
    )


async def rate_limit_exceeded_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle rate limit exceeded errors."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded"},
    )


class ZebraFetchException(StarletteHTTPException):
    """Base exception class for ZebraFetch application errors."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[dict] = None
    ) -> None:
        """Initialize the exception with status code and detail message."""
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers
        )


class PDFProcessingError(ZebraFetchException):
    """Exception raised when PDF processing fails."""

    def __init__(self, detail: str) -> None:
        """Initialize with a 400 Bad Request status code."""
        super().__init__(
            status_code=400,
            detail=f"PDF processing error: {detail}"
        )


class JobNotFoundError(ZebraFetchException):
    """Exception raised when a requested job is not found."""

    def __init__(self, job_id: str) -> None:
        """Initialize with a 404 Not Found status code."""
        super().__init__(
            status_code=404,
            detail=f"Job not found: {job_id}"
        )


class InvalidJobStateError(ZebraFetchException):
    """Exception raised when a job operation is invalid for its current state."""

    def __init__(self, job_id: str, current_state: str) -> None:
        """Initialize with a 400 Bad Request status code."""
        super().__init__(
            status_code=400,
            detail=(
                f"Invalid operation for job {job_id} "
                f"in state: {current_state}"
            )
        )


class AuthenticationError(ZebraFetchException):
    """Exception raised when authentication fails."""

    def __init__(self, detail: str = "Authentication failed") -> None:
        """Initialize with a 401 Unauthorized status code."""
        super().__init__(
            status_code=401,
            detail=detail
        )


class RateLimitError(ZebraFetchException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, detail: str = "Rate limit exceeded") -> None:
        """Initialize with a 429 Too Many Requests status code."""
        super().__init__(
            status_code=429,
            detail=detail
        )
