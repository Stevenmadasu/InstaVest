"""Company routes — search, profile, research, refresh with SQL snapshots."""
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.company_brain import build_company_brain
from app.providers import get_provider
from app.core.database import get_db
from app.services.intelligence_snapshot import get_or_compute_snapshot

router = APIRouter()


@router.get("/search")
def search_companies(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Search companies by ticker or name."""
    provider = get_provider()

    # If FMP provider, use its search method
    if hasattr(provider, "search"):
        return provider.search(q)

    # Fallback: search mock PROFILES
    from app.providers.mock import PROFILES
    q_upper = q.upper()
    results = []
    for ticker, data in PROFILES.items():
        if q_upper in ticker or q.lower() in data["name"].lower():
            results.append({"ticker": ticker, "name": data["name"], "sector": data["sector"], "exchange": data["exchange"]})
    return results[:20]


@router.get("/trending")
def get_trending(db: Session = Depends(get_db)):
    """Get trending tickers for the dashboard."""
    provider = get_provider()

    # Use a curated watchlist of major tickers
    trending_tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "AMD", "TSLA"]
    results = []
    for t in trending_tickers:
        profile = provider.get_company_profile(t)
        if profile:
            results.append({
                "ticker": t,
                "name": profile.get("name", ""),
                "price": profile.get("price", 0),
                "sector": profile.get("sector", ""),
                "market_cap": profile.get("market_cap", 0),
            })
    return results


@router.get("/{ticker}")
def get_company(ticker: str, db: Session = Depends(get_db)):
    """Get company profile."""
    provider = get_provider()
    profile = provider.get_company_profile(ticker)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Company {ticker} not found")
    return profile


@router.get("/{ticker}/research")
def get_company_research(ticker: str, force_refresh: bool = False, db: Session = Depends(get_db)):
    """Get full Company Brain research payload — routed through the SQL snapshot cache layer."""
    snapshot = get_or_compute_snapshot(ticker, db=db, force_refresh=force_refresh)
    if "error" in snapshot:
        raise HTTPException(status_code=404, detail=snapshot["error"])
    return snapshot.get("intelligence_payload_json", snapshot)


@router.get("/{ticker}/metrics")
def get_key_metrics(ticker: str, db: Session = Depends(get_db)):
    """Get key valuation and financial metrics."""
    provider = get_provider()
    metrics = provider.get_key_metrics(ticker)
    if not metrics:
        raise HTTPException(status_code=404, detail=f"No metrics for {ticker}")
    return metrics


@router.get("/{ticker}/prices")
def get_prices(ticker: str, db: Session = Depends(get_db)):
    """Get historical prices."""
    provider = get_provider()
    prices = provider.get_price_history(ticker)
    return prices[-252:]


@router.get("/{ticker}/financials")
def get_financials(ticker: str, db: Session = Depends(get_db)):
    """Get financial statements."""
    provider = get_provider()
    return provider.get_financial_statements(ticker)


@router.get("/{ticker}/signals")
def get_company_signals(ticker: str, db: Session = Depends(get_db)):
    """Get signal stack for a company."""
    from app.services.signal_engine import generate_signals, prioritize_signals
    provider = get_provider()
    metrics = provider.get_key_metrics(ticker)
    if not metrics:
        raise HTTPException(status_code=404, detail=f"No data for {ticker}")
    signals = generate_signals(metrics)
    return prioritize_signals(signals)


@router.get("/{ticker}/peers")
def get_peers(ticker: str, db: Session = Depends(get_db)):
    """Get peer comparison analysis."""
    from app.models.peer_comparison import run_peer_comparison
    provider = get_provider()
    return run_peer_comparison(ticker, provider)
