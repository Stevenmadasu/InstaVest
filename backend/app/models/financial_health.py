"""
InstaVest — Financial Health Score Model
Composite quality assessment from fundamental data.
"""
from typing import Any


def compute_health_score(metrics: dict[str, Any], financials: list[dict]) -> dict[str, Any]:
    """
    Compute a composite financial health score from key metrics.
    Returns sub-scores and overall grade.
    """
    scores = {}

    # ─── Growth Score (0-100) ───────────────────────
    rev_growth = metrics.get("revenue_growth", 0)
    if rev_growth > 20:
        scores["growth"] = 90
    elif rev_growth > 10:
        scores["growth"] = 75
    elif rev_growth > 5:
        scores["growth"] = 60
    elif rev_growth > 0:
        scores["growth"] = 45
    else:
        scores["growth"] = 25

    # ─── Margin Score (0-100) ───────────────────────
    op_margin = metrics.get("operating_margin", 0)
    gross_margin = metrics.get("gross_margin", 0)
    margin_avg = (op_margin + gross_margin) / 2
    if margin_avg > 40:
        scores["margins"] = 90
    elif margin_avg > 25:
        scores["margins"] = 70
    elif margin_avg > 15:
        scores["margins"] = 50
    else:
        scores["margins"] = 30

    # ─── Balance Sheet Score (0-100) ────────────────
    debt_ebitda = metrics.get("debt_to_ebitda", 0) or 0
    if debt_ebitda < 0.5:
        scores["balance_sheet"] = 95
    elif debt_ebitda < 1.5:
        scores["balance_sheet"] = 80
    elif debt_ebitda < 3.0:
        scores["balance_sheet"] = 60
    elif debt_ebitda < 5.0:
        scores["balance_sheet"] = 40
    else:
        scores["balance_sheet"] = 20

    # ─── FCF Quality (0-100) ───────────────────────
    fcf_yield = metrics.get("fcf_yield", 0)
    if fcf_yield > 5:
        scores["fcf_quality"] = 85
    elif fcf_yield > 3:
        scores["fcf_quality"] = 70
    elif fcf_yield > 1:
        scores["fcf_quality"] = 55
    elif fcf_yield > 0:
        scores["fcf_quality"] = 40
    else:
        scores["fcf_quality"] = 20

    # ─── Profitability (0-100) ─────────────────────
    pe = metrics.get("pe_ratio")
    net_income = metrics.get("net_income_ttm", 0)
    if net_income > 0 and pe and pe < 25:
        scores["profitability"] = 85
    elif net_income > 0:
        scores["profitability"] = 65
    else:
        scores["profitability"] = 25

    # ─── Overall ───────────────────────────────────
    weights = {"growth": 0.25, "margins": 0.25, "balance_sheet": 0.2, "fcf_quality": 0.15, "profitability": 0.15}
    overall = sum(scores[k] * weights[k] for k in weights)

    if overall >= 80:
        grade = "A"
        label = "Excellent"
    elif overall >= 65:
        grade = "B"
        label = "Strong"
    elif overall >= 50:
        grade = "C"
        label = "Moderate"
    elif overall >= 35:
        grade = "D"
        label = "Weak"
    else:
        grade = "F"
        label = "Poor"

    # Risk warnings
    warnings = []
    if debt_ebitda > 3:
        warnings.append("Elevated leverage — debt/EBITDA above 3x")
    if op_margin < 10:
        warnings.append("Low operating margins may indicate competitive pressure")
    if rev_growth < 0:
        warnings.append("Revenue declining — monitor for structural issues")
    if fcf_yield < 0:
        warnings.append("Negative free cash flow — cash burn risk")

    return {
        "overall_score": round(overall),
        "grade": grade,
        "label": label,
        "sub_scores": scores,
        "warnings": warnings,
    }
