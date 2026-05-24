"""
InstaVest — State Change Detection & Service
Detects and records critical state change events across conviction boards, signals, and portfolios.
"""
import logging
from sqlalchemy.orm import Session
from app.db.models import StateChangeEvent

logger = logging.getLogger(__name__)


def record_state_change(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    prior_state: dict,
    current_state: dict,
    delta_summary: str,
    why_it_matters: str = None,
    severity: str = "medium",
) -> StateChangeEvent:
    """
    Log and persist a significant state change event.
    """
    event = StateChangeEvent(
        entity_type=entity_type,
        entity_id=entity_id,
        prior_state_json=prior_state,
        current_state_json=current_state,
        delta_summary=delta_summary,
        why_it_matters=why_it_matters,
        severity=severity,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info(f"Recorded state change for {entity_type} {entity_id}: {delta_summary}")
    return event
