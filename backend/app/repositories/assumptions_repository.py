"""
InstaVest — Assumptions Repository
CRUD for thesis assumptions with metric-linked evaluation state.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import ThesisAssumption


def add_assumption(
    db: Session,
    board_id: int,
    assumption_text: str,
    *,
    ticker: str = None,
    metric_key: str = None,
    operator: str = None,
    threshold_value: float = None,
) -> ThesisAssumption:
    asm = ThesisAssumption(
        thesis_board_id=board_id,
        ticker=ticker.upper().strip() if ticker else None,
        metric_key=metric_key,
        operator=operator,
        threshold_value=threshold_value,
        assumption_text=assumption_text,
        status="passing",
    )
    db.add(asm)
    db.commit()
    db.refresh(asm)
    return asm


def update_assumption_status(
    db: Session,
    assumption_id: int,
    status: str,
    current_value: float = None,
) -> ThesisAssumption | None:
    asm = db.query(ThesisAssumption).filter(ThesisAssumption.id == assumption_id).first()
    if not asm:
        return None
    asm.status = status
    asm.current_value = current_value
    asm.last_evaluated_at = datetime.utcnow()
    asm.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(asm)
    return asm


def list_assumptions(db: Session, board_id: int) -> list[ThesisAssumption]:
    return (
        db.query(ThesisAssumption)
        .filter(ThesisAssumption.thesis_board_id == board_id)
        .order_by(ThesisAssumption.created_at)
        .all()
    )


def get_assumption(db: Session, assumption_id: int) -> ThesisAssumption | None:
    return db.query(ThesisAssumption).filter(ThesisAssumption.id == assumption_id).first()


def delete_assumption(db: Session, assumption_id: int) -> bool:
    asm = db.query(ThesisAssumption).filter(ThesisAssumption.id == assumption_id).first()
    if asm:
        db.delete(asm)
        db.commit()
        return True
    return False
