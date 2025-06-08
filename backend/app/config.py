from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class CORSSettings(BaseSettings):
    allow_origins: List[str] = Field(default_factory=list)
    allow_methods: List[str] = Field(default_factory=list)
    allow_headers: List[str] = Field(default_factory=list)


class Settings(BaseSettings):
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
        env_prefix = "ZF_"

    @property
    def max_pdf_bytes(self) -> int:
        return self.max_pdf_mb * 1024 * 1024


def get_settings() -> Settings:
    return Settings()
