"""
InstaVest — Temporal Intelligence API Routes
Serves the prioritized intelligence stream and the pipeline trigger endpoint.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.intelligence_prioritization_service import compile_intelligence_stream
from app.services.daily_pipeline_service import run_daily_pipeline
from app.repositories import temporal_repository

router = APIRouter(prefix="/api/temporal", tags=["Temporal Intelligence"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/stream")
def get_intelligence_stream(
    limit: int = Query(default=30, ge=1, le=100),
    hours: int = Query(default=48, ge=1, le=168),
    db: Session = Depends(get_db),
):
    """
    Returns the prioritized intelligence narrative stream.
    Consumes precomputed temporal intelligence events and ranks them
    using cross-system importance scoring.
    """
    stream = compile_intelligence_stream(db, user_id=1, limit=limit, hours_lookback=hours)
    return {
        "stream": stream,
        "total_items": len(stream),
    }


@router.post("/pipeline/trigger")
def trigger_daily_pipeline(
    db: Session = Depends(get_db),
):
    """
    Manually triggers the full daily intelligence pipeline.
    Used for testing and on-demand refresh.
    Steps: macro → signals → thesis → snapshots → temporal → prioritization → cache
    """
    result = run_daily_pipeline(db=db, user_id=1)
    return result


@router.get("/snapshot/latest")
def get_latest_daily_snapshot(
    db: Session = Depends(get_db),
):
    """
    Returns the latest cached daily intelligence snapshot (precomputed).
    """
    snapshot = temporal_repository.get_latest_daily_intelligence_snapshot(db)
    if not snapshot:
        return {"error": "No daily intelligence snapshot available. Trigger the pipeline first."}

    return {
        "snapshot_date": str(snapshot.snapshot_date),
        "macro_state": snapshot.macro_state,
        "macro_summary": snapshot.macro_summary,
        "intelligence_feed": snapshot.intelligence_feed_json or [],
        "top_signals": snapshot.top_signals_json or [],
        "top_thesis_changes": snapshot.top_thesis_changes_json or [],
        "top_portfolio_changes": snapshot.top_portfolio_changes_json or [],
        "briefing_payload": snapshot.snapshot_payload_json,
        "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
    }
