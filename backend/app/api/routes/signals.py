"""Signal feed routes — powered by SQL prioritized signal engine."""
from fastapi import APIRouter, Query, Depends
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.signal_feed import get_prioritized_signal_feed

router = APIRouter()


@router.get("")
def get_signals(
    ticker: Optional[str] = None,
    severity: Optional[str] = None,
    direction: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Get prioritized signal feed across tracked companies using PostgreSQL."""
    ranked = get_prioritized_signal_feed(db=db, ticker=ticker, limit=limit)

    if severity:
        ranked = [s for s in ranked if s.get("severity") == severity]
    if direction:
        ranked = [s for s in ranked if s.get("direction") == direction]

    return ranked[:limit]
