"""
InstaVest — Intelligence Repository
SQL-backed storage for company and daily intelligence snapshots, and CompanyBrain aggregated profiles.
"""
from datetime import datetime, date as date_type
from sqlalchemy.orm import Session
from app.db.models import CompanyIntelligenceSnapshot, DailyIntelligenceSnapshot, CompanyBrain


# ─── Company Intelligence Snapshot ───────────────────────────────────

def save_company_snapshot(
    db: Session,
    ticker: str,
    snapshot_payload: dict,
    *,
    data_sources: dict = None,
    source_confidence: float = 1.0,
    source_discrepancies: dict = None,
    financial_version: str = "v1",
    signal_version: str = "v1",
    ai_version: str = "v1",
) -> CompanyIntelligenceSnapshot:
    ticker = ticker.upper().strip()
    
    # Optional: we can delete the older snapshot or just insert a new one.
    # Typically, keep history or overwrite. Let's overwrite or add new. Let's insert new history snapshot.
    snap = CompanyIntelligenceSnapshot(
        ticker=ticker,
        snapshot_payload_json=snapshot_payload,
        data_sources_json=data_sources,
        source_confidence=source_confidence,
        source_discrepancies_json=source_discrepancies,
        financial_version=financial_version,
        signal_version=signal_version,
        ai_version=ai_version,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


def get_latest_company_snapshot(db: Session, ticker: str) -> CompanyIntelligenceSnapshot | None:
    return (
        db.query(CompanyIntelligenceSnapshot)
        .filter(CompanyIntelligenceSnapshot.ticker == ticker.upper().strip())
        .order_by(CompanyIntelligenceSnapshot.created_at.desc())
        .first()
    )


# ─── Daily Intelligence Snapshot ─────────────────────────────────────

def save_daily_snapshot(
    db: Session,
    snapshot_date: date_type,
    snapshot_payload: dict,
    *,
    macro_state: str = None,
    top_signals: dict = None,
    top_thesis_changes: dict = None,
    top_portfolio_changes: dict = None,
) -> DailyIntelligenceSnapshot:
    # Overwrite if exists, since unique constraint is on snapshot_date
    existing = (
        db.query(DailyIntelligenceSnapshot)
        .filter(DailyIntelligenceSnapshot.snapshot_date == snapshot_date)
        .first()
    )
    if existing:
        existing.snapshot_payload_json = snapshot_payload
        existing.macro_state = macro_state
        existing.top_signals_json = top_signals
        existing.top_thesis_changes_json = top_thesis_changes
        existing.top_portfolio_changes_json = top_portfolio_changes
        existing.created_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
        
    snap = DailyIntelligenceSnapshot(
        snapshot_date=snapshot_date,
        snapshot_payload_json=snapshot_payload,
        macro_state=macro_state,
        top_signals_json=top_signals,
        top_thesis_changes_json=top_thesis_changes,
        top_portfolio_changes_json=top_portfolio_changes,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


def get_daily_snapshot(db: Session, snapshot_date: date_type) -> DailyIntelligenceSnapshot | None:
    return (
        db.query(DailyIntelligenceSnapshot)
        .filter(DailyIntelligenceSnapshot.snapshot_date == snapshot_date)
        .first()
    )


# ─── Company Brain (Aggregated Profiles) ────────────────────────────

def upsert_company_brain(
    db: Session,
    ticker: str,
    *,
    profile_json: dict = None,
    financials_json: dict = None,
    valuation_json: dict = None,
    signals_json: dict = None,
    peers_json: dict = None,
    risks_json: dict = None,
    catalysts_json: dict = None,
    ai_summary: str = None,
    ai_what_changed: str = None,
    ai_synthesis: str = None,
    market_expectations_json: dict = None,
    scenarios_json: dict = None,
    health_score_json: dict = None,
    confidence_score: float = None,
    thesis_status: str = None,
) -> CompanyBrain:
    ticker = ticker.upper().strip()
    brain = db.query(CompanyBrain).filter(CompanyBrain.ticker == ticker).first()
    
    if brain:
        if profile_json is not None: brain.profile_json = profile_json
        if financials_json is not None: brain.financials_json = financials_json
        if valuation_json is not None: brain.valuation_json = valuation_json
        if signals_json is not None: brain.signals_json = signals_json
        if peers_json is not None: brain.peers_json = peers_json
        if risks_json is not None: brain.risks_json = risks_json
        if catalysts_json is not None: brain.catalysts_json = catalysts_json
        if ai_summary is not None: brain.ai_summary = ai_summary
        if ai_what_changed is not None: brain.ai_what_changed = ai_what_changed
        if ai_synthesis is not None: brain.ai_synthesis = ai_synthesis
        if market_expectations_json is not None: brain.market_expectations_json = market_expectations_json
        if scenarios_json is not None: brain.scenarios_json = scenarios_json
        if health_score_json is not None: brain.health_score_json = health_score_json
        if confidence_score is not None: brain.confidence_score = confidence_score
        if thesis_status is not None: brain.thesis_status = thesis_status
        brain.last_refreshed = datetime.utcnow()
        brain.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(brain)
        return brain

    brain = CompanyBrain(
        ticker=ticker,
        profile_json=profile_json,
        financials_json=financials_json,
        valuation_json=valuation_json,
        signals_json=signals_json,
        peers_json=peers_json,
        risks_json=risks_json,
        catalysts_json=catalysts_json,
        ai_summary=ai_summary,
        ai_what_changed=ai_what_changed,
        ai_synthesis=ai_synthesis,
        market_expectations_json=market_expectations_json,
        scenarios_json=scenarios_json,
        health_score_json=health_score_json,
        confidence_score=confidence_score,
        thesis_status=thesis_status,
        last_refreshed=datetime.utcnow(),
    )
    db.add(brain)
    db.commit()
    db.refresh(brain)
    return brain


def get_company_brain(db: Session, ticker: str) -> CompanyBrain | None:
    return db.query(CompanyBrain).filter(CompanyBrain.ticker == ticker.upper().strip()).first()
