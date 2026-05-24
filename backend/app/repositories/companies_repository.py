"""
InstaVest — Companies Repository
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import Company


def get_or_create_company(
    db: Session,
    ticker: str,
    name: str,
    *,
    cik: str = None,
    sector: str = None,
    industry: str = None,
    exchange: str = None,
    description: str = None,
    source: str = "fmp",
) -> Company:
    ticker = ticker.upper().strip()
    company = db.query(Company).filter(Company.ticker == ticker).first()
    if company:
        return company
    company = Company(
        ticker=ticker,
        name=name,
        cik=cik,
        sector=sector,
        industry=industry,
        exchange=exchange,
        description=description,
        source=source,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def get_company(db: Session, ticker: str) -> Company | None:
    return db.query(Company).filter(Company.ticker == ticker.upper().strip()).first()


def list_companies(db: Session, limit: int = 100) -> list[Company]:
    return db.query(Company).order_by(Company.ticker).limit(limit).all()
