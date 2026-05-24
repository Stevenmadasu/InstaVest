"""
InstaVest — Application Configuration
Loads environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://instavest:instavest@db:5432/instavest"

    # App
    app_env: str = "development"
    log_level: str = "info"
    backend_port: int = 8000
    backend_cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:5173"

    # AI
    anthropic_api_key: Optional[str] = None

    # Data Providers
    fmp_api_key: Optional[str] = None
    fred_api_key: Optional[str] = None

    # Cache TTLs (seconds)
    cache_ttl_prices: int = 3600         # 1 hour
    cache_ttl_financials: int = 86400    # 24 hours
    cache_ttl_profile: int = 604800      # 7 days
    cache_ttl_ratios: int = 3600         # 1 hour
    cache_ttl_macro: int = 3600          # 1 hour

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",")]

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    @property
    def has_ai(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_fmp(self) -> bool:
        return bool(self.fmp_api_key)

    @property
    def has_fred(self) -> bool:
        return bool(self.fred_api_key)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
