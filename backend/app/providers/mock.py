"""
InstaVest — Mock Data Provider
Realistic financial data for 8 major tickers for development/demo.
"""
from typing import Any, Optional
from datetime import date, timedelta
import random
import math
from app.providers import DataProvider

# ─── Company Profiles ──────────────────────────────

PROFILES = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics", "exchange": "NASDAQ", "country": "US", "description": "Apple designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories. The company also provides digital content, cloud services, and AppleCare.", "market_cap": 3200000000000, "shares_outstanding": 15400000000, "price": 207.50, "cik": "0000320193", "website": "https://apple.com"},
    "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "industry": "Software - Infrastructure", "exchange": "NASDAQ", "country": "US", "description": "Microsoft develops and licenses software, services, devices, and solutions. Key segments include Intelligent Cloud (Azure), Productivity & Business (Office 365), and More Personal Computing (Windows, Xbox).", "market_cap": 3100000000000, "shares_outstanding": 7430000000, "price": 417.20, "cik": "0000789019", "website": "https://microsoft.com"},
    "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors", "exchange": "NASDAQ", "country": "US", "description": "NVIDIA designs GPUs and system-on-chip units for gaming, data center, professional visualization, and automotive markets. The company is the leading provider of AI accelerator hardware.", "market_cap": 2800000000000, "shares_outstanding": 24500000000, "price": 114.30, "cik": "0001045810", "website": "https://nvidia.com"},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "industry": "Internet Content & Information", "exchange": "NASDAQ", "country": "US", "description": "Alphabet operates Google Search, YouTube, Google Cloud Platform, Android, Chrome, and Waymo. The company generates revenue primarily through digital advertising.", "market_cap": 2100000000000, "shares_outstanding": 12200000000, "price": 172.10, "cik": "0001652044", "website": "https://abc.xyz"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Technology", "industry": "Internet Retail", "exchange": "NASDAQ", "country": "US", "description": "Amazon operates e-commerce, cloud computing (AWS), digital streaming, and artificial intelligence businesses. AWS is the world's largest cloud infrastructure provider.", "market_cap": 2000000000000, "shares_outstanding": 10500000000, "price": 190.50, "cik": "0001018724", "website": "https://amazon.com"},
    "META": {"name": "Meta Platforms Inc.", "sector": "Technology", "industry": "Internet Content & Information", "exchange": "NASDAQ", "country": "US", "description": "Meta operates Facebook, Instagram, WhatsApp, and Messenger. The company is investing heavily in Reality Labs (AR/VR) and AI infrastructure.", "market_cap": 1400000000000, "shares_outstanding": 2550000000, "price": 549.00, "cik": "0001326801", "website": "https://meta.com"},
    "AMD": {"name": "Advanced Micro Devices Inc.", "sector": "Technology", "industry": "Semiconductors", "exchange": "NASDAQ", "country": "US", "description": "AMD designs CPUs, GPUs, and adaptive SoCs for data center, client, gaming, and embedded markets. The company competes with Intel and NVIDIA.", "market_cap": 230000000000, "shares_outstanding": 1620000000, "price": 142.00, "cik": "0000002488", "website": "https://amd.com"},
    "TSLA": {"name": "Tesla Inc.", "sector": "Consumer Cyclical", "industry": "Auto Manufacturers", "exchange": "NASDAQ", "country": "US", "description": "Tesla designs, manufactures, and sells electric vehicles, energy storage systems, and solar products. The company also develops autonomous driving technology.", "market_cap": 800000000000, "shares_outstanding": 3200000000, "price": 250.00, "cik": "0001318605", "website": "https://tesla.com"},
}

# ─── Financial Data Templates ──────────────────────

