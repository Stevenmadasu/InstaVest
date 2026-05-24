"""
InstaVest — Daily Intelligence Pipeline Service
Orchestrates the full overnight/scheduled intelligence generation pipeline:

1. Refresh provider data & rerun signals
2. Rerun thesis conviction evaluation across all boards
3. Rerun temporal intelligence engine
4. Run intelligence prioritization & stream compilation
5. Generate the daily intelligence snapshot cache
6. Compile the morning briefing payload

Designed to be triggered on-demand or via a scheduled job.
All outputs are precomputed and cached — the frontend consumes snapshots only.
"""
import logging
from datetime import datetime, date as date_type
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.regime_classification import classify_market_regime
from app.services.signal_feed import get_prioritized_signal_feed
from app.services.thesis_monitoring import refresh_all_thesis_boards
from app.services.intelligence_snapshot import get_or_compute_snapshot
from app.services.temporal_intelligence_service import run_temporal_analysis
from app.services.intelligence_prioritization_service import compile_intelligence_stream
from app.services.morning_briefing import compile_morning_briefing
from app.repositories import temporal_repository, thesis_repository
from app.db.models import Watchlist, Portfolio, ThesisBoard

logger = logging.getLogger(__name__)


def run_daily_pipeline(db: Session = None, user_id: int = 1) -> Dict[str, Any]:
    """
    Execute the full daily intelligence generation pipeline.
    Returns a summary of what was computed and cached.
    """
    opened_session = False
    if db is None:
        db = SessionLocal()
        opened_session = True

    pipeline_start = datetime.utcnow()
    results = {
        "pipeline_started_at": pipeline_start.isoformat(),
        "steps": {},
        "errors": [],
    }

    try:
        # ─────────────────────────────────────────────────────────────
        # STEP 1: Refresh macro regime classification
        # ─────────────────────────────────────────────────────────────
        logger.info("📊 [Pipeline Step 1/7] Refreshing macro regime classification...")
        try:
            regime = classify_market_regime(db)
            results["steps"]["macro_regime"] = {
                "status": "completed",
                "regime": regime.get("regime"),
                "confidence": regime.get("confidence"),
            }
        except Exception as e:
            logger.error(f"Pipeline Step 1 failed: {e}")
            results["errors"].append(f"macro_regime: {str(e)}")
            results["steps"]["macro_regime"] = {"status": "failed", "error": str(e)}
            regime = {"regime": "growth-led easing", "confidence": 0.5}

        # ─────────────────────────────────────────────────────────────
        # STEP 2: Refresh signal generation across tracked tickers
        # ─────────────────────────────────────────────────────────────
        logger.info("📡 [Pipeline Step 2/7] Regenerating prioritized signals...")
        try:
            signals = get_prioritized_signal_feed(db=db, limit=20)
            results["steps"]["signal_refresh"] = {
                "status": "completed",
                "signals_generated": len(signals),
            }
        except Exception as e:
            logger.error(f"Pipeline Step 2 failed: {e}")
            results["errors"].append(f"signal_refresh: {str(e)}")
            results["steps"]["signal_refresh"] = {"status": "failed", "error": str(e)}
            signals = []

        # ─────────────────────────────────────────────────────────────
        # STEP 3: Rerun thesis conviction evaluation across all boards
        # ─────────────────────────────────────────────────────────────
        logger.info("🧠 [Pipeline Step 3/7] Evaluating thesis conviction across all boards...")
        try:
            refresh_all_thesis_boards(db)
            boards = thesis_repository.list_boards(db, user_id=user_id)
            thesis_summary = [
                {"id": b.id, "title": b.title, "status": b.status, "conviction": float(b.conviction_score or 50.0)}
                for b in boards
            ]
            results["steps"]["thesis_conviction"] = {
                "status": "completed",
                "boards_evaluated": len(boards),
                "summary": thesis_summary,
            }
        except Exception as e:
            logger.error(f"Pipeline Step 3 failed: {e}")
            results["errors"].append(f"thesis_conviction: {str(e)}")
            results["steps"]["thesis_conviction"] = {"status": "failed", "error": str(e)}

        # ─────────────────────────────────────────────────────────────
        # STEP 4: Refresh company intelligence snapshots for key tickers
        # ─────────────────────────────────────────────────────────────
        logger.info("🔬 [Pipeline Step 4/7] Refreshing company intelligence snapshots...")
        refreshed_tickers = []
        try:
            # Collect tickers from watchlists, thesis boards, and portfolios
            tickers_set = set()
            watchlists = db.query(Watchlist).filter(Watchlist.user_id == user_id).all()
            for w in watchlists:
                tickers_set.update(i.ticker.upper() for i in w.items)

            boards = thesis_repository.list_boards(db, user_id=user_id)
            for b in boards:
                tickers_set.update(s.ticker.upper() for s in b.stocks)

            portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
            for p in portfolios:
                tickers_set.update(h.ticker.upper() for h in p.holdings)

            # Always include a base ticker
            if not tickers_set:
                tickers_set = {"AAPL"}

            for ticker in tickers_set:
                try:
                    get_or_compute_snapshot(ticker, db=db, force_refresh=True)
                    refreshed_tickers.append(ticker)
                except Exception as te:
                    logger.warning(f"Failed to refresh snapshot for {ticker}: {te}")

            results["steps"]["snapshot_refresh"] = {
                "status": "completed",
                "tickers_refreshed": refreshed_tickers,
            }
        except Exception as e:
            logger.error(f"Pipeline Step 4 failed: {e}")
            results["errors"].append(f"snapshot_refresh: {str(e)}")
            results["steps"]["snapshot_refresh"] = {"status": "failed", "error": str(e)}

        # ─────────────────────────────────────────────────────────────
        # STEP 5: Run temporal intelligence engine
        # ─────────────────────────────────────────────────────────────
        logger.info("⏳ [Pipeline Step 5/7] Executing temporal intelligence engine...")
        try:
            temporal_events = run_temporal_analysis(db, user_id=user_id)
            results["steps"]["temporal_engine"] = {
                "status": "completed",
                "events_generated": len(temporal_events),
            }
        except Exception as e:
            logger.error(f"Pipeline Step 5 failed: {e}")
            results["errors"].append(f"temporal_engine: {str(e)}")
            results["steps"]["temporal_engine"] = {"status": "failed", "error": str(e)}

        # ─────────────────────────────────────────────────────────────
        # STEP 6: Compile prioritized intelligence stream
        # ─────────────────────────────────────────────────────────────
        logger.info("📋 [Pipeline Step 6/7] Compiling prioritized intelligence stream...")
        try:
            stream = compile_intelligence_stream(db, user_id=user_id, limit=30)
            results["steps"]["intelligence_stream"] = {
                "status": "completed",
                "stream_items": len(stream),
            }
        except Exception as e:
            logger.error(f"Pipeline Step 6 failed: {e}")
            results["errors"].append(f"intelligence_stream: {str(e)}")
            results["steps"]["intelligence_stream"] = {"status": "failed", "error": str(e)}
            stream = []

        # ─────────────────────────────────────────────────────────────
        # STEP 7: Cache daily intelligence snapshot
        # ─────────────────────────────────────────────────────────────
        logger.info("💾 [Pipeline Step 7/7] Caching daily intelligence snapshot...")
        try:
            today = date_type.today()

            # Build thesis change summary
            thesis_changes = []
            for b in thesis_repository.list_boards(db, user_id=user_id):
                evolutions = temporal_repository.list_thesis_evolution(db, b.id, limit=1)
                if evolutions:
                    ev = evolutions[0]
                    thesis_changes.append({
                        "board_id": b.id,
                        "title": b.title,
                        "prior_conviction": ev.prior_conviction,
                        "current_conviction": ev.current_conviction,
                        "evolution_summary": ev.evolution_summary,
                    })

            # Build signal change summary
            signal_changes = []
            for sig in signals[:10]:
                signal_changes.append({
                    "ticker": sig.get("ticker"),
                    "signal_type": sig.get("signal_type"),
                    "severity": sig.get("severity"),
                    "priority_score": sig.get("priority_score"),
                    "title": sig.get("title"),
                })

            # Briefing payload
            briefing = compile_morning_briefing(db=db, user_id=user_id)

            # Persist snapshot
            temporal_repository.upsert_daily_intelligence_snapshot(
                db=db,
                snapshot_date=today,
                snapshot_payload_json=briefing,
                macro_state=regime.get("regime"),
                top_signals_json=signal_changes,
                top_thesis_changes_json=thesis_changes,
                top_portfolio_changes_json=results["steps"].get("snapshot_refresh", {}).get("tickers_refreshed", []),
                macro_summary=regime.get("description"),
                top_signal_changes_json=signal_changes,
                intelligence_feed_json=stream,
            )

            results["steps"]["daily_snapshot"] = {
                "status": "completed",
                "snapshot_date": str(today),
            }
        except Exception as e:
            logger.error(f"Pipeline Step 7 failed: {e}")
            results["errors"].append(f"daily_snapshot: {str(e)}")
            results["steps"]["daily_snapshot"] = {"status": "failed", "error": str(e)}

        # ─────────────────────────────────────────────────────────────
        # PIPELINE SUMMARY
        # ─────────────────────────────────────────────────────────────
        pipeline_end = datetime.utcnow()
        duration = (pipeline_end - pipeline_start).total_seconds()
        results["pipeline_completed_at"] = pipeline_end.isoformat()
        results["pipeline_duration_seconds"] = round(duration, 2)
        results["total_errors"] = len(results["errors"])

        if results["total_errors"] == 0:
            logger.info(f"🏆 Daily intelligence pipeline completed successfully in {duration:.1f}s")
        else:
            logger.warning(f"⚠️ Daily pipeline completed with {results['total_errors']} error(s) in {duration:.1f}s")

        return results

    except Exception as e:
        logger.error(f"Critical pipeline failure: {e}", exc_info=True)
        results["errors"].append(f"critical: {str(e)}")
        return results
    finally:
        if opened_session:
            db.close()
