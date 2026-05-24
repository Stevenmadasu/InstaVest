"""
InstaVest — SEC EDGAR Provider (Stub)
Minimal adapter with proper User-Agent for future SEC EDGAR API integration.
Currently returns placeholder data — full implementation planned for Phase 2.

SEC EDGAR API Reference:
- Company Search: https://efts.sec.gov/LATEST/search-index?q=<query>&dateRange=custom
- Filings: https://data.sec.gov/submissions/CIK{cik}.json
- XBRL Facts: https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
- Full-text search: https://efts.sec.gov/LATEST/search-index?q=<query>

IMPORTANT: SEC requires a User-Agent header with contact info.
Rate limit: 10 requests/second max.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# SEC requires this header on all requests
SEC_HEADERS = {
    "User-Agent": "InstaVest/1.0 (contact@instavest.ai)",
    "Accept-Encoding": "gzip, deflate",
}

# Bookmark: Key SEC EDGAR endpoints for future implementation
SEC_ENDPOINTS = {
    "submissions": "https://data.sec.gov/submissions/CIK{cik}.json",
    "company_facts": "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
    "company_concept": "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json",
    "full_text_search": "https://efts.sec.gov/LATEST/search-index?q={query}",
    "edgar_browse": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form_type}",
}


class SECProvider:
    """
    SEC EDGAR API stub.
    Provides the interface for future SEC filing integration.
    Currently returns filing links based on CIK.
    """

    def __init__(self):
        self.headers = SEC_HEADERS

    def get_filing_links(self, cik: str, form_types: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Generate SEC EDGAR links for a company's filings.
        Full API integration planned for Phase 2.
        """
        if not cik:
            return []

        # Normalize CIK to 10 digits with leading zeros
        cik_padded = cik.lstrip("0").zfill(10)

        forms = form_types or ["10-K", "10-Q", "8-K"]
        links = []
        for form in forms:
            links.append({
                "form_type": form,
                "filing_date": "See SEC EDGAR",
                "url": SEC_ENDPOINTS["edgar_browse"].format(cik=cik_padded, form_type=form),
                "data_url": SEC_ENDPOINTS["submissions"].format(cik=cik_padded),
                "source": "sec_edgar",
            })

        return links

    def get_xbrl_url(self, cik: str) -> str:
        """Get the XBRL company facts URL for future parsing."""
        cik_padded = cik.lstrip("0").zfill(10)
        return SEC_ENDPOINTS["company_facts"].format(cik=cik_padded)
