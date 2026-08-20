"""
critic.py

Fact-checks the writer's draft by comparing `numbers_used` against the
evidence list and valuation dict.  Returns "PASS" if every figure is
verifiable, or a bulleted list of unverifiable numbers.

should_revise() is the routing function wired to add_conditional_edges.
The revision_count cap is what prevents an infinite writer→critic loop
that would silently burn API credits without the user noticing.
"""

import json
import sys
import os
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from langchain_core.messages import HumanMessage, SystemMessage
from llm_config import get_critic_llm
from state import ResearchState

class RevisionCommand(BaseModel):
    needs_revision: bool
    feedback: str = Field(description="A concise bulleted list of unverified numbers, or 'PASS'")

def critic_node(state: ResearchState) -> dict:
    """Verify every number in the draft against evidence and valuation."""
    evidence     = state.get("evidence") or []
    valuation    = state.get("valuation") or {}
    draft_str    = state.get("draft") or "{}"

    # Parse the draft to extract the explicit numbers_used list
    try:
        draft = json.loads(draft_str)
        numbers_used: list[str] = draft.get("numbers_used") or []
    except (json.JSONDecodeError, AttributeError):
        numbers_used = []

    # Format evidence as "key = value (source, as_of)" — one line per entry
    evidence_lines = "\n".join(
        f"  {e['key']} = {e['value']}  (source: {e['source']}, as_of: {e['as_of']})"
        for e in evidence
    )

    numbers_block = "\n".join(f"  - {n}" for n in numbers_used) or "  (none listed)"

    system_msg = SystemMessage(content=(
        "You are a strict financial fact-checker. "
        "Your only job is to verify that the numbers listed in NUMBERS USED IN MEMO "
        "can each be found verbatim (or as a trivial restatement) in EVIDENCE or VALUATION. "
        "Reply with exactly the word PASS if every number checks out. "
        "Otherwise reply with a bulleted list of ONLY the numbers that cannot be verified — "
        "one bullet per unverifiable figure, no extra commentary."
    ))

    human_content = f"""EVIDENCE (ground truth):
{evidence_lines if evidence_lines else "  (none)"}

VALUATION (ground truth):
{json.dumps(valuation, indent=2)}

NUMBERS USED IN MEMO (to verify):
{numbers_block}

Reply PASS or a bulleted list of unverifiable numbers.
"""

    critic_llm = get_critic_llm()
    verdict = critic_llm.invoke(
        [system_msg, HumanMessage(content=human_content)]
    ).content.strip()

    return {"critique": verdict}


# ── Routing function ─────────────────────────────────────────────────────────

def should_revise(state: ResearchState) -> str:
    """Decide whether to send the draft back to the writer or to human approval.

    Returns "writer" or "human_approval".

    The revision_count cap (>= 2) is what prevents an infinite loop that
    silently burns API credits.  Without it a stubborn writer could keep
    generating flawed drafts and the critic would keep rejecting them.
    Each full writer→critic round costs ~2 LLM calls; capping at 2 revisions
    limits worst-case API spend for this sub-loop to 3 writer calls + 3 critic
    calls = 6 calls total, regardless of model behaviour.
    """
    critique       = (state.get("critique") or "").strip()
    revision_count = state.get("revision_count") or 0

    # Proceed if fact-checker approved OR we have hit the revision ceiling
    if critique.upper() == "PASS" or revision_count >= 2:
        return "human_approval"

    return "writer"
