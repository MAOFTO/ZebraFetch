"""Job management routes for the ZebraFetch API."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import Optional, Coroutine, Any
import asyncio
import tempfile
import os
import uuid
import sys

from app.config import get_settings
from app.services.scanner import Scanner
from app.dependencies.auth import get_api_key
from app.db import create_job, update_job_status, get_job

router = APIRouter(prefix="/v1")


# Global task group manager
class TaskGroupManager:
    """Manages a global asyncio.TaskGroup for job processing."""

    def __init__(self) -> None:
        """Initialize the TaskGroupManager."""
        self._task_group: Optional[Any] = None
        self._lock = asyncio.Lock()

    async def get_task_group(self) -> Any:
        """Get or create the global TaskGroup instance."""
        async with self._lock:
            if self._task_group is None:
                if sys.version_info >= (3, 11):
                    self._task_group = asyncio.TaskGroup()
                else:
                    raise NotImplementedError("TaskGroup requires Python 3.11+")
            return self._task_group

    async def create_task(self, coro: Coroutine[Any, Any, None]) -> None:
        """Add a coroutine to the global TaskGroup."""
        task_group = await self.get_task_group()
        async with task_group:
            task_group.create_task(coro)


# Initialize task group manager
task_manager = TaskGroupManager()


@router.post("/jobs")  # type: ignore
async def create_scan_job(
    file: UploadFile = File(...),
    pages: Optional[str] = None,
    types: Optional[str] = None,
    embed_page: bool = False,
    embed_snippet: bool = False,
    api_key: str = Depends(get_api_key),
) -> JSONResponse:
    """Create an asynchronous scan job."""
    settings = get_settings()

    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF"
        )

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > settings.max_pdf_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF must be smaller than {settings.max_pdf_mb}MB",
        )

    # Generate job ID and create temporary file
    job_id = str(uuid.uuid4())
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    # Create job record
    await create_job(job_id, temp_path)

    # Parse parameters
    page_range = None
    if pages:
        try:
            if "-" in pages:
                start, end = map(int, pages.split("-"))
                page_range = list(range(start - 1, end))
            else:
                page_range = [int(p) - 1 for p in pages.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid page range format",
            )

    symbologies = types.split(",") if types else None

    # Schedule processing
    async def process_job() -> None:
        try:
            # Update status to running
            await update_job_status(job_id, "running")

            # Process PDF
            scanner = Scanner()
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: scanner.scan_pdf(
                    content,
                    page_range=page_range,
                    symbologies=symbologies,
                    embed_page=embed_page,
                    embed_snippet=embed_snippet,
                ),
            )

            # Update job with results
            await update_job_status(job_id, "completed", result={"results": results})

        except Exception as e:
            # Update job with error
            await update_job_status(job_id, "failed", result={"error": str(e)})

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    # Add task to group
    await task_manager.create_task(process_job())

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED, content={"job_id": job_id}
    )


@router.get("/jobs/{job_id}")  # type: ignore
async def get_job_status(
    job_id: str, api_key: str = Depends(get_api_key)
) -> JSONResponse:
    """Get the status and results of a scan job."""
    job = await get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    return JSONResponse(content=job)
