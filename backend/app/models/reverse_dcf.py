"""
InstaVest — Reverse DCF Model
Deterministic valuation model that calculates what the market is pricing in.
"""
from typing import Any
import math


def run_reverse_dcf(
    price: float,
    shares_outstanding: int,
    revenue_ttm: float,
    net_debt: float = 0,
    tax_rate: float = 0.21,
    wacc: float = 0.10,
    terminal_growth: float = 0.03,
    projection_years: int = 10,
    current_op_margin: float = 0.25,
) -> dict[str, Any]:
    """
    Reverse-engineer what growth and margin assumptions the current stock price implies.

    Returns implied revenue CAGR, implied margins, fair value sensitivity, and interpretation.
    """
    market_cap = price * shares_outstanding
    enterprise_value = market_cap + net_debt

    # ─── Implied Revenue CAGR ───────────────────────
    # Solve for revenue growth that justifies current EV
    # Using iterative approach
    best_cagr = None
    min_diff = float("inf")

    for cagr_bps in range(0, 3000, 25):  # 0% to 30%
        cagr = cagr_bps / 10000
        terminal_rev = revenue_ttm * ((1 + cagr) ** projection_years)
        terminal_op_income = terminal_rev * current_op_margin
        terminal_nopat = terminal_op_income * (1 - tax_rate)
        terminal_value = terminal_nopat / (wacc - terminal_growth)

        # Discount terminal value back
        pv_terminal = terminal_value / ((1 + wacc) ** projection_years)

        # Sum of interim FCFs (simplified)
        pv_fcfs = 0
        for yr in range(1, projection_years + 1):
            yr_rev = revenue_ttm * ((1 + cagr) ** yr)
            yr_fcf = yr_rev * current_op_margin * (1 - tax_rate) * 0.7  # 70% conversion
            pv_fcfs += yr_fcf / ((1 + wacc) ** yr)

        implied_ev = pv_terminal + pv_fcfs
        diff = abs(implied_ev - enterprise_value)

        if diff < min_diff:
            min_diff = diff
            best_cagr = cagr

    implied_cagr = best_cagr or 0.0

    # ─── Implied Terminal Margin ────────────────────
    terminal_rev = revenue_ttm * ((1 + implied_cagr) ** projection_years)
    implied_terminal_nopat = enterprise_value * ((wacc - terminal_growth) * ((1 + wacc) ** projection_years))
    implied_terminal_margin = (implied_terminal_nopat / terminal_rev / (1 - tax_rate)) if terminal_rev > 0 else 0
    implied_terminal_margin = max(0, min(1, implied_terminal_margin))

    # ─── Scenario Analysis ──────────────────────────
    scenarios = {}
    for label, growth_adj, margin_adj in [
        ("bear", -0.03, -0.05), ("base", 0, 0), ("bull", 0.03, 0.05)
    ]:
        sc_cagr = implied_cagr + growth_adj
        sc_margin = current_op_margin + margin_adj
        sc_terminal_rev = revenue_ttm * ((1 + sc_cagr) ** projection_years)
        sc_nopat = sc_terminal_rev * sc_margin * (1 - tax_rate)
        sc_tv = sc_nopat / (wacc - terminal_growth) if (wacc - terminal_growth) > 0 else 0
        sc_pv_tv = sc_tv / ((1 + wacc) ** projection_years)

        sc_pv_fcfs = 0
        for yr in range(1, projection_years + 1):
            yr_rev = revenue_ttm * ((1 + sc_cagr) ** yr)
            yr_fcf = yr_rev * sc_margin * (1 - tax_rate) * 0.7
            sc_pv_fcfs += yr_fcf / ((1 + wacc) ** yr)

        sc_ev = sc_pv_tv + sc_pv_fcfs
        sc_equity = sc_ev - net_debt
        sc_price = sc_equity / shares_outstanding if shares_outstanding > 0 else 0
        scenarios[label] = round(sc_price, 2)

    # ─── Sensitivity Table ──────────────────────────
    sensitivity = []
    for w in [wacc - 0.02, wacc - 0.01, wacc, wacc + 0.01, wacc + 0.02]:
        row = {"wacc": round(w * 100, 1)}
        for g in [terminal_growth - 0.01, terminal_growth, terminal_growth + 0.01]:
            t_rev = revenue_ttm * ((1 + implied_cagr) ** projection_years)
            t_nopat = t_rev * current_op_margin * (1 - tax_rate)
            tv = t_nopat / (w - g) if (w - g) > 0 else 0
            pv = tv / ((1 + w) ** projection_years)
            fair = (pv - net_debt) / shares_outstanding if shares_outstanding > 0 else 0
            row[f"tg_{round(g*100,1)}"] = round(fair, 2)
        sensitivity.append(row)

    # ─── Interpretation ─────────────────────────────
    upside = (scenarios["bull"] / price - 1) * 100 if price > 0 else 0
    downside = (scenarios["bear"] / price - 1) * 100 if price > 0 else 0

    if implied_cagr > 0.20:
        interpretation = "Market expectations appear stretched — pricing in aggressive growth."
    elif implied_cagr > 0.12:
        interpretation = "Market expectations are elevated but achievable for a high-quality compounder."
    elif implied_cagr > 0.05:
        interpretation = "Market expectations appear reasonable given historical growth."
    else:
        interpretation = "Market expectations are conservative — potential value opportunity."

    return {
        "implied_revenue_cagr": round(implied_cagr * 100, 1),
        "implied_terminal_margin": round(implied_terminal_margin * 100, 1),
        "current_op_margin": round(current_op_margin * 100, 1),
        "enterprise_value": round(enterprise_value),
        "assumptions": {
            "wacc": round(wacc * 100, 1),
            "terminal_growth": round(terminal_growth * 100, 1),
            "tax_rate": round(tax_rate * 100, 1),
            "projection_years": projection_years,
        },
        "scenarios": scenarios,
        "sensitivity": sensitivity,
        "interpretation": interpretation,
        "upside_pct": round(upside, 1),
        "downside_pct": round(downside, 1),
    }
