"""
valuation.py

Pure Python — zero LLM calls.

Reads Free Cash Flow out of the evidence list produced by fundamentals_agent,
then calls finance_core.simple_dcf with fixed conservative assumptions.
Writes the result (or an error dict) into state["valuation"].

WHY no LLM here?
  The DCF model is a deterministic formula.  Letting a language model
  "compute" it would introduce hallucination risk in the most sensitive part
  of the memo (the price target).  The critic in the next stage cross-checks
  every number the writer quotes against this dict.
"""

import re
import sys
import os

# Allow running from backend/ directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import finance_core
from state import ResearchState

# ── DCF assumptions ───────────────────────────────────────────────────────────
_GROWTH_RATE      = 0.08   # 8 % — conservative long-term FCF growth
_DISCOUNT_RATE    = 0.11   # 11 % — typical WACC for a large-cap tech stock
_TERMINAL_MULTIPLE = 12    # exit multiple on final-year FCF
_YEARS            = 5


def _find_fcf(evidence: list[dict]) -> float | None:
    """Search all evidence strings for a Free Cash Flow dollar figure.

    Handles formats produced by compute_ratios:
      "Free Cash Flow:  $124.20B"
      "free cash flow is $5.5B"
      "free cash flow of $900M"
    Returns the value in raw dollars (e.g. 124.2e9).
    """
    for entry in evidence:
        text = entry.get("value", "")
        # Match "free cash flow" then the dollar amount anywhere on that line
        match = re.search(
            r"free cash flow[^\n$]*\$\s*([\d,\.]+)\s*([BMK])?",
            text,
            re.IGNORECASE,
        )
        if match:
            raw = match.group(1).replace(",", "")
            suffix = (match.group(2) or "").upper()
            try:
                amount = float(raw)
            except ValueError:
                continue
            multiplier = {"B": 1e9, "M": 1e6, "K": 1e3}.get(suffix, 1.0)
            return amount * multiplier
    return None


def valuation_node(state: ResearchState) -> dict:
    """DCF valuation node — no LLM, pure arithmetic."""
    evidence = state.get("evidence", [])

    fcf = _find_fcf(evidence)
    if fcf is None:
        return {
            "valuation": {
                "error": (
                    "Could not extract Free Cash Flow from evidence. "
                    "Ensure fundamentals_agent has run and returned FCF data."
                )
            }
        }

    result = finance_core.simple_dcf(
        fcf=fcf,
        growth_rate=_GROWTH_RATE,
        discount_rate=_DISCOUNT_RATE,
        terminal_multiple=_TERMINAL_MULTIPLE,
        years=_YEARS,
    )

    if result is None:
        return {
            "valuation": {
                "error": "simple_dcf returned None — check FCF sign and discount rate."
            }
        }

    return {
        "valuation": {
            "dcf_value_usd": round(result, 2),
            "dcf_value_billions": round(result / 1e9, 2),
            "assumptions": {
                "fcf_input_usd": fcf,
                "fcf_input_billions": round(fcf / 1e9, 2),
                "growth_rate_pct": _GROWTH_RATE * 100,
                "discount_rate_pct": _DISCOUNT_RATE * 100,
                "terminal_multiple": _TERMINAL_MULTIPLE,
                "projection_years": _YEARS,
            },
        }
    }
