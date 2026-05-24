"""
InstaVest — Temporal Repository
SQL-backed storage for temporal intelligence events, thesis evolution histories, and signal temporal analyses.
"""
from datetime import date as date_type, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import (
    TemporalIntelligenceEvent,
    ThesisEvolutionHistory,
    SignalTemporalAnalysis,
    DailyIntelligenceSnapshot,
)

# ============================================
# TEMPORAL INTELLIGENCE EVENTS
# ============================================

def create_temporal_event(
    db: Session,
    entity_type: str,
    entity_id: str,
    prior_state_summary: Optional[str],
    current_state_summary: str,
    evolution_type: str,
    acceleration_score: float = 0.0,
    importance_score: float = 0.0,
    why_it_matters: Optional[str] = None,
    implication_summary: Optional[str] = None,
) -> TemporalIntelligenceEvent:
    event = TemporalIntelligenceEvent(
        entity_type=entity_type,
        entity_id=str(entity_id),
        prior_state_summary=prior_state_summary,
        current_state_summary=current_state_summary,
        evolution_type=evolution_type,
        acceleration_score=acceleration_score,
        importance_score=importance_score,
        why_it_matters=why_it_matters,
        implication_summary=implication_summary,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_temporal_events(
    db: Session,
    limit: int = 50,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> List[TemporalIntelligenceEvent]:
    query = db.query(TemporalIntelligenceEvent)
    if entity_type:
        query = query.filter(TemporalIntelligenceEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(TemporalIntelligenceEvent.entity_id == str(entity_id))
    return query.order_by(TemporalIntelligenceEvent.importance_score.desc(), TemporalIntelligenceEvent.created_at.desc()).limit(limit).all()


# ============================================
# THESIS EVOLUTION HISTORY
# ============================================

def create_thesis_evolution(
    db: Session,
    thesis_board_id: int,
    prior_conviction: Optional[float],
    current_conviction: float,
    evolution_summary: str,
    strongest_supporting_signal: Optional[str] = None,
    strongest_weakening_signal: Optional[str] = None,
    macro_alignment: Optional[str] = None,
) -> ThesisEvolutionHistory:
    history = ThesisEvolutionHistory(
        thesis_board_id=thesis_board_id,
        prior_conviction=prior_conviction,
        current_conviction=current_conviction,
        evolution_summary=evolution_summary,
        strongest_supporting_signal=strongest_supporting_signal,
        strongest_weakening_signal=strongest_weakening_signal,
        macro_alignment=macro_alignment,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def list_thesis_evolution(
    db: Session,
    thesis_board_id: int,
    limit: int = 50,
) -> List[ThesisEvolutionHistory]:
    return (
        db.query(ThesisEvolutionHistory)
        .filter(ThesisEvolutionHistory.thesis_board_id == thesis_board_id)
        .order_by(ThesisEvolutionHistory.created_at.desc())
        .limit(limit)
        .all()
    )


# ============================================
# SIGNAL TEMPORAL ANALYSIS
# ============================================

def upsert_signal_temporal_analysis(
    db: Session,
    ticker: str,
    signal_type: str,
    persistence_score: float = 0.0,
    acceleration_score: float = 0.0,
    regime_sensitivity: Optional[str] = None,
    confidence_trend: Optional[str] = None,
    interpretation: Optional[str] = None,
) -> SignalTemporalAnalysis:
    ticker = ticker.upper().strip()
    existing = (
        db.query(SignalTemporalAnalysis)
        .filter(
            SignalTemporalAnalysis.ticker == ticker,
            SignalTemporalAnalysis.signal_type == signal_type,
        )
        .first()
    )
    if existing:
        existing.persistence_score = persistence_score
        existing.acceleration_score = acceleration_score
        existing.regime_sensitivity = regime_sensitivity
        existing.confidence_trend = confidence_trend
        existing.interpretation = interpretation
        existing.created_at = datetime.utcnow()  # Update timestamp to show latest run
        db.commit()
        db.refresh(existing)
        return existing

    analysis = SignalTemporalAnalysis(
        ticker=ticker,
        signal_type=signal_type,
        persistence_score=persistence_score,
        acceleration_score=acceleration_score,
        regime_sensitivity=regime_sensitivity,
        confidence_trend=confidence_trend,
        interpretation=interpretation,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def list_signal_temporal_analyses(
    db: Session,
    ticker: Optional[str] = None,
    limit: int = 50,
) -> List[SignalTemporalAnalysis]:
    query = db.query(SignalTemporalAnalysis)
    if ticker:
        query = query.filter(SignalTemporalAnalysis.ticker == ticker.upper().strip())
    return query.order_by(SignalTemporalAnalysis.created_at.desc()).limit(limit).all()


# ============================================
# DAILY INTELLIGENCE SNAPSHOTS
# ============================================

def upsert_daily_intelligence_snapshot(
    db: Session,
    snapshot_date: date_type,
    snapshot_payload_json: Dict[str, Any],
    macro_state: Optional[str] = None,
    top_signals_json: Optional[Dict[str, Any]] = None,
    top_thesis_changes_json: Optional[Dict[str, Any]] = None,
    top_portfolio_changes_json: Optional[Dict[str, Any]] = None,
    macro_summary: Optional[str] = None,
    top_signal_changes_json: Optional[Dict[str, Any]] = None,
    intelligence_feed_json: Optional[List[Dict[str, Any]]] = None,
) -> DailyIntelligenceSnapshot:
    existing = (
        db.query(DailyIntelligenceSnapshot)
        .filter(DailyIntelligenceSnapshot.snapshot_date == snapshot_date)
        .first()
    )
    if existing:
        existing.snapshot_payload_json = snapshot_payload_json
        existing.macro_state = macro_state
        existing.top_signals_json = top_signals_json
        existing.top_thesis_changes_json = top_thesis_changes_json
        existing.top_portfolio_changes_json = top_portfolio_changes_json
        existing.macro_summary = macro_summary
        existing.top_signal_changes_json = top_signal_changes_json
        existing.intelligence_feed_json = intelligence_feed_json
        db.commit()
        db.refresh(existing)
        return existing

    snapshot = DailyIntelligenceSnapshot(
        snapshot_date=snapshot_date,
        snapshot_payload_json=snapshot_payload_json,
        macro_state=macro_state,
        top_signals_json=top_signals_json,
        top_thesis_changes_json=top_thesis_changes_json,
        top_portfolio_changes_json=top_portfolio_changes_json,
        macro_summary=macro_summary,
        top_signal_changes_json=top_signal_changes_json,
        intelligence_feed_json=intelligence_feed_json,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_latest_daily_intelligence_snapshot(db: Session) -> Optional[DailyIntelligenceSnapshot]:
    return (
        db.query(DailyIntelligenceSnapshot)
        .order_by(DailyIntelligenceSnapshot.snapshot_date.desc())
        .first()
    )
