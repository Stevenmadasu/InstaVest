"""
InstaVest — Thesis Conviction Service
Evaluates the collective conviction score of a thesis board by aggregating
individual assumption evaluation statuses and managing status updates, conviction historical snapshots,
timeline events, and state change transitions.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import ThesisBoard
from app.repositories import thesis_repository, assumptions_repository
from app.services import assumption_evaluation_service, state_change_service
from app.providers import get_ai_provider, get_provider

logger = logging.getLogger(__name__)


def evaluate_board_conviction(db: Session, board_id: int) -> dict:
    """
    Evaluate all assumptions, compute the new composite conviction score,
    update board status, record snapshots, state changes, and timeline events.
    """
    board = thesis_repository.get_board(db, board_id)
    if not board:
        return {"error": "Thesis board not found"}

    prior_score = board.conviction_score or 50.0
    prior_status = board.status or "stable"

    # 1. Evaluate all linked assumptions
    assumptions = board.assumptions
    evaluation_results = []
    total_delta = 0.0

    supporting_signals = []
    weakening_signals = []

    for asm in assumptions:
        res = assumption_evaluation_service.evaluate_assumption(db, asm)
        evaluation_results.append(res)
        total_delta += res["delta"]

        # Track supporting vs weakening for conviction snapshot
        if res["status"] == "passing":
            supporting_signals.append({
                "assumption_id": asm.id,
                "text": asm.assumption_text,
                "value": res["current_value"]
            })
        elif res["status"] in ("warning", "failing"):
            weakening_signals.append({
                "assumption_id": asm.id,
                "text": asm.assumption_text,
                "value": res["current_value"],
                "status": res["status"]
            })

    # 2. Calculate composite conviction score (Base 50.0 + sum of deltas, clamped to 0-100)
    new_score = prior_score
    if assumptions:
        new_score = 50.0 + total_delta
        new_score = max(0.0, min(100.0, new_score))

    # 3. Determine new board status based on the conviction score
    # Spec: 80-100 = strengthening, 60-79 = stable, 40-59 = weakening, 0-39 = broken
    if new_score >= 80.0:
        new_status = "strengthening"
    elif new_score >= 60.0:
        new_status = "stable"
    elif new_score >= 40.0:
        new_status = "weakening"
    else:
        new_status = "broken"

    # 4. Save Thesis Conviction Snapshot
    confidence_delta = new_score - prior_score
    thesis_repository.save_conviction_snapshot(
        db=db,
        board_id=board_id,
        conviction_score=new_score,
        confidence_delta=confidence_delta,
        supporting_signals_json={"items": supporting_signals},
        weakening_signals_json={"items": weakening_signals},
        regime_alignment="neutral"  # Can be enhanced later
    )

    # 5. Update board status & score
    thesis_repository.update_board_status(db, board_id, new_status, new_score)

    # 6. If status or score shifted significantly, record events
    status_changed = (prior_status != new_status)
    score_shifted = (abs(confidence_delta) >= 5.0)

    if status_changed or score_shifted or len(evaluation_results) > 0:
        # Create user-facing timeline event description
        title = f"Conviction Shift: {board.title} turned {new_status.upper()}"
        summary = f"Evaluated thesis conviction: {len(evaluation_results)} assumptions evaluated."
        what_changed = "\n".join(
            f"- Assumption '{asm.assumption_text}' status: {res['status']} (value: {res['current_value']})"
            for asm, res in zip(assumptions, evaluation_results)
        )
        
        stocks_list = [s.ticker for s in board.stocks]
        why_it_matters = (
            f"This alters the fundamental conviction profile of your monitored holdings: {', '.join(stocks_list)}. "
            f"A score delta of {confidence_delta:+.1f} indicates shifting operational or macro support."
        )

        # Optional: AI enrichment if available
        ai = get_ai_provider()
        if ai and stocks_list:
            try:
                # Trigger quick AI analysis of the conviction change
                provider = get_provider()
                metrics = provider.get_key_metrics(stocks_list[0])
                # Mock schema representation for the AI prompt
                board_dict = {
                    "title": board.title,
                    "description": board.description,
                    "status": new_status,
                    "confidence": new_score
                }
                ai_eval = ai.evaluate_thesis(board_dict, metrics)
                if ai_eval and "reasoning" in ai_eval:
                    why_it_matters = ai_eval["reasoning"]
            except Exception as e:
                logger.warning(f"AI enrichment failed: {e}")

        # Add to board timeline
        thesis_repository.add_timeline_event(
            db=db,
            board_id=board_id,
            event_type="conviction_shift" if status_changed else "assumption_check",
            title=title,
            ticker=stocks_list[0] if stocks_list else None,
            summary=summary,
            what_changed=what_changed,
            why_it_matters=why_it_matters,
            impacted_assumptions_json={"changes": evaluation_results},
            severity="high" if new_status in ("weakening", "broken") else "medium"
        )

        # Add generic state change event
        state_change_service.record_state_change(
            db=db,
            entity_type="ThesisBoard",
            entity_id=board_id,
            prior_state={"score": prior_score, "status": prior_status},
            current_state={"score": new_score, "status": new_status},
            delta_summary=f"Conviction score shifted from {prior_score:.1f} to {new_score:.1f} ({new_status})",
            why_it_matters=why_it_matters,
            severity="high" if new_status in ("weakening", "broken") else "medium"
        )

    return {
        "board_id": board_id,
        "status": new_status,
        "conviction_score": new_score,
        "confidence_delta": confidence_delta,
        "evaluations": evaluation_results
    }
