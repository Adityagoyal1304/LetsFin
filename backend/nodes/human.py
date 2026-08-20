"""
human.py

Pauses the graph at human_approval_node using LangGraph's interrupt() primitive.

WHY interrupt() needs a checkpointer
──────────────────────────────────────
When interrupt(value) is called inside a node:
  1. LangGraph serialises the ENTIRE current graph state to the checkpoint store
     (SqliteSaver → checkpoints.sqlite in our setup).
  2. It raises NodeInterrupt, which bubbles up through graph.invoke() or
     graph.stream() to the caller.
  3. The caller inspects the paused state, gets human input, then calls
     graph.invoke(Command(resume=value), config) with the SAME thread_id.
  4. LangGraph reloads the exact checkpoint from step 1, injects the resume
     value as interrupt()'s return value, and continues from THIS node.

Without a checkpointer there is nowhere to persist step 1.  The graph cannot
be paused and resumed — it would have to restart from the beginning, losing
all evidence, the draft, the critique, and the valuation.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from langgraph.types import interrupt
from state import ResearchState


def human_approval_node(state: ResearchState) -> dict:
    """Pause execution and hand control back to the caller for human review.

    The value passed to interrupt() is forwarded to the caller as the
    interrupt payload.  The resumed value (whatever was passed to
    Command(resume=...)) becomes interrupt()'s return value here.
    """
    response: str = interrupt({
        "draft":     state.get("draft", ""),
        "critique":  state.get("critique", ""),
        "valuation": state.get("valuation", {}),
    })

    # Anything other than the exact string "approve" (case-insensitive) is a rejection
    approved = str(response).strip().lower() == "approve"
    return {"approved": approved}
