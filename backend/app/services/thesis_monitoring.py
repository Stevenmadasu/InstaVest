"""
InstaVest — Thesis Monitoring & Status Engine (SQL Persisted)
Evaluates monitored assumptions and updates thesis board states in PostgreSQL.
"""
import logging
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services import thesis_conviction_service
from app.db.models import ThesisBoard

logger = logging.getLogger(__name__)


def evaluate_board_assumptions(board_id: int, db: Session = None) -> dict:
    """
    Scan all assumptions on a thesis board. Check actual company metrics
    to flag violations, update status, and compile conviction updates.
    SQL Persisted.
    """
    opened_session = False
    if db is None:
        db = SessionLocal()
        opened_session = True
        
    try:
        res = thesis_conviction_service.evaluate_board_conviction(db, board_id)
        if "error" in res:
            logger.error(f"Error evaluating conviction for board {board_id}: {res['error']}")
        return res
    finally:
        if opened_session:
            db.close()


def refresh_all_thesis_boards(db: Session = None):
    """Trigger update loop across all registered thesis boards."""
    opened_session = False
    if db is None:
        db = SessionLocal()
        opened_session = True
        
    try:
        boards = db.query(ThesisBoard).all()
        for b in boards:
            evaluate_board_assumptions(b.id, db)
    finally:
        if opened_session:
            db.close()
