"""
InstaVest — Peer Comparison Model
Relative valuation analysis across a peer group.
"""
from typing import Any
from app.providers.mock import MockProvider


def run_peer_comparison(ticker: str, provider: Any = None) -> dict[str, Any]:
    """Compare a company's valuation to its peer group."""
    if provider is None:
        provider = MockProvider()

    target_metrics = provider.get_key_metrics(ticker)
    if not target_metrics:
        return {"error": f"No data for {ticker}"}

    peers = provider.get_peer_group(ticker)
    peer_data = []
    for p in peers:
        m = provider.get_key_metrics(p)
        if m:
            peer_data.append(m)

    if not peer_data:
        return {"target": target_metrics, "peers": [], "analysis": {}}

    # Calculate peer medians
    def median(vals):
        s = sorted([v for v in vals if v is not None])
        if not s:
            return None
        mid = len(s) // 2
        return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2

    peer_ev_rev = median([p.get("ev_revenue") for p in peer_data])
    peer_ev_ebitda = median([p.get("ev_ebitda") for p in peer_data])
    peer_pe = median([p.get("pe_ratio") for p in peer_data])
    peer_growth = median([p.get("revenue_growth") for p in peer_data])
    peer_margin = median([p.get("operating_margin") for p in peer_data])
    peer_gross = median([p.get("gross_margin") for p in peer_data])

    # Premium/discount
    def prem_disc(target_val, peer_val):
        if target_val is None or peer_val is None or peer_val == 0:
            return None
        return round((target_val / peer_val - 1) * 100, 1)

    ev_rev_premium = prem_disc(target_metrics.get("ev_revenue"), peer_ev_rev)
    ev_ebitda_premium = prem_disc(target_metrics.get("ev_ebitda"), peer_ev_ebitda)
    pe_premium = prem_disc(target_metrics.get("pe_ratio"), peer_pe)

    # Signal
    if ev_rev_premium and ev_rev_premium < -15:
        signal = "Undervalued relative to peers"
        direction = "positive"
    elif ev_rev_premium and ev_rev_premium > 30:
        signal = "Premium valuation versus peers"
        direction = "negative"
    else:
        signal = "In-line with peer valuation"
        direction = "neutral"

    peer_table = [
        {
            "ticker": p["ticker"], "ev_revenue": p.get("ev_revenue"),
            "ev_ebitda": p.get("ev_ebitda"), "pe_ratio": p.get("pe_ratio"),
            "revenue_growth": p.get("revenue_growth"),
            "operating_margin": p.get("operating_margin"),
            "gross_margin": p.get("gross_margin"),
        }
        for p in peer_data
    ]

    return {
        "target": {
            "ticker": ticker, "ev_revenue": target_metrics.get("ev_revenue"),
            "ev_ebitda": target_metrics.get("ev_ebitda"), "pe_ratio": target_metrics.get("pe_ratio"),
            "revenue_growth": target_metrics.get("revenue_growth"),
            "operating_margin": target_metrics.get("operating_margin"),
            "gross_margin": target_metrics.get("gross_margin"),
        },
        "peers": peer_table,
        "medians": {
            "ev_revenue": peer_ev_rev, "ev_ebitda": peer_ev_ebitda,
            "pe_ratio": peer_pe, "revenue_growth": peer_growth,
            "operating_margin": peer_margin, "gross_margin": peer_gross,
        },
        "premium_discount": {
            "ev_revenue": ev_rev_premium, "ev_ebitda": ev_ebitda_premium, "pe_ratio": pe_premium,
        },
        "signal": signal,
        "direction": direction,
    }
