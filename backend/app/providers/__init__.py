"""
InstaVest — Abstract Data Provider Interface & Factory
All data providers must implement the DataProvider contract.
Use get_provider() to get the configured data source.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)


class DataProvider(ABC):
    """Base interface for all data source adapters."""

    @abstractmethod
    def get_company_profile(self, ticker: str) -> dict[str, Any]:
        """Return company metadata: name, sector, industry, description, market_cap, etc."""
        ...

    @abstractmethod
    def get_price_history(self, ticker: str, start: Optional[date] = None, end: Optional[date] = None) -> list[dict]:
        """Return list of {date, open, high, low, close, volume} dicts."""
        ...

    @abstractmethod
    def get_financial_statements(self, ticker: str) -> list[dict]:
        """Return normalized financial metrics: {fiscal_year, fiscal_period, statement_type, metric, value}."""
        ...

    @abstractmethod
    def get_filings(self, ticker: str) -> list[dict]:
        """Return SEC filings: {form_type, filing_date, accession_number, url}."""
        ...

    @abstractmethod
    def get_peer_group(self, ticker: str) -> list[str]:
        """Return list of peer tickers."""
        ...

    @abstractmethod
    def get_key_metrics(self, ticker: str) -> dict[str, Any]:
        """Return key valuation/financial metrics for modeling."""
        ...


# ─── Provider Factory ──────────────────────────────

_provider_instance: DataProvider | None = None


def get_provider() -> DataProvider:
    """
    Factory function that returns the configured data provider.
    Uses FMPProvider if FMP_API_KEY is set, otherwise falls back to MockProvider.
    Singleton pattern — same instance reused across the app.
    """
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    from app.config import settings

    if settings.has_fmp:
        from app.providers.fmp import FMPProvider
        _provider_instance = FMPProvider(settings.fmp_api_key)
        logger.info("✅ Using FMP live data provider")
    else:
        from app.providers.mock import MockProvider
        _provider_instance = MockProvider()
        logger.info("📦 Using mock data provider (no FMP_API_KEY)")

    return _provider_instance


def get_fred_provider():
    """Get FRED provider if configured, else None."""
    from app.config import settings
    if settings.has_fred:
        from app.providers.fred import FREDProvider
        return FREDProvider(settings.fred_api_key)
    return None


def get_ai_provider():
    """Get Anthropic AI provider if configured, else None."""
    from app.config import settings
    if settings.has_ai:
        from app.providers.anthropic_ai import AnthropicAIProvider
        return AnthropicAIProvider(settings.anthropic_api_key)
    return None


def get_sec_provider():
    """Get SEC EDGAR provider stub."""
    from app.providers.sec import SECProvider
    return SECProvider()