FINANCIALS = {
    "AAPL": {"revenue": [383285, 394328, 381623, 365817], "gross_margin": [0.462, 0.457, 0.438, 0.433], "op_margin": [0.307, 0.301, 0.283, 0.306], "net_income": [96995, 99803, 94680, 99803], "total_assets": [352583, 338516, 352755, 351002], "total_debt": [111088, 109280, 111088, 120069], "cash": [29965, 28408, 30737, 23646], "fcf": [111443, 110543, 99584, 92953], "ebitda": [130541, 129188, 123136, 130541], "shares": [15400, 15550, 15700, 16200], "capex": [10959, 10708, 10959, 11085]},
    "MSFT": {"revenue": [236584, 227583, 211915, 198270], "gross_margin": [0.697, 0.694, 0.688, 0.683], "op_margin": [0.449, 0.441, 0.424, 0.421], "net_income": [88136, 82540, 72738, 72361], "total_assets": [512163, 468310, 411976, 380088], "total_debt": [47069, 41990, 47032, 48344], "cash": [80015, 75528, 111262, 104749], "fcf": [74071, 70099, 63280, 65149], "ebitda": [123700, 115500, 102400, 95000], "shares": [7430, 7455, 7470, 7502], "capex": [44477, 28107, 23886, 24448]},
    "NVDA": {"revenue": [130497, 60922, 26974, 26914], "gross_margin": [0.748, 0.729, 0.569, 0.648], "op_margin": [0.623, 0.541, 0.176, 0.378], "net_income": [72880, 29760, 4368, 9752], "total_assets": [112198, 65728, 44321, 41182], "total_debt": [8459, 8459, 9709, 10946], "cash": [31444, 25984, 13296, 21208], "fcf": [60859, 27021, 3808, 8132], "ebitda": [85000, 38000, 7200, 12500], "shares": [24500, 24560, 24600, 24960], "capex": [3233, 1833, 1833, 1128]},
    "GOOGL": {"revenue": [350018, 307394, 282836, 257637], "gross_margin": [0.577, 0.569, 0.565, 0.553], "op_margin": [0.322, 0.307, 0.277, 0.263], "net_income": [94270, 73795, 59972, 59972], "total_assets": [432280, 407000, 365264, 359268], "total_debt": [13233, 14701, 14701, 14817], "cash": [100746, 110916, 113760, 91432], "fcf": [69495, 60476, 52592, 60037], "ebitda": [125000, 108000, 94000, 83000], "shares": [12200, 12330, 12560, 13044], "capex": [52549, 32251, 29024, 24640]},
    "AMZN": {"revenue": [637997, 574785, 513983, 469822], "gross_margin": [0.498, 0.478, 0.464, 0.439], "op_margin": [0.107, 0.087, 0.072, 0.024], "net_income": [59248, 30425, 21330, -2722], "total_assets": [624966, 527854, 462675, 420549], "total_debt": [58319, 67150, 67150, 59000], "cash": [78744, 73387, 64000, 53888], "fcf": [38200, 32600, 21400, -11600], "ebitda": [108000, 85700, 72600, 55300], "shares": [10500, 10300, 10200, 10200], "capex": [83024, 63645, 58321, 63645]},
    "META": {"revenue": [161740, 134902, 116609, 113640], "gross_margin": [0.818, 0.808, 0.803, 0.785], "op_margin": [0.415, 0.383, 0.349, 0.250], "net_income": [55264, 39098, 23200, 23200], "total_assets": [246010, 229623, 185727, 165987], "total_debt": [28826, 28826, 18385, 9922], "cash": [58068, 41862, 37444, 41583], "fcf": [44300, 43013, 24100, 19417], "ebitda": [82000, 64000, 47800, 37200], "shares": [2550, 2580, 2630, 2700], "capex": [37258, 27266, 32037, 31431]},
    "AMD": {"revenue": [25785, 22680, 23601, 16434], "gross_margin": [0.528, 0.506, 0.471, 0.445], "op_margin": [0.222, 0.053, 0.043, 0.001], "net_income": [5803, 854, 1299, -21], "total_assets": [67886, 67885, 67580, 12419], "total_debt": [1717, 1717, 2467, 312], "cash": [5131, 5878, 5861, 4835], "fcf": [2350, 845, 3065, 2023], "ebitda": [7500, 3800, 3700, 1900], "shares": [1620, 1614, 1610, 1610], "capex": [546, 546, 530, 432]},
    "TSLA": {"revenue": [97690, 96773, 81462, 53823], "gross_margin": [0.184, 0.183, 0.256, 0.254], "op_margin": [0.079, 0.078, 0.168, 0.127], "net_income": [7091, 7928, 12583, 12556], "total_assets": [122070, 106618, 82338, 82338], "total_debt": [5745, 2301, 3543, 3543], "cash": [36563, 29094, 22185, 22185], "fcf": [4358, 4358, 7593, 7593], "ebitda": [14500, 14200, 17400, 13700], "shares": [3200, 3174, 3164, 3130], "capex": [11339, 8877, 7172, 7158]},
}

