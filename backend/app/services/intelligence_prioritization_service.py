"""
InstaVest — Intelligence Prioritization Service
Ranks, sequences, and filters temporal intelligence events into an editorial narrative stream.
Suppresses low-value noise and elevates major inflections using multi-factor importance scoring.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.db.models import (
    TemporalIntelligenceEvent,
    ThesisBoard,
    Portfolio,
    Watchlist,
    Signal,
)
from app.repositories import temporal_repository

logger = logging.getLogger(__name__)

# Minimum importance threshold to appear in the feed
NOISE_THRESHOLD = 0.25

# Evolution type severity multipliers
EVOLUTION_WEIGHTS = {
    "reversing": 1.5,
    "accelerating": 1.3,
    "deteriorating": 1.2,
    "weakening": 1.15,
    "diverging": 1.1,
    "strengthening": 1.0,
    "improving": 0.9,
    "stabilizing": 0.7,
}

# Entity type base relevance
ENTITY_WEIGHTS = {
    "thesis": 1.4,
    "portfolio": 1.3,
    "ticker": 1.0,
    "signal": 0.9,
    "macro": 1.2,
}


def compute_composite_priority(
    event: TemporalIntelligenceEvent,
    db: Session,
    user_id: int = 1,
) -> float:
    """
    Compute a composite priority score for a temporal intelligence event
    combining importance_score, acceleration_score, evolution severity,
    entity relevance, and user context (watchlist, portfolio, thesis associations).
    """
    base = event.importance_score or 0.0
    accel = event.acceleration_score or 0.0

    # Evolution type multiplier
    evo_mult = EVOLUTION_WEIGHTS.get(event.evolution_type, 1.0)

    # Entity type multiplier
    entity_mult = ENTITY_WEIGHTS.get(event.entity_type, 1.0)

    # User context relevance boost
    context_boost = 0.0

    if event.entity_type == "ticker":
        ticker = event.entity_id.upper()
        # Check watchlist
        watchlists = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()
        for w in watchlists:
            if any(i.ticker.upper() == ticker for i in w.items):
                context_boost += 0.15
                break

        # Check portfolio
        portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
        for p in portfolios:
            if any(h.ticker.upper() == ticker for h in p.holdings):
                context_boost += 0.2
                break

        # Check thesis
        boards = db.query(ThesisBoard).filter(ThesisBoard.user_id == user_id).all()
        for b in boards:
            if any(s.ticker.upper() == ticker for s in b.stocks):
                context_boost += 0.25
                break

    elif event.entity_type == "thesis":
        # Thesis events are inherently high-context
        context_boost += 0.2

    elif event.entity_type == "portfolio":
        context_boost += 0.2

    # Composite formula
    composite = (base * 0.4 + accel * 0.3 + context_boost) * evo_mult * entity_mult
    return round(min(1.0, composite), 3)


def build_stream_item(event: TemporalIntelligenceEvent, priority: float) -> Dict[str, Any]:
    """
    Convert a TemporalIntelligenceEvent into a richly structured stream item
    suitable for the frontend narrative feed.
    """
    # Map evolution types to severity categories for the UI
    severity_map = {
        "reversing": "critical",
        "accelerating": "high",
        "deteriorating": "high",
        "weakening": "medium",
        "diverging": "medium",
        "strengthening": "positive",
        "improving": "positive",
        "stabilizing": "low",
    }
    severity = severity_map.get(event.evolution_type, "medium")

    # Map evolution types to signal direction
    direction_map = {
        "reversing": "negative",
        "deteriorating": "negative",
        "weakening": "negative",
        "diverging": "mixed",
        "accelerating": "positive",
        "strengthening": "positive",
        "improving": "positive",
        "stabilizing": "neutral",
    }
    direction = direction_map.get(event.evolution_type, "neutral")

    # Determine affected tickers from entity_id
    affected_tickers = []
    if event.entity_type == "ticker":
        affected_tickers = [event.entity_id.upper()]
    elif event.entity_type == "signal" and ":" in event.entity_id:
        affected_tickers = [event.entity_id.split(":")[0].upper()]

    return {
        "id": event.id,
        "timestamp": event.created_at.isoformat() if event.created_at else datetime.utcnow().isoformat(),
        "severity": severity,
        "direction": direction,
        "evolution_type": event.evolution_type,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "narrative": event.current_state_summary,
        "prior_state": event.prior_state_summary,
        "why_it_matters": event.why_it_matters,
        "implication": event.implication_summary,
        "affected_tickers": affected_tickers,
        "acceleration_score": event.acceleration_score,
        "importance_score": event.importance_score,
        "priority_score": priority,
    }


def compile_intelligence_stream(
    db: Session,
    user_id: int = 1,
    limit: int = 30,
    hours_lookback: int = 48,
) -> List[Dict[str, Any]]:
    """
    Compile a prioritized, narrative-sequenced intelligence stream from
    recent temporal intelligence events.

    Returns a list of stream items sorted by composite priority (descending),
    with noise filtered out.
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours_lookback)

    # Fetch recent events
    events = (
        db.query(TemporalIntelligenceEvent)
        .filter(TemporalIntelligenceEvent.created_at >= cutoff)
        .order_by(TemporalIntelligenceEvent.created_at.desc())
        .limit(200)  # pre-filter ceiling
        .all()
    )

    if not events:
        # If no recent events, fetch the most recent ones regardless of time
        events = (
            db.query(TemporalIntelligenceEvent)
            .order_by(TemporalIntelligenceEvent.created_at.desc())
            .limit(50)
            .all()
        )

    # Score and build stream items
    stream = []
    for event in events:
        priority = compute_composite_priority(event, db, user_id)

        # Suppress noise below threshold
        if priority < NOISE_THRESHOLD:
            continue

        item = build_stream_item(event, priority)
        stream.append(item)

    # Sort by priority descending, then by timestamp descending for ties
    stream.sort(key=lambda x: (-x["priority_score"], x["timestamp"]), reverse=False)
    stream.sort(key=lambda x: x["priority_score"], reverse=True)

    return stream[:limit]
