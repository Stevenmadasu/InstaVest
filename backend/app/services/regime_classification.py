"""
InstaVest — Market Regime Classification Service (SQL Persisted)
Classifies the macroeconomic regime using FRED data (interest rates, yield curves, unemployment).
"""
import logging
from typing import Any
from datetime import datetime, date as date_type
from sqlalchemy.orm import Session
from app.providers import get_fred_provider
from app.core.database import SessionLocal
from app.db.models import MarketRegimeSnapshot, MacroIndicator

logger = logging.getLogger(__name__)

REGIMES = {
    "growth-led tightening": {
        "label": "Growth-Led Tightening",
        "description": "Strong economic growth with monetary policy tightening (high interest rates to cool inflation). High conviction on operating efficiency and strong moats.",
        "icon": "trending-up"
    },
    "growth-led easing": {
        "label": "Growth-Led Easing",
        "description": "Healthy expansion accompanied by accommodative or stabilizing interest rates. Risk-on assets and high-multiple growth stocks tend to outperform.",
        "icon": "shield-check"
    },
    "defensive-led tightening": {
        "label": "Defensive-Led Tightening",
        "description": "Slowing growth momentum with elevated inflation. Focus on resilient free cash flows, low leverage, and consumer staples.",
        "icon": "shield-exclamation"
    },
    "risk-off contracting": {
        "label": "Risk-Off Contracting",
        "description": "Inverted yield curves and rising unemployment signaling recession risks. Capital preservation, high FCF yield, and net cash balances are prioritized.",
        "icon": "alert-triangle"
    }
}


def classify_market_regime(db: Session = None) -> dict[str, Any]:
    """
    Query FRED provider, apply economic rules to classify current market regime,
    and persist results in PostgreSQL.
    """
    opened_session = False
    if db is None:
        db = SessionLocal()
        opened_session = True

    try:
        fred = get_fred_provider()
        
        # Defaults / fallback
        fed_funds = 5.25
        spread = -0.42
        unrate = 3.9
        treasury_10y = 4.35
        treasury_2y = 4.77
        
        if fred:
            try:
                snapshot = fred.get_macro_snapshot()
                indicators = snapshot.get("indicators", [])
                for ind in indicators:
                    val = ind["value"]
                    if val is None:
                        continue
                    
                    if ind["key"] == "fed_funds_rate":
                        fed_funds = val
                    elif ind["key"] == "unemployment":
                        unrate = val
                    elif ind["key"] == "treasury_10y":
                        treasury_10y = val
                    elif ind["key"] == "treasury_2y":
                        treasury_2y = val

                    # Cache in macro_indicators table
                    # Determine a date (e.g. today)
                    today = date_type.today()
                    existing_ind = db.query(MacroIndicator).filter(
                        MacroIndicator.series_id == ind["key"],
                        MacroIndicator.date == today
                    ).first()
                    if not existing_ind:
                        new_ind = MacroIndicator(
                            series_id=ind["key"],
                            name=ind["name"],
                            date=today,
                            value=val,
                            source="FRED"
                        )
                        db.add(new_ind)
                
                yc = snapshot.get("yield_curve", {})
                if yc.get("spread_10y_2y") is not None:
                    spread = yc["spread_10y_2y"]
                else:
                    spread = round(treasury_10y - treasury_2y, 2)
                    
                db.commit()
            except Exception as e:
                logger.error(f"Failed to fetch real-time FRED data for regime classifier: {e}")

        # Regime Classification Rule Engine
        if spread < -0.1 and unrate > 4.5:
            regime_key = "risk-off contracting"
            confidence = 0.85
        elif fed_funds > 4.0:
            if spread < 0.2:
                regime_key = "growth-led tightening"
                confidence = 0.90
            else:
                regime_key = "defensive-led tightening"
                confidence = 0.75
        else:
            regime_key = "growth-led easing"
            confidence = 0.80

        regime_info = REGIMES[regime_key]
        
        factors = {
            "fed_funds_rate": fed_funds,
            "yield_curve_spread": spread,
            "treasury_10y": treasury_10y,
            "treasury_2y": treasury_2y,
            "unemployment_rate": unrate
        }

        result = {
            "regime": regime_key,
            "label": regime_info["label"],
            "description": regime_info["description"],
            "icon": regime_info["icon"],
            "confidence": confidence,
            "factors": factors
        }
        
        # Cache snapshot in database
        today = date_type.today()
        existing_snap = db.query(MarketRegimeSnapshot).filter(
            MarketRegimeSnapshot.snapshot_date == today
        ).first()
        if existing_snap:
            existing_snap.regime = regime_key
            existing_snap.confidence = confidence
            existing_snap.factors_json = factors
        else:
            new_snap = MarketRegimeSnapshot(
                regime=regime_key,
                confidence=confidence,
                factors_json=factors,
                snapshot_date=today
            )
            db.add(new_snap)
        db.commit()
        return result
    except Exception as e:
        logger.error(f"Failed in SQL regime classification: {e}")
        # Return fallback in case of connection errors
        return {
            "regime": "growth-led tightening",
            "label": "Growth-Led Tightening",
            "description": REGIMES["growth-led tightening"]["description"],
            "icon": REGIMES["growth-led tightening"]["icon"],
            "confidence": 0.90,
            "factors": {
                "fed_funds_rate": 5.25,
                "yield_curve_spread": -0.42,
                "treasury_10y": 4.35,
                "treasury_2y": 4.77,
                "unemployment_rate": 3.9
            }
        }
    finally:
        if opened_session:
            db.close()
