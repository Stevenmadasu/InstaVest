"""
InstaVest — Company Brain Service
Assembles the full research intelligence object for a company.
Uses live providers when configured, falls back to mock data.
"""
from typing import Any
from app.providers import get_provider, get_ai_provider
from app.models.reverse_dcf import run_reverse_dcf
from app.models.peer_comparison import run_peer_comparison
from app.models.financial_health import compute_health_score
from app.services.signal_engine import generate_signals, prioritize_signals


def build_company_brain(ticker: str, provider=None) -> dict[str, Any]:
    """
    Build the full Company Brain for a ticker.
    Aggregates: profile, financials, valuation, signals, peers, health, AI summary.
    """
    if provider is None:
        provider = get_provider()

    ticker = ticker.upper()
    profile = provider.get_company_profile(ticker)
    if not profile:
        return {"error": f"No data for {ticker}"}

    metrics = provider.get_key_metrics(ticker)
    financials = provider.get_financial_statements(ticker)
    prices = provider.get_price_history(ticker)

    # ─── Reverse DCF ───────────────────────────────
    # All financial values are in millions; convert shares to millions for consistency
    shares_m = metrics.get("shares_outstanding", 1) / 1e6  # shares in millions
    dcf_result = run_reverse_dcf(
        price=metrics.get("price", 0),
        shares_outstanding=shares_m,
        revenue_ttm=metrics.get("revenue_ttm", 0),  # already in millions
        net_debt=metrics.get("net_debt", 0),          # already in millions
        current_op_margin=metrics.get("operating_margin", 20) / 100,
    )

    # ─── Peer Comparison ──────────────────────────
    peer_result = run_peer_comparison(ticker, provider)

    # ─── Health Score ─────────────────────────────
    health_result = compute_health_score(metrics, financials)

    # ─── Signal Engine ────────────────────────────
    signals = generate_signals(metrics)
    signals = prioritize_signals(signals)

    # ─── Scenarios ────────────────────────────────
    scenarios = {
        "bull": {"price": dcf_result["scenarios"]["bull"],
                 "thesis": "Strong execution, margin expansion, market share gains",
                 "upside": dcf_result["upside_pct"]},
        "base": {"price": dcf_result["scenarios"]["base"],
                 "thesis": "Continuation of current growth and margin trajectory",
                 "upside": 0},
        "bear": {"price": dcf_result["scenarios"]["bear"],
                 "thesis": "Growth slowdown, margin pressure, competitive threats",
                 "downside": dcf_result["downside_pct"]},
    }

    # ─── Key Metrics Summary ──────────────────────
    key_metrics = {
        "price": metrics.get("price"),
        "market_cap": metrics.get("market_cap"),
        "ev": metrics.get("ev"),
        "pe_ratio": metrics.get("pe_ratio"),
        "ev_revenue": metrics.get("ev_revenue"),
        "ev_ebitda": metrics.get("ev_ebitda"),
        "fcf_yield": metrics.get("fcf_yield"),
        "revenue_growth": metrics.get("revenue_growth"),
        "gross_margin": metrics.get("gross_margin"),
        "operating_margin": metrics.get("operating_margin"),
        "revenue_ttm": metrics.get("revenue_ttm"),
        "net_income_ttm": metrics.get("net_income_ttm"),
        "fcf_ttm": metrics.get("fcf_ttm"),
        "net_debt": metrics.get("net_debt"),
        "debt_to_ebitda": metrics.get("debt_to_ebitda"),
    }

    # ─── Risks ────────────────────────────────────
    risks = health_result.get("warnings", [])
    if dcf_result["implied_revenue_cagr"] > 15:
        risks.append("Market pricing in aggressive growth expectations — downside risk if execution falters")
    if metrics.get("pe_ratio") and metrics["pe_ratio"] > 50:
        risks.append("Richly valued — stock sensitive to multiple compression")

    # ─── AI Synthesis ─────────────────────────────
    # Assemble the brain data first for AI context
    brain_data = {
        "ticker": ticker,
        "profile": profile,
        "key_metrics": key_metrics,
        "valuation": dcf_result,
        "health_score": health_result,
        "signals": signals,
        "scenarios": scenarios,
        "financials": financials,
    }

    ai_provider = get_ai_provider()
    if ai_provider:
        ai_summary = ai_provider.synthesize_research(brain_data)
        what_changed = ai_provider.generate_what_changed(brain_data)
        ai_synthesis = ai_summary  # Use the same synthesis
    else:
        # Template fallback
        ai_summary = (
            f"{profile['name']} ({ticker}) is a {profile.get('sector', 'N/A')} company "
            f"trading at ${metrics.get('price', 0):.2f}. "
            f"The market is pricing in {dcf_result['implied_revenue_cagr']}% revenue CAGR "
            f"over the next 10 years. "
            f"Financial health is {health_result['label']} ({health_result['grade']}) "
            f"with a score of {health_result['overall_score']}/100. "
            f"{dcf_result['interpretation']}"
        )
        what_changed = (
            f"Revenue grew {metrics.get('revenue_growth', 0)}% YoY. "
            f"Operating margin is at {metrics.get('operating_margin', 0)}%. "
            f"{len(signals)} active signals detected."
        )
        ai_synthesis = (
            f"Overall, {ticker} presents a {health_result['label'].lower()} fundamental profile. "
            f"{dcf_result['interpretation']}"
        )

    return {
        "ticker": ticker,
        "profile": profile,
        "key_metrics": key_metrics,
        "valuation": dcf_result,
        "peers": peer_result,
        "health_score": health_result,
        "signals": signals,
        "scenarios": scenarios,
        "risks": risks,
        "catalysts": [
            "New product launches or market expansion",
            "Margin improvement from operating leverage",
            "Share buyback program reducing share count",
        ],
        "ai_summary": ai_summary,
        "ai_what_changed": what_changed,
        "ai_synthesis": ai_synthesis,
        "market_expectations": dcf_result,
        "financials": financials,
        "price_history": prices[-30:] if prices else [],
    }
