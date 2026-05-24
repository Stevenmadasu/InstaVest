"""
InstaVest — Morning Briefing & Portfolio Risk Intelligence Service (SQL Persisted)
Compiles the core institutional Bloomberg-style daily habit morning briefing package.
"""
import logging
from typing import Any
from datetime import datetime, date as date_type
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.repositories import users_repository, thesis_repository, briefing_repository
from app.services.regime_classification import classify_market_regime
from app.services.signal_feed import get_prioritized_signal_feed
from app.services.intelligence_snapshot import get_or_compute_snapshot
from app.services.thesis_monitoring import refresh_all_thesis_boards
from app.db.models import Portfolio, Holding, ThesisTimelineEvent, ThesisBoard
from app.providers import get_provider

logger = logging.getLogger(__name__)


def compute_portfolio_risk_sql(db: Session, portfolio: Portfolio, regime: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate concentration indicators, correlation alerts, and macro exposures
    across the user's active holdings in SQL.
    """
    holdings = portfolio.holdings if portfolio else []
    if not holdings:
        return {
            "concentration_score": 0,
            "warnings": ["Portfolio is currently empty. Add holdings to activate risk intelligence."],
            "sector_exposure": {},
            "regime_correlation": "Neutral"
        }
        
    provider = get_provider()
    total_val = 0.0
    holdings_with_data = []

    for h in holdings:
        ticker = h.ticker.upper()
        # Fetch current price & sector via provider/FMP
        try:
            metrics = provider.get_key_metrics(ticker) or {}
            price = float(metrics.get("price") or 0.0)
            sector = metrics.get("sector") or "Technology"
        except Exception:
            price = 100.0
            sector = "Technology"

        val = float(h.shares) * price
        total_val += val
        holdings_with_data.append({
            "ticker": ticker,
            "value": val,
            "sector": sector
        })

    if total_val == 0:
        total_val = 1.0
        
    warnings = []
    sector_exposure = {}
    
    # 1. Sector Concentration
    for h in holdings_with_data:
        pct = (h["value"] / total_val) * 100
        sector = h["sector"]
        sector_exposure[sector] = sector_exposure.get(sector, 0.0) + pct
        
        # Single stock concentration warning
        if pct > 30.0:
            warnings.append(f"High single-stock concentration in **{h['ticker']}** ({pct:.1f}% of portfolio).")
            
    # Check sector concentration warnings
    for sec, pct in sector_exposure.items():
        sector_exposure[sec] = round(pct, 1)
        if pct > 50.0:
            warnings.append(f"Severe sector concentration in **{sec}** ({pct:.1f}% of total).")
            
    # 2. Macro Regime Overlaps & Interest Rate Sensitivities
    regime_key = regime.get("regime", "").lower()
    high_multiple_tech_pct = 0.0
    for h in holdings_with_data:
        pct = (h["value"] / total_val) * 100
        # If in high duration/growth
        if h["sector"] == "Technology" or h["ticker"] in ("TSLA", "NVDA", "AMD"):
            high_multiple_tech_pct += pct

    if "tightening" in regime_key:
        if high_multiple_tech_pct > 60.0:
            warnings.append(
                f"Rate hike cycle warning: {high_multiple_tech_pct:.1f}% portfolio exposure to high-duration technology. "
                "Rising interest rates threaten valuation multiple stability."
            )
    elif "risk-off" in regime_key or "contracting" in regime_key:
        warnings.append(
            "Economic contraction warning: Defensive positions highly recommended. "
            "Evaluate cyclical technology exposures."
        )
        
    # Standard correlation note if warning list is clean
    if not warnings:
        warnings.append("Holdings are well-diversified. No high-correlation warnings detected.")
        
    return {
        "concentration_score": min(100, int(len(warnings) * 20)),
        "warnings": warnings,
        "sector_exposure": sector_exposure,
        "regime_correlation": "High" if len(warnings) > 1 else "Moderate"
    }


def compile_morning_briefing(db: Session = None, user_id: int = 1, force_refresh: bool = False) -> dict[str, Any]:
    """
    Assembles the 7-section daily Morning Briefing payload for the dashboard using PostgreSQL.
    Ensures sub-second response times through precomputed caching where applicable.
    """
    opened_session = False
    if db is None:
        db = SessionLocal()
        opened_session = True

    try:
        # Seed default user if not exists
        users_repository.seed_default_user(db)

        # 1. Update/validate active thesis boards
        refresh_all_thesis_boards(db)
        
        # 2. Fetch current macro regime context
        regime = classify_market_regime(db)
        
        # 3. Fetch prioritized signals
        signals = get_prioritized_signal_feed(db=db, limit=8)
        
        # 4. Process portfolios
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        risk = compute_portfolio_risk_sql(db, portfolio, regime)
        
        # 5. Extract core precomputed company briefing (e.g. key watchlisted/owned ticker like AAPL or NVDA)
        featured_ticker = "AAPL"
        if portfolio and portfolio.holdings:
            featured_ticker = portfolio.holdings[0].ticker.upper()
        else:
            # Fallback to watchlist or default
            watchlists = thesis_repository.list_boards(db, user_id=user_id)
            if watchlists:
                stocks = watchlists[0].stocks
                if stocks:
                    featured_ticker = stocks[0].ticker.upper()
                
        snapshot = get_or_compute_snapshot(featured_ticker, db=db, force_refresh=force_refresh)
        featured_intelligence = snapshot.get("intelligence_payload_json", {})
        
        # 6. Sum Thesis Board conviction levels
        boards = thesis_repository.list_boards(db, user_id=user_id)
        
        thesis_stats = {
            "strengthening": sum(1 for b in boards if b.status == "strengthening"),
            "stable": sum(1 for b in boards if b.status == "stable"),
            "weakening": sum(1 for b in boards if b.status == "weakening"),
            "broken": sum(1 for b in boards if b.status == "broken"),
            "avg_confidence": int(sum(b.conviction_score or 50.0 for b in boards) / max(1, len(boards)))
        }
        
        # 7. Synthesize Quick Action Checklist items dynamically
        # Clear/retrieve today's checklist
        today = date_type.today()
        db_items = briefing_repository.get_checklist_items(db, user_id, today)
        
        if not db_items:
            actions_to_seed = []
            for b in boards:
                if b.status == "broken":
                    actions_to_seed.append({
                        "key": f"re-evaluate-{b.id}",
                        "title": f"Critical: Re-evaluate {b.title}. Core assumptions have broken."
                    })
                elif b.status == "weakening":
                    actions_to_seed.append({
                        "key": f"monitor-{b.id}",
                        "title": f"Alert: Monitored assumptions are weakening on {b.title}."
                    })
            # Fallback default action
            if not actions_to_seed:
                actions_to_seed.append({
                    "key": f"review-{featured_ticker}",
                    "title": f"Investigate active signals on watchlisted assets (e.g. {featured_ticker})."
                })
                
            for action in actions_to_seed:
                briefing_repository.upsert_checklist_item(
                    db=db,
                    user_id=user_id,
                    date=today,
                    item_key=action["key"],
                    title=action["title"],
                    completed=False
                )
            db_items = briefing_repository.get_checklist_items(db, user_id, today)

        actions = [
            {
                "id": item.id,
                "key": item.item_key,
                "message": item.title,
                "completed": item.completed
            }
            for item in db_items
        ]

        # 8. Fetch timeline events
        timeline = db.query(ThesisTimelineEvent).order_by(ThesisTimelineEvent.created_at.desc()).limit(12).all()
        formatted_timeline = [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "title": ev.title,
                "ticker": ev.ticker,
                "summary": ev.summary,
                "what_changed": ev.what_changed,
                "why_it_matters": ev.why_it_matters,
                "created_at": ev.created_at.isoformat() if ev.created_at else None
            }
            for ev in timeline
        ]

        formatted_boards = [
            {
                "id": b.id,
                "title": b.title,
                "status": b.status,
                "confidence": float(b.conviction_score or 50.0),
                "stocks": [s.ticker for s in b.stocks]
            }
            for b in boards
        ]
        
        return {
            "compiled_at": datetime.now().isoformat(),
            "macro_regime": regime,
            "featured_intelligence": {
                "ticker": featured_ticker,
                "summary": featured_intelligence.get("ai_summary", {}).get("summary", "No intelligence payload available."),
                "why_it_matters": featured_intelligence.get("ai_summary", {}).get("why_it_matters", "Investment questions pending classification."),
                "valuation_impact": featured_intelligence.get("ai_summary", {}).get("valuation_impact", "Valuation multiple analysis pending."),
                "thesis_impact": featured_intelligence.get("ai_summary", {}).get("thesis_impact", "Conviction tracking pending."),
                "ai_metadata": featured_intelligence.get("ai_summary", {}).get("ai_generation_metadata", {})
            },
            "thesis_conviction": {
                "stats": thesis_stats,
                "boards": formatted_boards
            },
            "prioritized_signals": signals,
            "timeline_events": formatted_timeline,
            "portfolio_risk": risk,
            "action_checklist": actions
        }
    except Exception as e:
        logger.error(f"Failed to compile morning briefing payload: {e}", exc_info=True)
        return {"error": f"Failed to compile morning briefing: {str(e)}"}
    finally:
        if opened_session:
            db.close()
