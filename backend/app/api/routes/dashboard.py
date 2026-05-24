"""Dashboard route — aggregated daily intelligence with macro data and checklist management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.providers import get_provider
from app.core.database import get_db
from app.services.morning_briefing import compile_morning_briefing
from app.repositories import briefing_repository

router = APIRouter()


class ChecklistToggle(BaseModel):
    completed: bool


@router.get("/morning-briefing")
def get_morning_briefing(force_refresh: bool = False, db: Session = Depends(get_db)):
    """Institutional, Bloomberg-style morning briefing daily package."""
    return compile_morning_briefing(db=db, force_refresh=force_refresh)


@router.post("/morning-briefing/checklist/{item_id}/toggle")
def toggle_checklist_item(item_id: int, data: ChecklistToggle, db: Session = Depends(get_db)):
    """Toggle a morning briefing checklist item's completion status."""
    item = briefing_repository.toggle_checklist_item(db, item_id, data.completed)
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return {"status": "success", "id": item.id, "completed": item.completed}


@router.get("")
def get_dashboard(db: Session = Depends(get_db)):
    """Morning briefing fallback dashboard data."""
    briefing = compile_morning_briefing(db=db)
    
    # Safeguard old frontend dashboard from crashing if it expects indicators list
    factors = briefing["macro_regime"]["factors"]
    macro_adapted = {
        **briefing["macro_regime"],
        "indicators": [
            {"key": "fed_funds_rate", "label": "Fed Funds Rate", "value": factors.get("fed_funds_rate", 5.25), "unit": "%", "series_id": "DFF"},
            {"key": "unemployment", "label": "Unemployment Rate", "value": factors.get("unemployment_rate", 3.9), "unit": "%", "series_id": "UNRATE"},
            {"key": "treasury_10y", "label": "10-Year Treasury", "value": factors.get("treasury_10y", 4.35), "unit": "%", "series_id": "DGS10"},
            {"key": "treasury_2y", "label": "2-Year Treasury", "value": factors.get("treasury_2y", 4.77), "unit": "%", "series_id": "DGS2"},
        ],
        "yield_curve": {
            "spread_10y_2y": factors.get("yield_curve_spread", -0.42),
            "signal": "normal" if factors.get("yield_curve_spread", -0.42) >= 0.5 else "flat" if factors.get("yield_curve_spread", -0.42) > -0.1 else "inverted",
            "interpretation": (
                "Normal yield curve — healthy growth expectations"
                if factors.get("yield_curve_spread", -0.42) >= 0.5
                else "Flat yield curve — uncertainty about growth outlook"
                if factors.get("yield_curve_spread", -0.42) > -0.1
                else "Inverted yield curve — recession warning signal"
            )
        }
    }
    
    # Adapt to support prior schema for older/fallback clients
    return {
        "greeting": "Good morning" if len(briefing["timeline_events"]) > 0 else "Welcome",
        "briefing": f"{len(briefing['prioritized_signals'])} signals detected across monitored companies.",
        "top_signals": briefing["prioritized_signals"][:10],
        "market_movers": [
            {
                "ticker": s["ticker"],
                "name": s["title"],
                "price": 0.0,
                "market_cap": 0.0,
                "revenue_growth": 0.0,
                "pe_ratio": None
            } for s in briefing["prioritized_signals"][:8]
        ],
        "watchlist_tickers": ["AAPL", "MSFT", "NVDA", "GOOGL"],
        "macro": macro_adapted,
    }
