"""
InstaVest — FMP (Financial Modeling Prep) Data Provider
Live financial data via FMP /stable/ API endpoints.
All financial values are normalized to USD Millions to match model expectations.
"""
import time
import logging
from typing import Any, Optional
from datetime import date, timedelta
import httpx
from app.providers import DataProvider

logger = logging.getLogger(__name__)

# ─── In-Memory Cache ────────────────────────────────

_cache: dict[str, dict[str, Any]] = {}


def _cache_get(key: str, ttl: int) -> Any | None:
    """Return cached value if still valid, else None."""
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < ttl:
        return entry["data"]
    return None


def _cache_set(key: str, data: Any) -> None:
    """Store value in cache with current timestamp."""
    _cache[key] = {"data": data, "ts": time.time()}


# ─── FMP Provider ───────────────────────────────────

BASE_URL = "https://financialmodelingprep.com/stable"


class FMPProvider(DataProvider):
    """Live data provider using Financial Modeling Prep /stable/ API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.Client(timeout=15.0)

    def _get(self, endpoint: str, params: dict | None = None) -> Any:
        """Make authenticated GET request to FMP."""
        params = params or {}
        params["apikey"] = self.api_key
        url = f"{BASE_URL}/{endpoint}"
        try:
            resp = self.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            # FMP returns error objects sometimes
            if isinstance(data, dict) and "Error Message" in data:
                logger.warning(f"FMP error for {endpoint}: {data['Error Message']}")
                return None
            return data
        except httpx.HTTPError as e:
            logger.error(f"FMP request failed: {endpoint} — {e}")
            return None

    # ─── DataProvider Interface ──────────────────────

    def get_company_profile(self, ticker: str) -> dict[str, Any]:
        t = ticker.upper()
        cache_key = f"profile:{t}"
        cached = _cache_get(cache_key, 604800)  # 7 days
        if cached:
            return cached

        data = self._get("profile", {"symbol": t})
        if not data or not isinstance(data, list) or len(data) == 0:
            from app.providers.mock import MockProvider
            fallback = MockProvider()
            res = fallback.get_company_profile(ticker)
            if res:
                _cache_set(cache_key, res)
                return res
            return {}

        raw = data[0]
        result = {
            "ticker": t,
            "name": raw.get("companyName", ""),
            "sector": raw.get("sector", ""),
            "industry": raw.get("industry", ""),
            "exchange": raw.get("exchange", ""),
            "country": raw.get("country", ""),
            "description": raw.get("description", ""),
            "market_cap": raw.get("marketCap", 0),
            "shares_outstanding": int(raw.get("marketCap", 0) / raw.get("price", 1)) if raw.get("price") else 0,
            "price": raw.get("price", 0),
            "cik": raw.get("cik", ""),
            "website": raw.get("website", ""),
            "ceo": raw.get("ceo", ""),
            "image": raw.get("image", ""),
            "beta": raw.get("beta"),
            "volume": raw.get("volume", 0),
            "avg_volume": raw.get("averageVolume", 0),
            "range_52w": raw.get("range", ""),
        }
        _cache_set(cache_key, result)
        return result

    def get_price_history(self, ticker: str, start: Optional[date] = None, end: Optional[date] = None) -> list[dict]:
        t = ticker.upper()
        end_date = end or date.today()
        start_date = start or (end_date - timedelta(days=365))
        cache_key = f"prices:{t}:{start_date}:{end_date}"
        cached = _cache_get(cache_key, 3600)  # 1 hour
        if cached:
            return cached

        data = self._get("historical-price-eod/full", {
            "symbol": t,
            "from": str(start_date),
            "to": str(end_date),
        })
        if not data or not isinstance(data, list):
            from app.providers.mock import MockProvider
            fallback = MockProvider()
            res = fallback.get_price_history(ticker, start, end)
            if res:
                _cache_set(cache_key, res)
                return res
            return []

        # FMP returns newest first — reverse to chronological
        prices = []
        for bar in reversed(data):
            prices.append({
                "date": bar.get("date", ""),
                "open": bar.get("open", 0),
                "high": bar.get("high", 0),
                "low": bar.get("low", 0),
                "close": bar.get("close", 0),
                "adjusted_close": bar.get("close", 0),
                "volume": bar.get("volume", 0),
            })

        _cache_set(cache_key, prices)
        return prices

    def get_financial_statements(self, ticker: str) -> list[dict]:
        t = ticker.upper()
        cache_key = f"financials:{t}"
        cached = _cache_get(cache_key, 86400)  # 24 hours
        if cached:
            return cached

        income = self._get("income-statement", {"symbol": t, "period": "annual", "limit": 4}) or []
        balance = self._get("balance-sheet-statement", {"symbol": t, "period": "annual", "limit": 4}) or []
        cashflow = self._get("cash-flow-statement", {"symbol": t, "period": "annual", "limit": 4}) or []

        if not income or not balance or not cashflow:
            from app.providers.mock import MockProvider
            fallback = MockProvider()
            res = fallback.get_financial_statements(ticker)
            if res:
                _cache_set(cache_key, res)
                return res
            return []

        stmts = []

        # ─── Income Statement ────────────────────────
        for row in income:
            fy = row.get("fiscalYear", row.get("date", "")[:4])
            rev = row.get("revenue", 0)
            gp = row.get("grossProfit", 0)
            oi = row.get("operatingIncome", 0)
            ni = row.get("netIncome", 0)
            ebitda = row.get("ebitda", 0)
            gm = round(gp / rev * 100, 1) if rev else 0
            om = round(oi / rev * 100, 1) if rev else 0
            stmts.extend([
                {"fiscal_year": int(fy), "fiscal_period": "FY", "statement_type": "income", "metric": "revenue", "value": round(rev / 1e6), "unit": "USD_M"},
                {"fiscal_year": int(fy), "fiscal_period": "FY", "statement_type": "income", "metric": "gross_profit", "value": round(gp / 1e6), "unit": "USD_M"},
                {"fiscal_year": int(fy), "fiscal_period": "FY", "statement_type": "income", "metric": "operating_income", "value": round(oi / 1e6), "unit": "USD_M"},
                {"fiscal_year": int(fy), "fiscal_period": "FY", "statement_type": "income", "metric": "net_income", "value": round(ni / 1e6), "unit": "USD_M"},
                {"fiscal_year": int(fy), "fiscal_period": "FY", "statement_type": "income", "metric": "ebitda", "value": round(ebitda / 1e6), "unit": "USD_M"},
                {"fiscal_year": int(fy), "fiscal_period": "FY", "statement_type": "income", "metric": "gross_margin", "value": gm, "unit": "PCT"},
                {"fiscal_year": int(fy), "fiscal_period": "FY", "statement_type": "income", "metric": "operating_margin", "value": om, "unit": "PCT"},
            ])

        # ─── Balance Sheet ────────────────────────────
        for row in balance:
            fy = row.get("fiscalYear", row.get("date", "")[:4])
            ta = row.get("totalAssets", 0)
            td = (row.get("longTermDebt", 0) or 0) + (row.get("shortTermDebt", 0) or 0)
            cash = row.get("cashAndCashEquivalents", 0) or 0
            stmts.extend([
                {"fiscal_year": int(fy), "fiscal_period": "FY", "statement_type": "balance_sheet", "metric": "total_assets", "value": round(ta / 1e6), "unit": "USD_M"},
                {"fiscal_year": int(fy), "fiscal_period": "FY", "statement_type": "balance_sheet", "metric": "total_debt", "value": round(td / 1e6), "unit": "USD_M"},
                {"fiscal_year": int(fy), "fiscal_period": "FY", "statement_type": "balance_sheet", "metric": "cash_and_equivalents", "value": round(cash / 1e6), "unit": "USD_M"},
            ])

        # ─── Cash Flow ────────────────────────────────
        for row in cashflow:
            fy = row.get("fiscalYear", row.get("date", "")[:4])
            opcf = row.get("netCashProvidedByOperatingActivities", 0) or 0
            capex = abs(row.get("investmentsInPropertyPlantAndEquipment", 0) or 0)
            fcf = opcf - capex
            stmts.extend([
                {"fiscal_year": int(fy), "fiscal_period": "FY", "statement_type": "cash_flow", "metric": "free_cash_flow", "value": round(fcf / 1e6), "unit": "USD_M"},
                {"fiscal_year": int(fy), "fiscal_period": "FY", "statement_type": "cash_flow", "metric": "capital_expenditures", "value": round(capex / 1e6), "unit": "USD_M"},
            ])

        _cache_set(cache_key, stmts)
        return stmts

    def get_filings(self, ticker: str) -> list[dict]:
        """SEC filings — stub for now, returns basic info from profile."""
        t = ticker.upper()
        profile = self.get_company_profile(t)
        cik = profile.get("cik", "")
        return [
            {"form_type": "10-K", "filing_date": "See SEC EDGAR", "accession_number": f"{t}-10K", "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K"},
            {"form_type": "10-Q", "filing_date": "See SEC EDGAR", "accession_number": f"{t}-10Q", "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-Q"},
        ]

    def get_peer_group(self, ticker: str) -> list[str]:
        t = ticker.upper()
        cache_key = f"peers:{t}"
        cached = _cache_get(cache_key, 604800)  # 7 days
        if cached:
            return cached

        data = self._get("stock-peers", {"symbol": t})
        if not data or not isinstance(data, list):
            from app.providers.mock import MockProvider
            fallback = MockProvider()
            res = fallback.get_peer_group(ticker)
            if res:
                _cache_set(cache_key, res)
                return res
            return []

        # Filter to top peers by market cap, exclude tiny companies
        peers = []
        for item in data:
            sym = item.get("symbol", "")
            mkt = item.get("mktCap", 0)
            if sym and sym != t and mkt > 1_000_000_000:  # >$1B market cap
                peers.append(sym)
        peers = peers[:5]

        _cache_set(cache_key, peers)
        return peers

    def get_key_metrics(self, ticker: str) -> dict[str, Any]:
        t = ticker.upper()
        cache_key = f"metrics:{t}"
        cached = _cache_get(cache_key, 3600)  # 1 hour
        if cached:
            return cached

        profile = self.get_company_profile(t)
        if not profile:
            from app.providers.mock import MockProvider
            fallback = MockProvider()
            res = fallback.get_key_metrics(ticker)
            if res:
                _cache_set(cache_key, res)
                return res
            return {}

        ratios = self._get("ratios-ttm", {"symbol": t})
        ratios_data = ratios[0] if ratios and isinstance(ratios, list) and len(ratios) > 0 else {}

        if not ratios_data:
            from app.providers.mock import MockProvider
            fallback = MockProvider()
            res = fallback.get_key_metrics(ticker)
            if res:
                _cache_set(cache_key, res)
                return res
            return {}

        # Get financials for revenue growth calculation
        income = self._get("income-statement", {"symbol": t, "period": "annual", "limit": 2}) or []
        rev_current = income[0].get("revenue", 0) if len(income) > 0 else 0
        rev_prev = income[1].get("revenue", 0) if len(income) > 1 else 0
        rev_growth = round((rev_current / rev_prev - 1) * 100, 1) if rev_prev else 0

        # Extract key metrics
        mcap = profile.get("market_cap", 0)
        price = profile.get("price", 0)
        shares = profile.get("shares_outstanding", 1)

        # Calculate from ratios TTM
        pe = ratios_data.get("priceToEarningsRatioTTM")
        ev_val = ratios_data.get("enterpriseValueTTM", mcap)
        rev_ttm = round(rev_current / 1e6) if rev_current else 0  # to millions
        
        # Net income TTM from EPS
        eps = ratios_data.get("netIncomePerShareTTM", 0) or 0
        ni_ttm = round(eps * shares / 1e6) if shares else 0

        # FCF TTM from P/FCF ratio
        p_fcf = ratios_data.get("priceToFreeCashFlowRatioTTM")
        fcf_ttm = round(mcap / p_fcf / 1e6) if p_fcf and p_fcf > 0 else 0

        gm = ratios_data.get("grossProfitMarginTTM")
        om = ratios_data.get("operatingProfitMarginTTM")

        # Debt metrics from balance sheet cache or new fetch
        bs = self._get("balance-sheet-statement", {"symbol": t, "period": "annual", "limit": 1}) or []
        bs_data = bs[0] if bs else {}
        total_debt = ((bs_data.get("longTermDebt", 0) or 0) + (bs_data.get("shortTermDebt", 0) or 0))
        cash = bs_data.get("cashAndCashEquivalents", 0) or 0
        net_debt = round((total_debt - cash) / 1e6)

        # EBITDA from income statement
        ebitda_raw = income[0].get("ebitda", 0) if income else 0
        ebitda_ttm = round(ebitda_raw / 1e6)

        ev_m = round(ev_val / 1e6) if ev_val else round(mcap / 1e6 + net_debt)

        result = {
            "ticker": t,
            "price": price,
            "market_cap": mcap,
            "shares_outstanding": shares,
            "ev": ev_m,
            "revenue_ttm": rev_ttm,
            "ebitda_ttm": ebitda_ttm,
            "net_income_ttm": ni_ttm,
            "fcf_ttm": fcf_ttm,
            "ev_revenue": round(ev_m / rev_ttm, 1) if rev_ttm else None,
            "ev_ebitda": round(ev_m / ebitda_ttm, 1) if ebitda_ttm else None,
            "pe_ratio": round(pe, 1) if pe else None,
            "fcf_yield": round(fcf_ttm / (mcap / 1e6) * 100, 1) if mcap and fcf_ttm else 0,
            "gross_margin": round(gm * 100, 1) if gm else None,
            "operating_margin": round(om * 100, 1) if om else None,
            "revenue_growth": rev_growth,
            "net_debt": net_debt,
            "debt_to_ebitda": round(total_debt / 1e6 / ebitda_ttm, 1) if ebitda_ttm else None,
        }
        _cache_set(cache_key, result)
        return result

    # ─── Additional FMP-specific methods ─────────────

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Search for companies by name or ticker."""
        cache_key = f"search:{query.upper()}"
        cached = _cache_get(cache_key, 3600)
        if cached:
            return cached

        data = self._get("search", {"query": query, "limit": limit}) or []
        if not data:
            from app.providers.mock import MockProvider
            q_upper = query.upper()
            results = []
            from app.providers.mock import PROFILES
            for ticker, data_profile in PROFILES.items():
                if q_upper in ticker or query.lower() in data_profile["name"].lower():
                    results.append({
                        "ticker": ticker,
                        "name": data_profile["name"],
                        "exchange": data_profile["exchange"],
                        "sector": data_profile["sector"]
                    })
            _cache_set(cache_key, results)
            return results[:limit]

        results = []
        for item in data:
            if item.get("exchangeFullName", "").startswith(("NASDAQ", "NYSE", "AMEX")):
                results.append({
                    "ticker": item.get("symbol", ""),
                    "name": item.get("name", ""),
                    "exchange": item.get("exchangeFullName", ""),
                    "sector": "",  # Not in search results
                })
        _cache_set(cache_key, results)
        return results[:limit]
