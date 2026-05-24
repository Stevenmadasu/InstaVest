"""
InstaVest — Thesis Repository
SQL-backed thesis board persistence: boards, stocks, assumptions, timeline.
"""
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.db.models import (
    ThesisBoard, ThesisStock, ThesisAssumption,
    ThesisTimelineEvent, ThesisConvictionSnapshot,
)


# ─── Boards ───────────────────────────────────────

def list_boards(db: Session, user_id: int) -> list[ThesisBoard]:
    return (
        db.query(ThesisBoard)
        .filter(ThesisBoard.user_id == user_id)
        .options(
            joinedload(ThesisBoard.stocks),
            joinedload(ThesisBoard.assumptions),
        )
        .order_by(ThesisBoard.updated_at.desc())
        .all()
    )


def create_board(
    db: Session,
    user_id: int,
    title: str,
    description: str = None,
    time_horizon: str = "medium",
) -> ThesisBoard:
    board = ThesisBoard(
        user_id=user_id,
        title=title,
        description=description,
        time_horizon=time_horizon,
        conviction_score=50.0,
        status="stable",
    )
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


def get_board(db: Session, board_id: int) -> ThesisBoard | None:
    return (
        db.query(ThesisBoard)
        .filter(ThesisBoard.id == board_id)
        .options(
            joinedload(ThesisBoard.stocks),
            joinedload(ThesisBoard.assumptions),
            joinedload(ThesisBoard.timeline_events),
            joinedload(ThesisBoard.conviction_snapshots),
        )
        .first()
    )


def update_board_status(
    db: Session, board_id: int, status: str, conviction_score: float
) -> ThesisBoard | None:
    board = db.query(ThesisBoard).filter(ThesisBoard.id == board_id).first()
    if not board:
        return None
    board.status = status
    board.conviction_score = conviction_score
    board.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(board)
    return board


def delete_board(db: Session, board_id: int) -> bool:
    board = db.query(ThesisBoard).filter(ThesisBoard.id == board_id).first()
    if board:
        db.delete(board)
        db.commit()
        return True
    return False


# ─── Stocks ───────────────────────────────────────

def add_stock(db: Session, board_id: int, ticker: str) -> ThesisStock:
    ticker = ticker.upper().strip()
    existing = (
        db.query(ThesisStock)
        .filter(ThesisStock.thesis_board_id == board_id, ThesisStock.ticker == ticker)
        .first()
    )
    if existing:
        return existing
    stock = ThesisStock(thesis_board_id=board_id, ticker=ticker)
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


def remove_stock(db: Session, board_id: int, ticker: str) -> bool:
    ticker = ticker.upper().strip()
    stock = (
        db.query(ThesisStock)
        .filter(ThesisStock.thesis_board_id == board_id, ThesisStock.ticker == ticker)
        .first()
    )
    if stock:
        db.delete(stock)
        db.commit()
        return True
    return False


# ─── Timeline Events ─────────────────────────────

def add_timeline_event(
    db: Session,
    board_id: int,
    event_type: str,
    title: str,
    *,
    ticker: str = None,
    summary: str = None,
    what_changed: str = None,
    why_it_matters: str = None,
    impacted_assumptions_json: dict = None,
    severity: str = "medium",
) -> ThesisTimelineEvent:
    event = ThesisTimelineEvent(
        thesis_board_id=board_id,
        ticker=ticker,
        event_type=event_type,
        title=title,
        summary=summary,
        what_changed=what_changed,
        why_it_matters=why_it_matters,
        impacted_assumptions_json=impacted_assumptions_json,
        severity=severity,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_timeline(db: Session, board_id: int, limit: int = 50) -> list[ThesisTimelineEvent]:
    return (
        db.query(ThesisTimelineEvent)
        .filter(ThesisTimelineEvent.thesis_board_id == board_id)
        .order_by(ThesisTimelineEvent.created_at.desc())
        .limit(limit)
        .all()
    )


# ─── Conviction Snapshots ────────────────────────

def save_conviction_snapshot(
    db: Session,
    board_id: int,
    conviction_score: float,
    confidence_delta: float = None,
    supporting_signals_json: dict = None,
    weakening_signals_json: dict = None,
    regime_alignment: str = None,
) -> ThesisConvictionSnapshot:
    snap = ThesisConvictionSnapshot(
        thesis_board_id=board_id,
        conviction_score=conviction_score,
        confidence_delta=confidence_delta,
        supporting_signals_json=supporting_signals_json,
        weakening_signals_json=weakening_signals_json,
        regime_alignment=regime_alignment,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


def get_conviction_history(
    db: Session, board_id: int, limit: int = 30
) -> list[ThesisConvictionSnapshot]:
    return (
        db.query(ThesisConvictionSnapshot)
        .filter(ThesisConvictionSnapshot.thesis_board_id == board_id)
        .order_by(ThesisConvictionSnapshot.created_at.desc())
        .limit(limit)
        .all()
    )
