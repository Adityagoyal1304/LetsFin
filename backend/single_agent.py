"""
single_agent.py

A single ReAct agent built with create_react_agent from langgraph.prebuilt.
Run it from the command line:

    python single_agent.py "What is Apple's ROE and free cash flow?"
    python single_agent.py "What supply chain risks does the company describe?"

LangSmith tracing is enabled automatically when LANGCHAIN_TRACING_V2=true
in your .env file. Open https://smith.langchain.com to see the trace.

What create_react_agent builds for you (so you know what you are NOT writing):
─────────────────────────────────────────────────────────────────────────────
  State schema: MessagesState
      {"messages": Annotated[list, add_messages]}
      Every node reads and appends to this list.

  Node 1 — "agent" (the LLM node)
      The model receives all current messages plus the JSON schema of every tool.
      It either:
        (a) emits an AIMessage with one or more tool_calls → go to ToolNode, OR
        (b) emits a plain AIMessage with no tool_calls   → go to END

  Node 2 — ToolNode (built-in langgraph node)
      Looks at the tool_calls in the last AIMessage, runs each matching tool
      function, and appends the results as ToolMessages to the state.
      Then loops back to the agent node.

  Conditional edge: after the agent node
      if last_message.tool_calls → "tools"
      else                       → END

  The loop terminates naturally when the model stops requesting tools.
  Without a revision_count guard this *could* loop forever on a confused model —
  the full multi-agent graph in Phase 3 adds that cap explicitly.
─────────────────────────────────────────────────────────────────────────────
"""

import sys
from dotenv import load_dotenv

load_dotenv()  # must run before any LangChain import so LANGCHAIN_* vars are set

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Import all four tools from the module we just built.
# Importing tools also triggers the FAISS index load (module-level code).
from tools import compute_ratios, get_financials, get_price_history, search_filings

# ── Build the agent ───────────────────────────────────────────────────────────
# gpt-4o-mini: cheap, fast, good at tool selection. Swap to gpt-4o for harder
# reasoning without changing any other code.
_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

_tools = [get_financials, compute_ratios, get_price_history, search_filings]

# create_react_agent compiles and returns a LangGraph app.
# We pass the LLM and the tool list; it wires the agent/tool nodes and
# the conditional edge described in the module docstring above.
agent_app = create_react_agent(_llm, _tools)


def run(question: str) -> None:
    """Invoke the agent with a question and print the final answer."""
    print(f"\nQuestion: {question}\n{'─' * 60}")

    result = agent_app.invoke(
        {"messages": [{"role": "user", "content": question}]}
    )

    # result["messages"] is the full conversation including tool calls.
    # The last message is always the model's final text answer.
    final = result["messages"][-1].content
    print(f"\nAnswer:\n{final}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python single_agent.py \"your question here\"")
        print("\nTest questions:")
        print("  Numeric : python single_agent.py \"What is Apple's ROE and free cash flow?\"")
        print("  Filings : python single_agent.py \"What supply chain risks does the company disclose?\"")
        sys.exit(0)

    question = " ".join(sys.argv[1:])
    run(question)

# ── Two questions to test with after setup ────────────────────────────────────
#
# 1. NUMERIC (must trigger compute_ratios, not model arithmetic):
#      python single_agent.py "What is Apple's return on equity and free cash flow?"
#    Verify in LangSmith: the trace must show a compute_ratios tool call.
#    The model should quote the numbers verbatim from the tool output.
#
# 2. FILINGS (must trigger search_filings and cite a page number):
#      python single_agent.py "What supply chain risks does the company disclose?"
#    Verify: the answer should reference a page number (e.g. "page 14").
#    If search_filings returns "index not loaded", run ingest.py first.
