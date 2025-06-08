"""Configuration settings and environment variables for the ZebraFetch \
application."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class CORSSettings(BaseSettings):
    """CORS (Cross-Origin Resource Sharing) configuration settings."""

    allow_origins: List[str] = Field(default_factory=list)
    allow_methods: List[str] = Field(default_factory=list)
    allow_headers: List[str] = Field(default_factory=list)


class Settings(BaseSettings):
    """Main application configuration settings."""

    host: str = "0.0.0.0"
    port: int = 8000
    max_pdf_mb: int = 100
    max_req_per_min: int = 0
    sync_timeout_sec: int = 60
    job_retention_hours: int = 24
    worker_pool_size: int = 2
    auth_enabled: bool = False
    api_keys: List[str] = Field(default_factory=list)
    sqlite_url: str = "sqlite:///./jobs.db"
    log_level: str = "INFO"
    log_json: bool = False
    metrics_enabled: bool = True
    cors: CORSSettings = Field(default_factory=CORSSettings)

    class Config:
        """Pydantic model configuration settings."""

        env_prefix = "ZF_"

    @property
    def max_pdf_bytes(self) -> int:
        """Convert maximum PDF size from megabytes to bytes."""
        return self.max_pdf_mb * 1024 * 1024


def get_settings() -> Settings:
    """Get an instance of the application settings."""
    return Settings()
