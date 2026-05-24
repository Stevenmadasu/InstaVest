"""
InstaVest — FRED (Federal Reserve Economic Data) Provider
Fetches macroeconomic indicators for the dashboard and valuation context.
"""
import time
import logging
from typing import Any
import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://api.stlouisfed.org/fred"

# ─── Cache ──────────────────────────────────────────
_macro_cache: dict[str, dict[str, Any]] = {}


def _cache_get(key: str, ttl: int) -> Any | None:
    entry = _macro_cache.get(key)
    if entry and (time.time() - entry["ts"]) < ttl:
        return entry["data"]
    return None


def _cache_set(key: str, data: Any) -> None:
    _macro_cache[key] = {"data": data, "ts": time.time()}


# ─── Series Configuration ──────────────────────────

MACRO_SERIES = {
    "fed_funds_rate": {"id": "DFF", "label": "Fed Funds Rate", "unit": "%", "frequency": "daily"},
    "cpi_yoy": {"id": "CPIAUCSL", "label": "CPI (Inflation)", "unit": "%", "frequency": "monthly", "units": "pc1"},
    "treasury_10y": {"id": "DGS10", "label": "10-Year Treasury", "unit": "%", "frequency": "daily"},
    "treasury_2y": {"id": "DGS2", "label": "2-Year Treasury", "unit": "%", "frequency": "daily"},
    "unemployment": {"id": "UNRATE", "label": "Unemployment Rate", "unit": "%", "frequency": "monthly"},
    "gdp_growth": {"id": "A191RL1Q225SBEA", "label": "Real GDP Growth (QoQ)", "unit": "%", "frequency": "quarterly"},
}


class FREDProvider:
    """FRED API provider for macroeconomic data."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.Client(timeout=10.0)

    def _get_latest(self, series_id: str, units: str = "lin") -> str | None:
        """Fetch the latest observation for a FRED series."""
        try:
            resp = self.client.get(f"{BASE_URL}/series/observations", params={
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": 5,
                "sort_order": "desc",
                "units": units,
            })
            resp.raise_for_status()
            data = resp.json()
            observations = data.get("observations", [])
            # Return first non-missing value
            for obs in observations:
                val = obs.get("value", ".")
                if val != ".":
                    return val
            return None
        except Exception as e:
            logger.error(f"FRED request failed for {series_id}: {e}")
            return None

    def _get_series_history(self, series_id: str, limit: int = 12) -> list[dict]:
        """Fetch recent history for a FRED series."""
        try:
            resp = self.client.get(f"{BASE_URL}/series/observations", params={
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": limit,
                "sort_order": "desc",
            })
            resp.raise_for_status()
            data = resp.json()
            results = []
            for obs in data.get("observations", []):
                val = obs.get("value", ".")
                if val != ".":
                    results.append({"date": obs["date"], "value": float(val)})
            return list(reversed(results))
        except Exception as e:
            logger.error(f"FRED history request failed for {series_id}: {e}")
            return []

    def get_macro_snapshot(self) -> dict[str, Any]:
        """
        Get a snapshot of all key macro indicators.
        Returns a dict with current values and yield curve signal.
        """
        cache_key = "macro_snapshot"
        cached = _cache_get(cache_key, 3600)  # 1 hour
        if cached:
            return cached

        snapshot = {"indicators": [], "yield_curve": {}, "timestamp": time.time()}

        for key, config in MACRO_SERIES.items():
            val = self._get_latest(config["id"], units=config.get("units", "lin"))
            if val is not None:
                try:
                    numeric_val = float(val)
                except ValueError:
                    numeric_val = None

                snapshot["indicators"].append({
                    "key": key,
                    "label": config["label"],
                    "value": numeric_val,
                    "unit": config["unit"],
                    "series_id": config["id"],
                })

        # ─── Yield Curve Signal ──────────────────────
        t10 = next((i["value"] for i in snapshot["indicators"] if i["key"] == "treasury_10y"), None)
        t2 = next((i["value"] for i in snapshot["indicators"] if i["key"] == "treasury_2y"), None)

        if t10 is not None and t2 is not None:
            spread = round(t10 - t2, 2)
            snapshot["yield_curve"] = {
                "spread_10y_2y": spread,
                "signal": "normal" if spread > 0.5 else "flat" if spread > -0.1 else "inverted",
                "interpretation": (
                    "Normal yield curve — healthy growth expectations"
                    if spread > 0.5
                    else "Flat yield curve — uncertainty about growth outlook"
                    if spread > -0.1
                    else "Inverted yield curve — recession warning signal"
                ),
            }

        _cache_set(cache_key, snapshot)
        return snapshot

    def get_risk_free_rate(self) -> float:
        """Get current 10-year Treasury yield as risk-free rate for WACC calculations."""
        cache_key = "risk_free_rate"
        cached = _cache_get(cache_key, 3600)
        if cached is not None:
            return cached

        val = self._get_latest("DGS10")
        rate = float(val) if val else 4.25  # fallback
        _cache_set(cache_key, rate)
        return rate
