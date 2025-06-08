"""Database operations for job management and persistence."""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from contextlib import contextmanager
import asyncio
from functools import partial
import os

from .config import get_settings


@contextmanager
def get_db_connection():
    """Get a SQLite database connection."""
    settings = get_settings()
    db_path = settings.sqlite_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


async def init_db():
    """Initialize the database schema."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _init_db_sync)


def _init_db_sync():
    """Initialize the database schema synchronously."""
    with get_db_connection() as conn:
        with open("schemas/jobs.sql", "r") as f:
            conn.executescript(f.read())
        conn.commit()


async def create_job(job_id: str, input_path: str) -> None:
    """Create a new job record in the database."""
    settings = get_settings()
    expires_at = datetime.utcnow() + timedelta(hours=settings.job_retention_hours)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None, partial(_create_job_sync, job_id, input_path, expires_at)
    )


def _create_job_sync(job_id: str, input_path: str, expires_at: datetime) -> None:
    """Create a new job record synchronously."""
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO jobs (id, status, input_path, expires_at)
            VALUES (?, 'pending', ?, ?)
            """,
            (job_id, input_path, expires_at.isoformat()),
        )
        conn.commit()


async def update_job_status(
    job_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    artifact_paths: Optional[list] = None,
) -> None:
    """Update job status and optionally set result and artifact paths."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None, partial(_update_job_sync, job_id, status, result, artifact_paths)
    )


def _update_job_sync(
    job_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    artifact_paths: Optional[list] = None,
) -> None:
    """Update job status synchronously with optional result and artifacts."""
    with get_db_connection() as conn:
        updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
        params = [status]

        if result is not None:
            updates.append("result_json = ?")
            params.append(json.dumps(result))

        if artifact_paths is not None:
            updates.append("artifact_paths = ?")
            params.append(json.dumps(artifact_paths))

        query = "UPDATE jobs " f"SET {', '.join(updates)} " "WHERE id = ?"
        params.append(job_id)

        conn.execute(query, params)
        conn.commit()


async def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve job details by ID."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_get_job_sync, job_id))


def _get_job_sync(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve job details synchronously by ID."""
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            return None

        job = dict(row)
        if job.get("result_json"):
            job["result_json"] = json.loads(job["result_json"])
        if job.get("artifact_paths"):
            job["artifact_paths"] = json.loads(job["artifact_paths"])
        return job


async def cleanup_expired_jobs() -> None:
    """Remove expired jobs and their associated artifacts."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _cleanup_expired_jobs_sync)


def _cleanup_expired_jobs_sync() -> None:
    """Remove expired jobs and their artifacts synchronously."""
    with get_db_connection() as conn:
        # Get expired jobs with artifacts
        cursor = conn.execute(
            """
            SELECT id, artifact_paths
            FROM jobs
            WHERE expires_at < CURRENT_TIMESTAMP
            """
        )
        expired_jobs = cursor.fetchall()

        # Delete expired jobs
        conn.execute("DELETE FROM jobs WHERE expires_at < CURRENT_TIMESTAMP")
        conn.commit()

        # Clean up artifacts
        for job in expired_jobs:
            if job["artifact_paths"]:
                artifact_paths = json.loads(job["artifact_paths"])
                for path in artifact_paths:
                    try:
                        os.remove(path)
                    except OSError:
                        pass  # Ignore errors during cleanup
