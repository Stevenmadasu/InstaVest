"""Thesis board routes — SQL-backed database endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import get_db
from app.repositories import thesis_repository, assumptions_repository
from app.services.thesis_monitoring import evaluate_board_assumptions

router = APIRouter()


class ThesisBoardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    time_horizon: Optional[str] = "medium"


class AssumptionAdd(BaseModel):
    assumption_text: str
    linked_metric: Optional[str] = None
    ticker: Optional[str] = None
    operator: Optional[str] = ">="
    threshold_value: Optional[float] = 0.0


@router.get("")
def list_thesis_boards(user_id: int = 1, db: Session = Depends(get_db)):
    boards = thesis_repository.list_boards(db, user_id=user_id)
    return [
        {
            "id": b.id,
            "title": b.title,
            "status": b.status,
            "confidence": float(b.conviction_score or 50.0),
            "stocks": [s.ticker for s in b.stocks]
        }
        for b in boards
    ]


@router.post("")
def create_thesis_board(data: ThesisBoardCreate, db: Session = Depends(get_db)):
    board = thesis_repository.create_board(
        db=db,
        user_id=1,
        title=data.title,
        description=data.description,
        time_horizon=data.time_horizon
    )
    return {"id": board.id, "title": board.title}


@router.get("/{board_id}")
def get_thesis_board(board_id: int, db: Session = Depends(get_db)):
    board = thesis_repository.get_board(db, board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Thesis board not found")
        
    assumptions_list = []
    for asm in board.assumptions:
        assumptions_list.append({
            "id": asm.id,
            "text": asm.assumption_text,
            "status": asm.status,
            "metric": asm.metric_key or "operating_margin",
            "linked_metric": asm.metric_key or "operating_margin",
            "ticker": asm.ticker,
            "operator": asm.operator,
            "threshold_value": float(asm.threshold_value) if asm.threshold_value is not None else None,
            "current_value": float(asm.current_value) if asm.current_value is not None else None
        })
        
    events = [
        {
            "id": ev.id,
            "event_type": ev.event_type,
            "title": ev.title,
            "ticker": ev.ticker,
            "summary": ev.summary,
            "what_changed": ev.what_changed,
            "why_it_matters": ev.why_it_matters,
            "created_at": ev.created_at.isoformat() if ev.created_at else None
        }
        for ev in board.timeline_events
    ]
    
    return {
        "id": board.id,
        "title": board.title,
        "description": board.description,
        "status": board.status,
        "confidence": float(board.conviction_score or 50.0),
        "time_horizon": board.time_horizon,
        "user_id": board.user_id,
        "stocks": [s.ticker for s in board.stocks],
        "assumptions": assumptions_list,
        "timeline": events
    }


@router.post("/{board_id}/assumptions")
def add_assumption(board_id: int, data: AssumptionAdd, db: Session = Depends(get_db)):
    board = thesis_repository.get_board(db, board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Thesis board not found")
        
    metric_map = {
        "revenue growth": "revenue_growth",
        "operating margin": "operating_margin",
        "fcf yield": "fcf_yield",
        "debt to ebitda": "debt_to_ebitda",
        "gross margin": "gross_margin"
    }
    raw_metric = (data.linked_metric or "operating_margin").lower().strip()
    linked_metric = metric_map.get(raw_metric, raw_metric)
    
    # Try to extract a ticker from board stocks if not provided
    ticker = data.ticker
    if not ticker and board.stocks:
        ticker = board.stocks[0].ticker
        
    asm = assumptions_repository.add_assumption(
        db=db,
        board_id=board_id,
        assumption_text=data.assumption_text,
        ticker=ticker,
        metric_key=linked_metric,
        operator=data.operator,
        threshold_value=data.threshold_value
    )
    
    # Trigger active thesis assessment
    evaluate_board_assumptions(board_id, db)
    return {"status": "added", "id": asm.id}


@router.post("/{board_id}/stocks")
def link_stock_to_board(board_id: int, ticker: str, db: Session = Depends(get_db)):
    board = thesis_repository.get_board(db, board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Thesis board not found")
    ticker_upper = ticker.upper().strip()
    thesis_repository.add_stock(db, board_id, ticker_upper)
    
    # Trigger active thesis assessment
    evaluate_board_assumptions(board_id, db)
    
    # Re-fetch board to return updated stocks list
    board = thesis_repository.get_board(db, board_id)
    return {"status": "linked", "stocks": [s.ticker for s in board.stocks]}
