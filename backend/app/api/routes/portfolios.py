"""Portfolio routes — SQL-backed database endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.db.models import Portfolio, Holding

router = APIRouter()


class PortfolioCreate(BaseModel):
    name: str


class HoldingAdd(BaseModel):
    ticker: str
    shares: float
    average_cost: float


@router.get("")
def list_portfolios(user_id: int = 1, db: Session = Depends(get_db)):
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    return [{"id": p.id, "name": p.name, "holdings_count": len(p.holdings)} for p in portfolios]


@router.post("")
def create_portfolio(data: PortfolioCreate, db: Session = Depends(get_db)):
    p = Portfolio(name=data.name, user_id=1)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name}


@router.get("/{portfolio_id}")
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    p = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    holdings_list = []
    for h in p.holdings:
        holdings_list.append({
            "id": h.id,
            "ticker": h.ticker,
            "shares": float(h.shares),
            "average_cost": float(h.average_cost),
            "current_price": float(h.average_cost)  # Fallback
        })
        
    return {
        "id": p.id,
        "name": p.name,
        "user_id": p.user_id,
        "holdings": holdings_list
    }


@router.post("/{portfolio_id}/holdings")
def add_holding(portfolio_id: int, data: HoldingAdd, db: Session = Depends(get_db)):
    p = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    ticker_upper = data.ticker.upper().strip()
    
    # Check if holding already exists in this portfolio
    existing = db.query(Holding).filter(
        Holding.portfolio_id == portfolio_id,
        Holding.ticker == ticker_upper
    ).first()
    
    if existing:
        existing.shares = data.shares
        existing.average_cost = data.average_cost
    else:
        new_holding = Holding(
            portfolio_id=portfolio_id,
            ticker=ticker_upper,
            shares=data.shares,
            average_cost=data.average_cost
        )
        db.add(new_holding)
        
    db.commit()
    return {"status": "added", "ticker": ticker_upper}
