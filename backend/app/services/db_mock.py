"""
InstaVest — Centralized In-Memory Database Store
Shares state across routes, services, and background intelligence threads.
"""
from datetime import datetime
from typing import Any, Optional

# ============================================
# IN-MEMORY COLLECTIONS
# ============================================

portfolios = [
    {
        "id": 1, "name": "Main Portfolio", "user_id": 1,
        "holdings": [
            {"ticker": "NVDA", "shares": 120, "average_cost": 85.20, "current_price": 114.30},
            {"ticker": "AAPL", "shares": 200, "average_cost": 155.00, "current_price": 207.50},
            {"ticker": "MSFT", "shares": 50, "average_cost": 310.00, "current_price": 417.20},
            {"ticker": "GOOGL", "shares": 100, "average_cost": 128.50, "current_price": 172.10},
            {"ticker": "AMD", "shares": 200, "average_cost": 110.00, "current_price": 142.00},
            {"ticker": "META", "shares": 10, "average_cost": 420.00, "current_price": 549.00},
        ],
    },
]

watchlists = [
    {"id": 1, "name": "Core Holdings", "user_id": 1, "items": ["AAPL", "MSFT", "NVDA", "GOOGL"]},
    {"id": 2, "name": "AI Thesis", "user_id": 1, "items": ["NVDA", "AMD", "MSFT", "META"]},
    {"id": 3, "name": "Value Plays", "user_id": 1, "items": ["GOOGL", "AMZN"]},
]

boards = [
    {
        "id": 1, 
        "title": "AI Infrastructure Supercycle", 
        "status": "strengthening",
        "confidence": 82, 
        "description": "AI demand drives GPU and cloud infrastructure spending for 3-5 years.",
        "time_horizon": "long", 
        "user_id": 1,
        "stocks": ["NVDA", "AMD", "MSFT"],
        "assumptions": [
            {"id": 1, "text": "Hyperscaler capex grows >20% annually through 2027", "status": "active", "metric": "revenue_growth"},
            {"id": 2, "text": "Operating margins stay healthy", "status": "validated", "metric": "operating_margin"},
            {"id": 3, "text": "FCF yield remains highly cash-generative", "status": "active", "metric": "fcf_yield"},
        ],
    },
    {
        "id": 2, 
        "title": "Consumer Resilience Play", 
        "status": "stable",
        "confidence": 65, 
        "description": "Consumer spending remains resilient despite macro headwinds.",
        "time_horizon": "medium", 
        "user_id": 1,
        "stocks": ["AAPL", "META"],
        "assumptions": [
            {"id": 4, "text": "Gross margins exceed 40%", "status": "active", "metric": "gross_margin"},
            {"id": 5, "text": "Leverage remains below 3.0x debt/EBITDA", "status": "active", "metric": "debt_to_ebitda"},
        ],
    },
]

timeline_events = [
    {
        "id": 1,
        "thesis_board_id": 1,
        "ticker": "NVDA",
        "event_type": "earnings",
        "title": "NVDA Q1 Earnings Beat: Data Center Revenue Surges 427% YoY",
        "description": "NVIDIA reported blowout earnings confirming massive hyperscaler capex acceleration. Cloud providers continue to deploy capital at an unprecedented rate, validating the initial hypothesis of a multi-year AI infrastructure spend cycle.",
        "metadata_json": {
            "summary": "NVIDIA's Data Center segment grows to $22.6B, smashing estimates.",
            "what_changed": "Hyperscaler demand is scaling rapidly. Revenue growth accelerates to 268% YoY.",
            "why_it_matters": "Confirms that AI spending is converting into hard revenue for hardware providers, strengthening infrastructure thesis conviction.",
            "impacted_assumptions_json": [
                {"id": 1, "text": "Hyperscaler capex grows >20% annually", "new_status": "validated"}
            ],
            "severity": "high"
        },
        "created_at": datetime(2026, 5, 10, 8, 30).isoformat()
    },
    {
        "id": 2,
        "thesis_board_id": 1,
        "ticker": "AMD",
        "event_type": "signal",
        "title": "AMD Margin Compression Signal Triggered",
        "description": "AMD gross margin compressed slightly to 47% under pressure from client CPU pricing competition, prompting an automated risk signal. MOat stability remains resilient but client segments present minor headwinds.",
        "metadata_json": {
            "summary": "AMD client CPU ASP declines, impacting core margins.",
            "what_changed": "Operating margin down 1.2% QoQ.",
            "why_it_matters": "AMD requires high margins in enterprise and server GPUs to fund R&D; margin compression slows their catch-up capability.",
            "impacted_assumptions_json": [
                {"id": 2, "text": "Operating margins stay healthy", "new_status": "at_risk"}
            ],
            "severity": "medium"
        },
        "created_at": datetime(2026, 5, 15, 14, 15).isoformat()
    }
]

intelligence_snapshots = {}

current_regime = {
    "regime": "growth-led tightening",
    "confidence": 0.85,
    "factors": {
        "fed_funds_rate": 5.25,
        "yield_curve_spread": -0.42,
        "treasury_10y": 4.35,
        "treasury_2y": 4.77,
        "vix_proxy": 13.4
    },
    "snapshot_date": datetime.now().date().isoformat(),
    "created_at": datetime.now().isoformat()
}

# ============================================
# ID GENERATORS
# ============================================
next_board_id = 3
next_assumption_id = 6
next_event_id = 3
next_portfolio_id = 2

# ============================================
# HELPERS
# ============================================

def get_all_timeline_events(board_id: Optional[int] = None) -> list[dict]:
    if board_id is not None:
        return [e for e in timeline_events if e["thesis_board_id"] == board_id]
    return timeline_events

def add_timeline_event(board_id: int, ticker: Optional[str], event_type: str, title: str, description: str, metadata: dict) -> dict:
    global next_event_id
    event = {
        "id": next_event_id,
        "thesis_board_id": board_id,
        "ticker": ticker,
        "event_type": event_type,
        "title": title,
        "description": description,
        "metadata_json": metadata,
        "created_at": datetime.now().isoformat()
    }
    timeline_events.insert(0, event) # Decending order (latest first)
    next_event_id += 1
    return event
