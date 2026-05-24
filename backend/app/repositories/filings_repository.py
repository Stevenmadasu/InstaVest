"""
InstaVest — Filings Repository
SQL-backed storage for SEC regulatory filings.
"""
from datetime import date as date_type, datetime
from sqlalchemy.orm import Session
from app.db.models import Filing


def upsert_filing(
    db: Session,
    ticker: str,
    form_type: str,
    filing_date: date_type,
    *,
    cik: str = None,
    accession_number: str = None,
    report_date: date_type = None,
    filing_url: str = None,
    raw_text_path: str = None,
    source: str = "sec_edgar",
) -> Filing:
    ticker = ticker.upper().strip()
    
    # If accession_number is provided, use it to deduplicate
    if accession_number:
        existing = db.query(Filing).filter(Filing.accession_number == accession_number).first()
        if existing:
            existing.ticker = ticker
            existing.cik = cik
            existing.form_type = form_type
            existing.filing_date = filing_date
            existing.report_date = report_date
            existing.filing_url = filing_url
            existing.raw_text_path = raw_text_path
            existing.source = source
            db.commit()
            db.refresh(existing)
            return existing

    # Fallback to unique ticker/form_type/date combo if no accession number
    existing_combo = (
        db.query(Filing)
        .filter(
            Filing.ticker == ticker,
            Filing.form_type == form_type,
            Filing.filing_date == filing_date,
        )
        .first()
    )
    if existing_combo:
        existing_combo.cik = cik
        existing_combo.accession_number = accession_number
        existing_combo.report_date = report_date
        existing_combo.filing_url = filing_url
        existing_combo.raw_text_path = raw_text_path
        existing_combo.source = source
        db.commit()
        db.refresh(existing_combo)
        return existing_combo

    filing = Filing(
        ticker=ticker,
        cik=cik,
        accession_number=accession_number,
        form_type=form_type,
        filing_date=filing_date,
        report_date=report_date,
        filing_url=filing_url,
        raw_text_path=raw_text_path,
        source=source,
    )
    db.add(filing)
    db.commit()
    db.refresh(filing)
    return filing


def get_filings(db: Session, ticker: str, limit: int = 50) -> list[Filing]:
    return (
        db.query(Filing)
        .filter(Filing.ticker == ticker.upper().strip())
        .order_by(Filing.filing_date.desc())
        .limit(limit)
        .all()
    )
