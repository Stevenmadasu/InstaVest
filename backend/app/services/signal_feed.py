"""
InstaVest — Signal Feed & Prioritization Engine (SQL Persisted)
Calculates multi-factor signal priority scores considering portfolio holdings,
watchlist presence, active thesis associations, and macro regime context.
"""
import logging
from typing import Any
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.db.models import Portfolio, Watchlist, ThesisBoard, Signal, SignalStateHistory
from app.services.regime_classification import classify_market_regime

logger = logging.getLogger(__name__)


def calculate_priority_score_sql(
    db: Session,
    sig: dict[str, Any],
    regime: dict[str, Any],
    user_id: int = 1
) -> float:
    """
    Apply multi-factor weighting to a raw signal querying SQL tables.
    """
    ticker = sig.get("ticker", "").upper()
    severity = sig.get("severity", "low").lower()
    direction = sig.get("direction", "neutral").lower()
    sig_type = sig.get("signal_type", "")
    
    # 1. Base Score
    severity_weights = {"critical": 80.0, "high": 60.0, "medium": 40.0, "low": 20.0}
    score = severity_weights.get(severity, 20.0)
    
    # 2. Portfolio Exposure Boost (+15)
    owned = False
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    for p in portfolios:
        if any(h.ticker.upper() == ticker for h in p.holdings):
            owned = True
            break
    if owned:
        score += 15.0
        
    # 3. Thesis Relevance Boost (+25)
    in_thesis = False
    boards = db.query(ThesisBoard).filter(ThesisBoard.user_id == user_id).all()
    for b in boards:
        if any(s.ticker.upper() == ticker for s in b.stocks):
            in_thesis = True
            break
    if in_thesis:
        score += 25.0
        
    # 4. Watchlist Boost (+10)
    watchlisted = False
    watchlists = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()
    for w in watchlists:
        if any(i.ticker.upper() == ticker for i in w.items):
            watchlisted = True
            break
    if watchlisted:
        score += 10.0
        
    # 5. Macro Regime Synergy
    regime_key = regime.get("regime", "")
    
    # In tightening/rate hike cycles, debt and leverage signals are highly critical
    if "tightening" in regime_key:
        if sig_type == "high_leverage" or sig_type == "margin_compression":
            score += 20.0
            
    # In risk-off recessions, negative fundamental signals are magnified
    elif "risk-off" in regime_key or "contracting" in regime_key:
        if direction == "negative":
            score += 25.0
        elif sig_type == "high_fcf_yield": # premium on real cash flows
            score += 15.0
            
    # In expansion / easing cycles, high-growth signals bubble up
    elif "easing" in regime_key:
        if sig_type == "revenue_acceleration" or sig_type == "exceptional_margins":
            score += 15.0

    return round(score, 1)


def get_prioritized_signal_feed(db: Session = None, ticker: str = None, limit: int = 50) -> list[dict[str, Any]]:
    """
    Compile and prioritize active signals across all companies using PostgreSQL.
    """
    from app.providers import get_provider
    from app.services.signal_engine import generate_signals
    
    opened_session = False
    if db is None:
        db = SessionLocal()
        opened_session = True
        
    try:
        provider = get_provider()
        regime = classify_market_regime(db)
        all_signals = []
        
        # Identify tickers to scan
        if ticker:
            scan_tickers = [ticker.upper()]
        else:
            # Scan portfolios, watchlists, and default list
            tickers_set = set(["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "AMD", "TSLA"])
            
            portfolios = db.query(Portfolio).all()
            for p in portfolios:
                tickers_set.update(h.ticker.upper() for h in p.holdings)
                
            watchlists = db.query(Watchlist).all()
            for w in watchlists:
                tickers_set.update(i.ticker.upper() for i in w.items)
                
            scan_tickers = list(tickers_set)
            
        # Generate raw signals
        for t in scan_tickers:
            metrics = provider.get_key_metrics(t)
            if metrics:
                metrics["ticker"] = t # Ensure ticker present for rule title builders
                sigs = generate_signals(metrics)
                all_signals.extend(sigs)
                
        # Apply priority scores & persist to database for signal auditing
        for sig in all_signals:
            score = calculate_priority_score_sql(db, sig, regime)
            sig["priority_score"] = score
            
            # Persist/Upsert to SQL signals table
            existing_sig = db.query(Signal).filter(
                Signal.ticker == sig["ticker"],
                Signal.signal_type == sig["signal_type"]
            ).first()
            
            if existing_sig:
                # Log state history if direction or priority changes significantly
                if existing_sig.priority_score != score:
                    history = SignalStateHistory(
                        ticker=sig["ticker"],
                        signal_type=sig["signal_type"],
                        prior_signal_strength=float(existing_sig.priority_score or 0.0),
                        current_signal_strength=float(score),
                        change_direction="up" if score > existing_sig.priority_score else "down",
                        interpretation=sig.get("description", "")
                    )
                    db.add(history)
                
                existing_sig.priority_score = score
                existing_sig.severity = sig.get("severity", "low")
                existing_sig.direction = sig.get("direction", "neutral")
                existing_sig.title = sig.get("title", "")
                existing_sig.explanation = sig.get("description", "")
            else:
                new_sig = Signal(
                    ticker=sig["ticker"],
                    signal_type=sig["signal_type"],
                    direction=sig.get("direction", "neutral"),
                    severity=sig.get("severity", "low"),
                    title=sig.get("title", ""),
                    explanation=sig.get("description", ""),
                    priority_score=score,
                    underlying_metrics_json=sig.get("metrics_payload", {})
                )
                db.add(new_sig)
        
        db.commit()
        
        # Sort descending by priority score
        ranked = sorted(all_signals, key=lambda s: s["priority_score"], reverse=True)
        return ranked[:limit]
    except Exception as e:
        logger.error(f"Failed to compile prioritized signals feed: {e}")
        return []
    finally:
        if opened_session:
            db.close()
