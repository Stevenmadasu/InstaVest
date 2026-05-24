"""
InstaVest — Intelligence Snapshot Service (SQL Persisted)
Coordinates precomputations and handles caching of full Company Brain packages in PostgreSQL.
"""
import logging
from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session
from app.services.company_brain import build_company_brain
from app.core.database import SessionLocal
from app.repositories import intelligence_repository

logger = logging.getLogger(__name__)


def get_or_compute_snapshot(ticker: str, db: Session = None, force_refresh: bool = False) -> dict[str, Any]:
    """
    Get the precomputed Company Brain snapshot for a ticker from SQL.
    If it doesn't exist, calculate it, store it in PostgreSQL, and return.
    """
    ticker = ticker.upper().strip()
    
    opened_session = False
    if db is None:
        db = SessionLocal()
        opened_session = True
        
    try:
        # 1. Check SQL cache first
        if not force_refresh:
            existing = intelligence_repository.get_latest_company_snapshot(db, ticker)
            if existing:
                logger.info(f"⚡ SQL Cache hit: Serving precomputed snapshot for {ticker}")
                return {
                    "ticker": existing.ticker,
                    "snapshot_type": "standard_briefing",
                    "intelligence_payload_json": existing.snapshot_payload_json,
                    "price_version": None,
                    "financial_version": existing.financial_version,
                    "signal_version": existing.signal_version,
                    "ai_version": existing.ai_version,
                    "created_at": existing.created_at.isoformat() if existing.created_at else None
                }
        
        # 2. Cache miss or forced refresh: compute it
        logger.info(f"🌀 SQL Cache miss: Building precomputed intelligence snapshot for {ticker}...")
        brain_data = build_company_brain(ticker)
        if "error" in brain_data:
            return brain_data
        
        # Prepare snapshot version tokens
        price_val = brain_data.get('key_metrics', {}).get('price', 0)
        revenue_val = brain_data.get('key_metrics', {}).get('revenue_ttm', 0)
        signal_count = len(brain_data.get('signals', []))
        
        ai_meta = brain_data.get("ai_summary", {}).get("ai_generation_metadata", {}) if isinstance(brain_data.get("ai_summary"), dict) else {}
        ai_ver = ai_meta.get("prompt_template_version", "fallback-1.0") if ai_meta else "legacy-1.0"
        
        # Save snapshot using the SQL intelligence repository
        snapshot_obj = intelligence_repository.save_company_snapshot(
            db=db,
            ticker=ticker,
            snapshot_payload=brain_data,
            financial_version=f"rev-{revenue_val}",
            signal_version=f"sigCount-{signal_count}",
            ai_version=ai_ver
        )
        
        return {
            "ticker": snapshot_obj.ticker,
            "snapshot_type": "standard_briefing",
            "intelligence_payload_json": snapshot_obj.snapshot_payload_json,
            "price_version": None,
            "financial_version": snapshot_obj.financial_version,
            "signal_version": snapshot_obj.signal_version,
            "ai_version": snapshot_obj.ai_version,
            "created_at": snapshot_obj.created_at.isoformat() if snapshot_obj.created_at else None
        }
        
    except Exception as e:
        logger.error(f"Error computing intelligence snapshot for {ticker}: {e}")
        return {"error": f"Failed to compute intelligence snapshot for {ticker}: {str(e)}"}
    finally:
        if opened_session:
            db.close()
