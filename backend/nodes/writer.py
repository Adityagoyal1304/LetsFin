"""
writer.py

Drafts a structured investment memo using writer_llm.with_structured_output(Memo).

The Memo Pydantic model enforces that every numeric claim is explicitly listed
in `numbers_used`.  The critic node in the next step uses that list to check
each figure against the evidence — if the writer invents a number, numbers_used
will contain it and the critic will flag it.

On revision rounds (revision_count > 0) the previous critique is appended to
the prompt so the writer knows exactly what to fix.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from llm_config import get_writer_llm
from state import ResearchState


class Memo(BaseModel):
    thesis: str = Field(description="One-sentence investment thesis.")
    strengths: list[str] = Field(description="Bulleted list of business strengths.")
    risks: list[str] = Field(description="Bulleted list of key risks.")
    valuation_summary: str = Field(
        description="One or two sentences interpreting the DCF result."
    )
    numbers_used: list[str] = Field(
        description=(
            "Every numeric claim made anywhere in the memo, one per entry. "
            "Example: ['ROE: 151.9%', 'FCF: $124.20B', 'DCF implied value: $1.23T']. "
            "If a number appears in the memo it MUST appear here."
        )
    )


def writer_node(state: ResearchState) -> dict:
    """Draft or revise an investment memo, incrementing revision_count each time."""
    evidence     = state.get("evidence") or []
    valuation    = state.get("valuation") or {}
    revision_count = state.get("revision_count") or 0

    # Format evidence as readable bullet lines
    evidence_lines = "\n".join(
        f"  [{e['source']} | {e['as_of']}]  {e['key']}: {e['value']}"
        for e in evidence
    )

    system_msg = SystemMessage(content=(
        "You are a senior financial analyst writing a structured investment memo. "
        "Every number you include MUST come verbatim from the EVIDENCE or VALUATION sections below. "
        "Do NOT invent, estimate, or round figures that are not explicitly stated in those sections. "
        "List every numeric claim you make in the `numbers_used` field — this will be audited."
    ))

    human_content = f"""Write an investment memo based solely on the following data.

EVIDENCE:
{evidence_lines if evidence_lines else "  (no evidence gathered)"}

VALUATION (DCF, no LLM involved):
{json.dumps(valuation, indent=2)}
"""

    if revision_count > 0:
        critique = state.get("critique") or ""
        human_content += f"""

---
REVISION REQUEST (this is revision #{revision_count + 1}):

The previous draft was rejected by the fact-checker for the following reasons:
{critique}

Fix ONLY the issues listed above.  For each problematic number either:
  (a) replace it with the exact figure from the evidence/valuation above, or
  (b) remove the claim entirely.
Do not add new numbers that are not in the evidence.
"""

    human_msg = HumanMessage(content=human_content)

    writer_llm = get_writer_llm()
    structured = writer_llm.with_structured_output(Memo)
    memo: Memo = structured.invoke([system_msg, human_msg])

    # Serialise Memo to a JSON string for state["draft"]
    draft_str = json.dumps(memo.model_dump(), indent=2)

    return {
        "draft": draft_str,
        "revision_count": revision_count + 1,
    }
