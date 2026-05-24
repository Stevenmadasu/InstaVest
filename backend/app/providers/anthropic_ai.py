"""
InstaVest — Anthropic AI Provider
Claude-powered research synthesis and thesis evaluation.
Falls back to template strings when API is unavailable.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AnthropicAIProvider:
    """AI provider for research synthesis using Claude."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    @property
    def client(self):
        """Lazy-initialize the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
        return self._client

    def _call_claude(self, system: str, prompt: str, max_tokens: int = 1024) -> str | None:
        """Make a Claude API call with error handling."""
        if not self.client:
            return None
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            return None
    def synthesize_research(self, brain_data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate decision-oriented AI research commentary from Company Brain data.
        Returns a structured dictionary answering "Why it matters", "Thesis impact",
        "Valuation impact" with full AI audit metadata versioning.
        """
        ticker = brain_data.get("ticker", "")
        profile = brain_data.get("profile", {})
        metrics = brain_data.get("key_metrics", {})
        valuation = brain_data.get("valuation", {})
        health = brain_data.get("health_score", {})
        signals = brain_data.get("signals", [])
        scenarios = brain_data.get("scenarios", {})

        system = """You are a senior hedge fund portfolio manager. 
Assess this company and return JSON format ONLY. Your response must be a single JSON object.
Never include prose outside the JSON. All keys must be answered:
{
  "summary": "Brief 1-sentence description.",
  "what_changed": "Brief details on recent financial trajectory shift.",
  "why_it_matters": "What is the critical investment question or core debate for this business right now?",
  "valuation_impact": "How does the implied DCF growth rate compare to historical norms or current multiple?",
  "thesis_impact": "Does this strengthen or weaken a long-term conviction stance and why?",
  "risks_to_monitor": ["risk item 1", "risk item 2"]
}"""

        prompt = f"""Synthesize a decision-oriented analysis for {ticker} ({profile.get('name', '')}):

Company: {profile.get('description', '')[:250]}
Sector: {profile.get('sector', '')} | Industry: {profile.get('industry', '')}

Key Metrics:
- Price: ${metrics.get('price', 0):.2f} | Market Cap: ${metrics.get('market_cap', 0):,.0f}
- Revenue TTM: ${metrics.get('revenue_ttm', 0):,}M | Growth: {metrics.get('revenue_growth', 0)}% YoY
- P/E: {metrics.get('pe_ratio', 'N/A')}x | EV/EBITDA: {metrics.get('ev_ebitda', 'N/A')}x
- Gross Margin: {metrics.get('gross_margin', 'N/A')}% | Op Margin: {metrics.get('operating_margin', 'N/A')}%
- FCF Yield: {metrics.get('fcf_yield', 0)}%

Valuation:
- Implied Revenue CAGR: {valuation.get('implied_revenue_cagr', 'N/A')}%
- DCF Interpretation: {valuation.get('interpretation', '')}

Scenarios: Bull ${scenarios.get('bull', {}).get('price', 'N/A')} | Base ${scenarios.get('base', {}).get('price', 'N/A')} | Bear ${scenarios.get('bear', {}).get('price', 'N/A')}

Health: {health.get('grade', 'N/A')} ({health.get('overall_score', 'N/A')}/100)

Active Signals ({len(signals)}): {', '.join(s.get('title', '')[:80] for s in signals[:3])}

Return a single JSON object matching the format specified."""

        import json
        from datetime import datetime
        metadata = {
            "source_model": "claude-sonnet-4-20250514",
            "prompt_template_version": "v2.2-decision-oriented",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_references": ["FMP:profile", "FMP:financials", "FRED:macro"],
            "source_data_version_references": {
                "price_version": f"px-{metrics.get('price', 0)}",
                "financial_version": f"rev-{metrics.get('revenue_ttm', 0)}"
            }
        }

        result = self._call_claude(system, prompt)
        if result:
            try:
                # Attempt to extract JSON if Claude added markdown wrapper
                json_str = result.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
                parsed = json.loads(json_str.strip())
                parsed["ai_generation_metadata"] = metadata
                return parsed
            except Exception as e:
                logger.error(f"Failed to parse Claude JSON response: {e}. Raw response: {result}")

        # High-fidelity Fallback to template
        return self._template_synthesis(brain_data, metadata)

    def generate_what_changed(self, brain_data: dict[str, Any]) -> str:
        """Generate a 'what changed' narrative from metrics."""
        ticker = brain_data.get("ticker", "")
        metrics = brain_data.get("key_metrics", {})
        signals = brain_data.get("signals", [])
        financials = brain_data.get("financials", [])

        # Group metrics by fiscal year
        by_year = {}
        for item in financials:
            yr = item.get("fiscal_year")
            if not yr:
                continue
            if yr not in by_year:
                by_year[yr] = {}
            by_year[yr][item.get("metric")] = item.get("value")

        # Format a chronological summary for Claude to see the trend
        sorted_years = sorted(by_year.keys())
        trend_summary = ""
        for yr in sorted_years:
            y_data = by_year[yr]
            trend_summary += (
                f"- FY{yr}: Revenue ${y_data.get('revenue', 'N/A')}M, "
                f"Gross Margin {y_data.get('gross_margin', 'N/A')}%, "
                f"Operating Margin {y_data.get('operating_margin', 'N/A')}%, "
                f"Net Income ${y_data.get('net_income', 'N/A')}M\n"
            )

        system = """You are a financial news analyst. Write a brief 2-sentence update
on what changed recently for this stock comparing recent fiscal years and current TTM metrics.
Focus on the most impactful metric changes. Be specific with numbers."""

        signal_text = "; ".join(s.get("title", "") for s in signals[:3])

        prompt = f"""What changed for {ticker}?

Trend History:
{trend_summary or "No trend history available."}

Current TTM Metrics & Growth:
- Revenue growth: {metrics.get('revenue_growth', 0)}% YoY
- Operating margin: {metrics.get('operating_margin', 'N/A')}%
- P/E ratio: {metrics.get('pe_ratio', 'N/A')}x
- Active signals: {signal_text or 'None'}

Write 2 sentences about what changed recently in its growth, margins, or valuation multiple."""

        result = self._call_claude(system, prompt, max_tokens=256)
        if result:
            return result

        # Fallback
        return (
            f"Revenue grew {metrics.get('revenue_growth', 0)}% YoY. "
            f"Operating margin is at {metrics.get('operating_margin', 0)}%. "
            f"{len(signals)} active signals detected."
        )

    def evaluate_thesis(self, thesis: dict, metrics: dict) -> dict[str, Any]:
        """Evaluate an investment thesis against current metrics."""
        system = """You are an investment thesis evaluator. Assess whether the thesis
is strengthening, weakening, or stable based on current data. Be specific.
Respond in JSON format: {"status": "strengthening|weakening|stable|broken", "confidence_delta": -10 to +10, "reasoning": "..."}"""

        prompt = f"""Thesis: {thesis.get('title', '')}
Description: {thesis.get('description', '')}
Current confidence: {thesis.get('confidence', 50)}%

Current metrics:
- Revenue growth: {metrics.get('revenue_growth', 'N/A')}%
- Op margin: {metrics.get('operating_margin', 'N/A')}%
- P/E: {metrics.get('pe_ratio', 'N/A')}x

Evaluate this thesis."""

        result = self._call_claude(system, prompt, max_tokens=256)
        if result:
            try:
                import json
                return json.loads(result)
            except Exception:
                return {"status": "stable", "confidence_delta": 0, "reasoning": result}

        return {"status": "stable", "confidence_delta": 0, "reasoning": "AI evaluation unavailable"}

    def _template_synthesis(self, brain_data: dict[str, Any], metadata: dict) -> dict[str, Any]:
        """Fallback template-based synthesis when AI is unavailable."""
        profile = brain_data.get("profile", {})
        metrics = brain_data.get("key_metrics", {})
        valuation = brain_data.get("valuation", {})
        health = brain_data.get("health_score", {})
        ticker = brain_data.get("ticker", "")

        cagr = valuation.get("implied_revenue_cagr", 10.0)
        
        why_it_matters = f"Can {profile.get('name', ticker)} maintain its current competitive position to support the market's implied long-term revenue CAGR of {cagr}%?"
        if metrics.get("pe_ratio") and isinstance(metrics["pe_ratio"], (int, float)) and metrics["pe_ratio"] > 40:
            why_it_matters += " A core debate centers on multiple sustainability under tightening monetary conditions."

        thesis_impact = f"Strong financial health of {health.get('grade', 'B')} maintains standard conviction levels."
        if health.get("overall_score", 50) < 40:
            thesis_impact = "Financial health issues trigger fundamental warnings, indicating potential structural weakening."

        return {
            "summary": f"{profile.get('name', ticker)} ({ticker}) is a {profile.get('sector', 'N/A')} player trading at ${metrics.get('price', 0):.2f}.",
            "what_changed": f"Revenue expanded by {metrics.get('revenue_growth', 0)}% YoY, paired with an operating margin of {metrics.get('operating_margin', 0)}%.",
            "why_it_matters": why_it_matters,
            "valuation_impact": f"The market currently prices in an implied 10-year revenue CAGR of {cagr}%, yielding an interpretation of: {valuation.get('interpretation', 'Fairly priced')}.",
            "thesis_impact": thesis_impact,
            "risks_to_monitor": [
                "Margin compression from rising inputs or industry scaling shifts",
                "Valuation multiple contraction if revenue CAGR declines below pricing assumptions"
            ],
            "ai_generation_metadata": metadata
        }