PEERS = {
    "AAPL": ["MSFT", "GOOGL", "META", "AMZN"],
    "MSFT": ["AAPL", "GOOGL", "AMZN", "META"],
    "NVDA": ["AMD", "AVGO", "INTC", "QCOM"],
    "GOOGL": ["META", "MSFT", "AMZN", "AAPL"],
    "AMZN": ["MSFT", "GOOGL", "AAPL", "META"],
    "META": ["GOOGL", "SNAP", "PINS", "MSFT"],
    "AMD": ["NVDA", "INTC", "QCOM", "AVGO"],
    "TSLA": ["F", "GM", "RIVN", "NIO"],
}


class MockProvider(DataProvider):
    """Mock data provider with realistic financial data for 8 tickers."""

    def get_company_profile(self, ticker: str) -> dict[str, Any]:
        t = ticker.upper()
        if t not in PROFILES:
            return {}
        return {**PROFILES[t], "ticker": t}

    def get_price_history(self, ticker: str, start: Optional[date] = None, end: Optional[date] = None) -> list[dict]:
        t = ticker.upper()
        if t not in PROFILES:
            return []
        base_price = PROFILES[t]["price"]
        end_date = end or date.today()
        start_date = start or (end_date - timedelta(days=365))
        days = (end_date - start_date).days
        prices = []
        price = base_price * 0.75
        for i in range(days):
            d = start_date + timedelta(days=i)
            if d.weekday() >= 5:
                continue
            change = random.gauss(0.0005, 0.018)
            price *= (1 + change)
            high = price * (1 + abs(random.gauss(0, 0.008)))
            low = price * (1 - abs(random.gauss(0, 0.008)))
            prices.append({
                "date": str(d), "open": round(price * (1 + random.gauss(0, 0.003)), 2),
                "high": round(high, 2), "low": round(low, 2),
                "close": round(price, 2), "adjusted_close": round(price, 2),
                "volume": random.randint(20000000, 120000000),
            })
        return prices

    def get_financial_statements(self, ticker: str) -> list[dict]:
        t = ticker.upper()
        if t not in FINANCIALS:
            return []
        fin = FINANCIALS[t]
        stmts = []
        years = [2025, 2024, 2023, 2022]
        for i, year in enumerate(years):
            rev = fin["revenue"][i]
            stmts.extend([
                {"fiscal_year": year, "fiscal_period": "FY", "statement_type": "income", "metric": "revenue", "value": rev, "unit": "USD_M"},
                {"fiscal_year": year, "fiscal_period": "FY", "statement_type": "income", "metric": "gross_profit", "value": round(rev * fin["gross_margin"][i]), "unit": "USD_M"},
                {"fiscal_year": year, "fiscal_period": "FY", "statement_type": "income", "metric": "operating_income", "value": round(rev * fin["op_margin"][i]), "unit": "USD_M"},
                {"fiscal_year": year, "fiscal_period": "FY", "statement_type": "income", "metric": "net_income", "value": fin["net_income"][i], "unit": "USD_M"},
                {"fiscal_year": year, "fiscal_period": "FY", "statement_type": "income", "metric": "ebitda", "value": fin["ebitda"][i], "unit": "USD_M"},
                {"fiscal_year": year, "fiscal_period": "FY", "statement_type": "balance_sheet", "metric": "total_assets", "value": fin["total_assets"][i], "unit": "USD_M"},
                {"fiscal_year": year, "fiscal_period": "FY", "statement_type": "balance_sheet", "metric": "total_debt", "value": fin["total_debt"][i], "unit": "USD_M"},
                {"fiscal_year": year, "fiscal_period": "FY", "statement_type": "balance_sheet", "metric": "cash_and_equivalents", "value": fin["cash"][i], "unit": "USD_M"},
                {"fiscal_year": year, "fiscal_period": "FY", "statement_type": "cash_flow", "metric": "free_cash_flow", "value": fin["fcf"][i], "unit": "USD_M"},
                {"fiscal_year": year, "fiscal_period": "FY", "statement_type": "cash_flow", "metric": "capital_expenditures", "value": fin["capex"][i], "unit": "USD_M"},
                {"fiscal_year": year, "fiscal_period": "FY", "statement_type": "income", "metric": "gross_margin", "value": round(fin["gross_margin"][i] * 100, 1), "unit": "PCT"},
                {"fiscal_year": year, "fiscal_period": "FY", "statement_type": "income", "metric": "operating_margin", "value": round(fin["op_margin"][i] * 100, 1), "unit": "PCT"},
            ])
        return stmts

    def get_filings(self, ticker: str) -> list[dict]:
        t = ticker.upper()
        if t not in PROFILES:
            return []
        return [
            {"form_type": "10-K", "filing_date": "2025-02-01", "accession_number": f"{t}-10K-2025", "url": f"https://sec.gov/filing/{t}/10K"},
            {"form_type": "10-Q", "filing_date": "2025-05-01", "accession_number": f"{t}-10Q-2025Q1", "url": f"https://sec.gov/filing/{t}/10Q"},
            {"form_type": "8-K", "filing_date": "2025-04-15", "accession_number": f"{t}-8K-2025", "url": f"https://sec.gov/filing/{t}/8K"},
        ]

    def get_peer_group(self, ticker: str) -> list[str]:
        return PEERS.get(ticker.upper(), [])

    def get_key_metrics(self, ticker: str) -> dict[str, Any]:
        t = ticker.upper()
        if t not in PROFILES or t not in FINANCIALS:
            return {}
        p = PROFILES[t]
        f = FINANCIALS[t]
        rev = f["revenue"][0]
        ebitda = f["ebitda"][0]
        net_debt = f["total_debt"][0] - f["cash"][0]
        ev = p["market_cap"] / 1e6 + net_debt
        return {
            "ticker": t, "price": p["price"], "market_cap": p["market_cap"],
            "shares_outstanding": p["shares_outstanding"],
            "ev": round(ev), "revenue_ttm": rev, "ebitda_ttm": ebitda,
            "net_income_ttm": f["net_income"][0], "fcf_ttm": f["fcf"][0],
            "ev_revenue": round(ev / rev, 1) if rev else None,
            "ev_ebitda": round(ev / ebitda, 1) if ebitda else None,
            "pe_ratio": round(p["market_cap"] / 1e6 / f["net_income"][0], 1) if f["net_income"][0] > 0 else None,
            "fcf_yield": round(f["fcf"][0] / (p["market_cap"] / 1e6) * 100, 1),
            "gross_margin": round(f["gross_margin"][0] * 100, 1),
            "operating_margin": round(f["op_margin"][0] * 100, 1),
            "revenue_growth": round((f["revenue"][0] / f["revenue"][1] - 1) * 100, 1) if f["revenue"][1] else 0,
            "net_debt": net_debt, "debt_to_ebitda": round(f["total_debt"][0] / ebitda, 1) if ebitda else None,
        }
