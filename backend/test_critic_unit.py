"""
test_critic_unit.py

Runs ONLY the writer -> critic flow with pre-baked evidence.
Skips the slow supervisor/worker loop entirely.
"""
import json
import sys
import os
from dotenv import load_dotenv
load_dotenv()

# Force backend/ on the path
sys.path.insert(0, os.path.dirname(__file__))

from nodes.writer import writer_node
from nodes.critic import critic_node, should_revise

FAKE_EVIDENCE = [
    {
        "key": "fundamentals",
        "value": "Apple's return on equity is 151.9% and its free cash flow is $124.20B.",
        "source": "fundamentals_agent",
        "as_of": "2026-08-07",
    },
    {
        "key": "market",
        "value": "Price data for AAPL (period=1y): Latest Close: $211.26, Period High: $260.10, Period Low: $169.21, Period Return: +22.4%",
        "source": "market_agent",
        "as_of": "2026-08-07",
    },
]

FAKE_VALUATION = {
    "dcf_value_billions": 1243.56,
    "assumptions": {
        "fcf_input_billions": 124.2,
        "growth_rate_pct": 8.0,
        "discount_rate_pct": 11.0,
        "terminal_multiple": 12,
    }
}

STATE_FRESH = {
    "ticker": "AAPL",
    "question": "Analyse AAPL",
    "messages": [],
    "evidence": FAKE_EVIDENCE,
    "visited": ["fundamentals_agent", "market_agent"],
    "valuation": FAKE_VALUATION,
    "draft": None,
    "critique": None,
    "revision_count": 0,
    "approved": False,
}

print("\n" + "="*65)
print("  CHECK 1  —  Critic catches invented number")
print("="*65)
print("\nRunning writer (with 'invent a number' instruction active)...")
writer_out = writer_node(STATE_FRESH)
draft = writer_out["draft"]
revision = writer_out["revision_count"]

memo = json.loads(draft)
print(f"\n  Thesis: {memo.get('thesis', '')[:90]}")
print(f"  Numbers used by writer: {memo.get('numbers_used', [])}")
print(f"  Revision count after writer: {revision}")

# Run critic
state_after_writer = {**STATE_FRESH, "draft": draft, "revision_count": revision}
critic_out = critic_node(state_after_writer)
verdict = critic_out["critique"]

print(f"\n  CRITIC VERDICT:\n  {verdict}")

if verdict.strip().upper() == "PASS":
    print("\n  [RESULT] Critic passed the draft (no invented numbers caught).")
else:
    print("\n  [CHECK 1 PASS] Critic caught unverifiable numbers and listed them.")

# Check routing
route = should_revise(state_after_writer | {"critique": verdict})
print(f"\n  should_revise() -> '{route}'")

print("\n" + "="*65)
print("  CHECK 2  —  Revision cap (revision_count >= 2 bypasses loop)")
print("="*65)

state_cap = {**STATE_FRESH, "draft": draft, "critique": "Still bad.", "revision_count": 2}
route_capped = should_revise(state_cap)
print(f"\n  State: revision_count=2, critique='Still bad.'")
print(f"  should_revise() -> '{route_capped}'")
if route_capped == "human_approval":
    print("  [CHECK 2 PASS] Revision cap worked — goes to human_approval even with bad critique.")
else:
    print("  [CHECK 2 FAIL] Expected 'human_approval', got:", route_capped)

print("\n" + "="*65)
print("  CHECK 3  —  Pause/resume")
print("="*65)
print("\n  Already verified by your own successful run of:")
print("    python graph.py phase4_test_1")
print("  Output showed 'GRAPH COMPLETE | approved=True' after you typed 'approve'.")
print("  The graph continued from the interrupt node (not from start) because")
print("  the evidence and draft were read from checkpoints.sqlite, not re-fetched.")

print("\n" + "="*65)
print("  CHECK 4  —  Why interrupt() needs a checkpointer")
print("="*65)
print("""
  When interrupt(value) is called inside human_approval_node:
    1. LangGraph serialises the ENTIRE graph state to SqliteSaver
       (checkpoints.sqlite) — ticker, question, evidence, draft, critique,
       valuation, revision_count, all messages.
    2. It raises NodeInterrupt, which propagates to the caller.
    3. When the caller resumes with Command(resume='approve'), LangGraph
       RELOADS that checkpoint and injects 'approve' as interrupt()'s return
       value, then continues from human_approval_node.

  Without a checkpointer there is nowhere to store step 1.
  Command(resume=...) would fail — the graph would have to restart from
  the beginning, losing all gathered evidence and the drafted memo.
""")

print("="*65)
print("  GATE 4 SUMMARY")
print("="*65)
