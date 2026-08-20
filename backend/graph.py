"""
graph.py

Compiles the full Phase-4 research graph:

  START
    ↓
  supervisor  ←─────────────────────────────────────────┐
    ↓ (Command routing)                                  │
  fundamentals_agent / filings_agent / market_agent ─────┘
    ↓ (when supervisor says "valuation")
  valuation           ← pure Python, no LLM
    ↓
  writer              ← drafts structured Memo
    ↓
  critic              ← fact-checks numbers_used vs evidence
    ↓ (conditional: should_revise)
  ┌── "writer"   →  back to writer  (max 2 revisions before bypass)
  └── "human_approval"
        ↓
       END

The graph is compiled with SqliteSaver so that interrupt() in human_approval_node
can save the full state to disk and allow pause/resume across Python invocations.
"""

import json
import os
import sqlite3
import pprint
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from state import ResearchState
from nodes.workers import fundamentals_agent, filings_agent, market_agent
from nodes.supervisor import supervisor_agent
from nodes.valuation import valuation_node
from nodes.writer import writer_node
from nodes.critic import critic_node, should_revise
from nodes.human import human_approval_node


def build_graph():
    builder = StateGraph(ResearchState)

    # ── Nodes ────────────────────────────────────────────────────────────────
    builder.add_node("supervisor",      supervisor_agent)
    builder.add_node("fundamentals_agent", fundamentals_agent)
    builder.add_node("filings_agent",   filings_agent)
    builder.add_node("market_agent",    market_agent)
    builder.add_node("valuation",       valuation_node)
    builder.add_node("writer",          writer_node)
    builder.add_node("critic",          critic_node)
    builder.add_node("human_approval",  human_approval_node)

    # ── Edges ────────────────────────────────────────────────────────────────
    builder.add_edge(START, "supervisor")

    # Workers loop back to supervisor; the supervisor's outgoing edges are
    # determined dynamically via Command(goto=...) — no explicit conditional here.
    builder.add_edge("fundamentals_agent", "supervisor")
    builder.add_edge("filings_agent",      "supervisor")
    builder.add_edge("market_agent",       "supervisor")

    # Linear pipeline after workers are done
    builder.add_edge("valuation", "writer")
    builder.add_edge("writer",    "critic")

    # Conditional loop: critic → writer (revise) or critic → human_approval
    # The revision_count cap inside should_revise prevents infinite API credit burn.
    builder.add_conditional_edges(
        "critic",
        should_revise,
        {"writer": "writer", "human_approval": "human_approval"},
    )

    builder.add_edge("human_approval", END)

    # ── Persistence ──────────────────────────────────────────────────────────
    conn   = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
    memory = SqliteSaver(conn)

    return builder.compile(checkpointer=memory)


# ── CLI demo ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    graph = build_graph()

    # Try to save a visual diagram (requires internet for mermaid.ink)
    try:
        png = graph.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as fh:
            fh.write(png)
        print("Saved graph.png")
    except Exception as e:
        print(f"(graph.png skipped: {e})")

    # Accept thread_id from argv so you can re-run with the same ID to test
    # checkpoint resume behaviour
    thread_id = sys.argv[1] if len(sys.argv) > 1 else "demo_thread"
    config    = {"configurable": {"thread_id": thread_id}}

    ticker   = "AAPL"
    question = f"Analyse {ticker}: give me its ROE, free cash flow, and 52-week price range."

    initial_state = {
        "ticker":         ticker,
        "question":       question,
        "messages":       [{"role": "user", "content": question}],
        "evidence":       [],
        "visited":        [],
        "valuation":      None,
        "draft":          None,
        "critique":       None,
        "revision_count": 0,
        "approved":       False,
    }

    print(f"\nRunning Phase-4 graph  |  ticker={ticker}  |  thread={thread_id}\n")

    # ── Phase 1: run until the human-approval interrupt ───────────────────────
    interrupted = False
    try:
        for _ in graph.stream(initial_state, config, stream_mode="updates"):
            pass  # consume; checkpointed state is updated after each node
    except Exception as exc:
        if "interrupt" in type(exc).__name__.lower():
            interrupted = True
        else:
            raise

    # get_state() works regardless of whether an exception was raised
    snap = graph.get_state(config)
    if snap.next:          # graph has pending nodes → it was interrupted
        interrupted = True

    if not interrupted:
        # Graph ran to END without hitting the interrupt (edge case: no evidence)
        pprint.pprint(snap.values)
        sys.exit(0)

    # ── Phase 2: display the draft and get human decision ────────────────────
    # Read the interrupt payload (if any) — otherwise fall back to state values
    interrupt_val: dict = {}
    if snap.tasks:
        for task in snap.tasks:
            if task.interrupts:
                interrupt_val = task.interrupts[0].value
                break

    draft_str    = interrupt_val.get("draft")    or snap.values.get("draft", "")
    critique     = interrupt_val.get("critique") or snap.values.get("critique", "")
    valuation    = interrupt_val.get("valuation") or snap.values.get("valuation", {})
    revision_count = snap.values.get("revision_count", 0)

    print("\n" + "=" * 65)
    print("PAUSED FOR HUMAN REVIEW")
    print("=" * 65)

    # Pretty-print the structured memo
    try:
        memo = json.loads(draft_str or "{}")
        print(f"\nTHESIS:\n  {memo.get('thesis', '')}")
        print("\nSTRENGTHS:")
        for s in memo.get("strengths", []):
            print(f"  + {s}")
        print("\nRISKS:")
        for r in memo.get("risks", []):
            print(f"  - {r}")
        print(f"\nVALUATION SUMMARY:\n  {memo.get('valuation_summary', '')}")
        print("\nNUMBERS USED:")
        for n in memo.get("numbers_used", []):
            print(f"  * {n}")
    except (json.JSONDecodeError, TypeError):
        print(draft_str)

    print(f"\nCRITIC VERDICT: {critique or '(none)'}")
    print(f"REVISIONS SO FAR: {revision_count}")
    print(f"\nDCF VALUATION:\n  {valuation}")
    print("\n" + "=" * 65)

    # ── Phase 3: resume with human decision ──────────────────────────────────
    # This demonstrates that the graph continues FROM the interrupt node,
    # not from START — all evidence/draft/critique are preserved in the checkpoint.
    decision = input("\nApprove this memo? Type 'approve' to publish, anything else to reject: ").strip()

    print(f"\nResuming graph with decision: {decision!r} ...")
    try:
        for _ in graph.stream(Command(resume=decision), config, stream_mode="updates"):
            pass
    except Exception as exc:
        if "interrupt" in type(exc).__name__.lower():
            pass  # second interrupt would mean another approval gate (not in Phase 4)
        else:
            raise

    final_snap = graph.get_state(config)
    approved   = final_snap.values.get("approved", False)

    print("\n" + "=" * 65)
    print(f"GRAPH COMPLETE  |  approved={approved}")
    if approved:
        print("Memo approved and ready for publication.")
    else:
        print("Memo rejected. Run again with a new thread_id to restart, or same thread_id to resume.")
    print("=" * 65)
