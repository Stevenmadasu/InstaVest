"""
InstaVest — Metrics Repository
Persists company financial metrics with source provenance.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import CompanyMetric


def upsert_metric(
    db: Session,
    ticker: str,
    metric_key: str,
    metric_value: float,
    *,
    period: str = "TTM",
    source: str = "fmp",
    source_priority: int = 50,
) -> CompanyMetric:
    ticker = ticker.upper().strip()
    existing = (
        db.query(CompanyMetric)
        .filter(
            CompanyMetric.ticker == ticker,
            CompanyMetric.metric_key == metric_key,
            CompanyMetric.period == period,
            CompanyMetric.source == source,
        )
        .first()
    )
    if existing:
        existing.metric_value = metric_value
        existing.fetched_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    m = CompanyMetric(
        ticker=ticker,
        metric_key=metric_key,
        metric_value=metric_value,
        period=period,
        source=source,
        source_priority=source_priority,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def get_latest_metric(db: Session, ticker: str, metric_key: str) -> CompanyMetric | None:
    """Get the most recent value for a metric, preferring the highest-priority source."""
    return (
        db.query(CompanyMetric)
        .filter(
            CompanyMetric.ticker == ticker.upper().strip(),
            CompanyMetric.metric_key == metric_key,
        )
        .order_by(CompanyMetric.source_priority.asc(), CompanyMetric.fetched_at.desc())
        .first()
    )


def get_all_metrics(db: Session, ticker: str) -> list[CompanyMetric]:
    return (
        db.query(CompanyMetric)
        .filter(CompanyMetric.ticker == ticker.upper().strip())
        .order_by(CompanyMetric.metric_key, CompanyMetric.source_priority.asc())
        .all()
    )
