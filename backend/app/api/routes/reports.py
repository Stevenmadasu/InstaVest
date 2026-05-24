"""Report routes — in-memory store for MVP."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

_reports = [
    {"id": 1, "ticker": "NVDA", "report_type": "stock_memo", "title": "NVDA — AI Infrastructure Thesis",
     "content": "NVIDIA is the dominant GPU supplier...", "created_at": "2025-05-15T10:00:00"},
    {"id": 2, "ticker": "AAPL", "report_type": "bull_bear", "title": "AAPL — Bull vs Bear Analysis",
     "content": "Apple's services growth continues...", "created_at": "2025-05-12T10:00:00"},
    {"id": 3, "ticker": None, "report_type": "portfolio_risk", "title": "Q2 2025 Portfolio Risk Review",
     "content": "Portfolio concentration risk elevated...", "created_at": "2025-05-10T10:00:00"},
]
_next_id = 4


class ReportGenerate(BaseModel):
    ticker: Optional[str] = None
    report_type: str


@router.get("")
def list_reports(user_id: int = 1):
    return [{"id": r["id"], "ticker": r["ticker"], "type": r["report_type"],
             "title": r["title"], "created_at": r["created_at"]} for r in _reports]


@router.get("/{report_id}")
def get_report(report_id: int):
    r = next((x for x in _reports if x["id"] == report_id), None)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
    return r


@router.post("/generate")
def generate_report(data: ReportGenerate):
    global _next_id
    report = {
        "id": _next_id, "ticker": data.ticker, "report_type": data.report_type,
        "title": f"{data.report_type.replace('_', ' ').title()} — {data.ticker or 'Portfolio'}",
        "content": "Report generation will be available once the AI reasoning service is connected.",
        "created_at": datetime.utcnow().isoformat(),
    }
    _reports.append(report)
    _next_id += 1
    return {"id": report["id"], "status": "generated", "title": report["title"]}
