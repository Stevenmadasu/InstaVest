"""
InstaVest — Signal Engine
Rule-based signal generation and prioritization.
"""
from typing import Any


SIGNAL_RULES = [
    {
        "type": "valuation_stretched",
        "check": lambda m: m.get("pe_ratio") and m["pe_ratio"] > 40,
        "severity": "medium", "direction": "negative",
        "title": lambda m: f'{m["ticker"]} P/E ratio at {m["pe_ratio"]}x — above market average',
        "explanation": lambda m: f'Current P/E of {m["pe_ratio"]}x suggests elevated expectations. Market is pricing in significant earnings growth.',
    },
    {
        "type": "high_fcf_yield",
        "check": lambda m: m.get("fcf_yield") and m["fcf_yield"] > 5,
        "severity": "low", "direction": "positive",
        "title": lambda m: f'{m["ticker"]} free cash flow yield at {m["fcf_yield"]}% — attractive cash generation',
        "explanation": lambda m: f'FCF yield of {m["fcf_yield"]}% indicates strong cash generation relative to valuation.',
    },
    {
        "type": "margin_compression",
        "check": lambda m: m.get("operating_margin") and m["operating_margin"] < 10,
        "severity": "high", "direction": "negative",
        "title": lambda m: f'{m["ticker"]} operating margin at {m["operating_margin"]}% — margin pressure',
        "explanation": lambda m: f'Operating margin of {m["operating_margin"]}% may indicate competitive pressure or rising costs.',
    },
    {
        "type": "revenue_acceleration",
        "check": lambda m: m.get("revenue_growth") and m["revenue_growth"] > 20,
        "severity": "low", "direction": "positive",
        "title": lambda m: f'{m["ticker"]} revenue growth at {m["revenue_growth"]}% — accelerating',
        "explanation": lambda m: f'Revenue growth of {m["revenue_growth"]}% suggests strong demand and market position.',
    },
    {
        "type": "revenue_deceleration",
        "check": lambda m: m.get("revenue_growth") and m["revenue_growth"] < 0,
        "severity": "high", "direction": "negative",
        "title": lambda m: f'{m["ticker"]} revenue declining at {m["revenue_growth"]}%',
        "explanation": lambda m: f'Negative revenue growth of {m["revenue_growth"]}% may indicate structural issues.',
    },
    {
        "type": "high_leverage",
        "check": lambda m: m.get("debt_to_ebitda") and m["debt_to_ebitda"] > 3,
        "severity": "medium", "direction": "negative",
        "title": lambda m: f'{m["ticker"]} leverage elevated at {m["debt_to_ebitda"]}x debt/EBITDA',
        "explanation": lambda m: f'Debt/EBITDA of {m["debt_to_ebitda"]}x may limit financial flexibility.',
    },
    {
        "type": "exceptional_margins",
        "check": lambda m: m.get("gross_margin") and m["gross_margin"] > 70,
        "severity": "low", "direction": "positive",
        "title": lambda m: f'{m["ticker"]} gross margin at {m["gross_margin"]}% — exceptional pricing power',
        "explanation": lambda m: f'Gross margin of {m["gross_margin"]}% indicates strong moat and pricing power.',
    },
]


def generate_signals(metrics: dict[str, Any]) -> list[dict]:
    """Generate signals from key metrics using rule-based engine."""
    signals = []
    for rule in SIGNAL_RULES:
        try:
            if rule["check"](metrics):
                signals.append({
                    "ticker": metrics.get("ticker", ""),
                    "signal_type": rule["type"],
                    "severity": rule["severity"],
                    "direction": rule["direction"],
                    "title": rule["title"](metrics),
                    "explanation": rule["explanation"](metrics),
                    "underlying_metrics": {
                        k: v for k, v in metrics.items()
                        if k in ("pe_ratio", "fcf_yield", "operating_margin", "revenue_growth", "debt_to_ebitda", "gross_margin")
                    },
                })
        except Exception:
            continue
    return signals


def prioritize_signals(signals: list[dict]) -> list[dict]:
    """Rank signals by composite priority score."""
    severity_weights = {"critical": 100, "high": 75, "medium": 50, "low": 25}
    for sig in signals:
        base = severity_weights.get(sig["severity"], 25)
        direction_mult = 1.2 if sig["direction"] == "negative" else 1.0
        sig["priority_score"] = round(base * direction_mult, 1)
    return sorted(signals, key=lambda s: s["priority_score"], reverse=True)
