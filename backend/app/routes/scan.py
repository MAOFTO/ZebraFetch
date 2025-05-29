from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Optional
import asyncio
import tempfile
import os

from ..config import get_settings
from ..services.scanner import Scanner
from ..dependencies.auth import get_api_key

router = APIRouter(prefix="/v1")

@router.post("/scan")
async def scan_pdf(
    file: UploadFile = File(...),
    pages: Optional[str] = None,
    types: Optional[str] = None,
    embed_page: bool = False,
    embed_snippet: bool = False,
    api_key: str = Depends(get_api_key)
) -> JSONResponse:
    """Scan PDF for barcodes synchronously."""
    settings = get_settings()
    
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF"
        )
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > settings.max_pdf_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF must be smaller than {settings.max_pdf_mb}MB"
        )
    
    # Parse page range
    page_range = None
    if pages:
        try:
            if "-" in pages:
                start, end = map(int, pages.split("-"))
                page_range = list(range(start - 1, end))  # Convert to 0-based
            else:
                page_range = [int(p) - 1 for p in pages.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid page range format"
            )
    
    # Parse barcode types
    symbologies = types.split(",") if types else None
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        # Process PDF with timeout
        scanner = Scanner()
        loop = asyncio.get_event_loop()
        results = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: scanner.scan_pdf(
                    content,
                    page_range=page_range,
                    symbologies=symbologies,
                    embed_page=embed_page,
                    embed_snippet=embed_snippet
                )
            ),
            timeout=settings.sync_timeout_sec
        )
        
        return JSONResponse(content={"results": results})
    
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="PDF processing timed out"
        )
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except OSError:
            pass 