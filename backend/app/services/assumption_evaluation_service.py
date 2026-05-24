"""
InstaVest — Assumption Evaluation Service
Deterministic mathematical evaluation of monitored metrics against defined thresholds.
Classifies assumption status as passing (+3 conviction impact), warning (-5 impact),
failing (-15 impact), or unavailable (-2 impact).
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import ThesisAssumption
from app.repositories import metrics_repository, assumptions_repository
from app.providers import get_provider

logger = logging.getLogger(__name__)


def evaluate_assumption(db: Session, assumption: ThesisAssumption) -> dict:
    """
    Evaluate a single thesis assumption against live/cached company metrics.
    Updates the assumption's current_value, status, and last_evaluated_at.
    """
    ticker = assumption.ticker
    metric_key = assumption.metric_key
    operator = assumption.operator or ">"
    threshold = assumption.threshold_value

    if not ticker or not metric_key:
        # Qualitative assumption (non-deterministic)
        return {
            "assumption_id": assumption.id,
            "status": assumption.status or "passing",
            "current_value": None,
            "delta": 3 if (assumption.status == "passing" or not assumption.status) else -5,
            "error": "Non-metric assumption"
        }

    # 1. Fetch metric value (check SQL cache first, fallback to provider)
    metric_val = None
    metric_record = metrics_repository.get_latest_metric(db, ticker, metric_key)
    
    if metric_record:
        # Check freshness (e.g., within last 24 hours)
        delta = datetime.utcnow() - metric_record.fetched_at
        if delta.total_seconds() < 86400: # 24 hours
            metric_val = metric_record.metric_value
            logger.info(f"Using cached metric {metric_key} for {ticker}: {metric_val}")
            
    if metric_val is None:
        try:
            provider = get_provider()
            metrics = provider.get_key_metrics(ticker)
            if metrics and metric_key in metrics:
                metric_val = float(metrics[metric_key])
                # Save to database cache
                metrics_repository.upsert_metric(
                    db=db,
                    ticker=ticker,
                    metric_key=metric_key,
                    metric_value=metric_val,
                    source="fmp"
                )
                logger.info(f"Fetched and cached metric {metric_key} for {ticker}: {metric_val}")
        except Exception as e:
            logger.error(f"Error fetching metric {metric_key} for {ticker}: {e}")

    # 2. If metric remains unavailable, assign status 'unavailable'
    if metric_val is None:
        # Use previous value if available, else None
        prior_val = assumption.current_value
        assumptions_repository.update_assumption_status(
            db,
            assumption_id=assumption.id,
            status="unavailable",
            current_value=prior_val
        )
        return {
            "assumption_id": assumption.id,
            "status": "unavailable",
            "current_value": prior_val,
            "delta": -2,
            "error": "Metric unavailable"
        }

    # 3. Deterministic soft-margin evaluation
    status = "passing"
    
    if operator == ">":
        if metric_val > threshold:
            status = "passing"
        elif metric_val >= threshold * 0.85:
            status = "warning"
        else:
            status = "failing"
    elif operator == ">=":
        if metric_val >= threshold:
            status = "passing"
        elif metric_val >= threshold * 0.85:
            status = "warning"
        else:
            status = "failing"
    elif operator == "<":
        if metric_val < threshold:
            status = "passing"
        elif metric_val <= threshold * 1.15:
            status = "warning"
        else:
            status = "failing"
    elif operator == "<=":
        if metric_val <= threshold:
            status = "passing"
        elif metric_val <= threshold * 1.15:
            status = "warning"
        else:
            status = "failing"
    elif operator in ("=", "=="):
        diff_ratio = abs(metric_val - threshold) / max(abs(threshold), 1.0)
        if diff_ratio < 1e-4:
            status = "passing"
        elif diff_ratio < 0.15:
            status = "warning"
        else:
            status = "failing"
    else:
        # Fallback
        if metric_val >= threshold:
            status = "passing"
        else:
            status = "failing"

    # Define score/conviction impacts
    delta_map = {
        "passing": 3.0,
        "warning": -5.0,
        "failing": -15.0,
        "unavailable": -2.0
    }
    
    # 4. Update status in database
    assumptions_repository.update_assumption_status(
        db,
        assumption_id=assumption.id,
        status=status,
        current_value=metric_val
    )

    return {
        "assumption_id": assumption.id,
        "status": status,
        "current_value": metric_val,
        "delta": delta_map[status]
    }
