import operator
from typing import Annotated, Optional, TypedDict
from langgraph.graph.message import add_messages


class ResearchState(TypedDict):
    # ── Phase 2/3 fields ──────────────────────────────────────────────────────
    ticker: str
    question: str
    messages: Annotated[list, add_messages]

    # We use Annotated with operator.add so that each node can return a list
    # of new evidence dicts, and LangGraph will append them to the existing list.
    # If this were a plain list, returning new evidence from a node would overwrite
    # all previous evidence gathered by earlier nodes.
    evidence: Annotated[list[dict], operator.add]

    # Same pattern: each worker appends its own name; never overwrites the list.
    visited: Annotated[list[str], operator.add]

    next_agent: str

    # ── Phase 4 fields ──────────────────────────────────────────────────────
    # Plain (non-Annotated) fields: each write replaces the previous value.
    # That is the correct behaviour — "draft" is always the latest version,
    # "critique" is the latest verdict, etc.
    valuation: Optional[dict]      # DCF result from valuation.py; may hold {"error": "..."}
    draft: Optional[str]           # JSON-serialised Memo from writer.py
    critique: Optional[str]        # "PASS" or bulleted fault list from critic.py
    revision_count: Optional[int]  # incremented by writer each time it runs
    approved: Optional[bool]       # set by human_approval node after interrupt()
