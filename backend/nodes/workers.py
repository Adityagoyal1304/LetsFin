import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from state import ResearchState
from llm_config import get_worker_llm
from tools import get_financials, compute_ratios, get_price_history, search_filings

# Each worker receives its own narrow sub-question, not the full user question.
# This stops the 70B model from trying to web-search when it sees phrases like
# "52-week" — a known Groq issue where the model hallucinates a brave_search tool.
_SYSTEM = SystemMessage(content=(
    "You are a specialist financial research agent. "
    "You MUST only use the tools explicitly provided to you. "
    "Do NOT call brave_search, web_search, or any other tool not in your list. "
    "Answer only with information returned by your tools."
))


def _run_agent(agent, question: str) -> str:
    """Run a sub-agent with a targeted question; return its final text.
    Catches Groq 400 errors (hallucinated tool calls) gracefully.
    """
    try:
        result = agent.invoke({"messages": [_SYSTEM, HumanMessage(content=question)]})
        return result["messages"][-1].content
    except Exception as exc:
        # Groq raises BadRequestError when the model tries to call a tool that
        # wasn't in the request (e.g. brave_search).  Return the error as text
        # so the graph can continue and the critic / writer handle the gap.
        return f"[agent error — {type(exc).__name__}: {str(exc)[:300]}]"


def fundamentals_agent(state: ResearchState) -> dict:
    """Agent that uses financial statement tools to gather fundamental data."""
    ticker = state.get("ticker", "the company")
    agent  = create_react_agent(get_worker_llm(), [get_financials, compute_ratios])
    answer = _run_agent(agent, f"What is the return on equity and free cash flow for {ticker}?")

    return {
        "evidence": [{
            "key": "fundamentals",
            "value": answer,
            "source": "fundamentals_agent",
            "as_of": datetime.date.today().isoformat(),
        }],
        "visited": ["fundamentals_agent"],
    }


def filings_agent(state: ResearchState) -> dict:
    """Agent that searches the indexed SEC filing PDF for qualitative insights."""
    question = state.get("question", "What are the key risk factors?")
    agent    = create_react_agent(get_worker_llm(), [search_filings])
    answer   = _run_agent(agent, question)

    return {
        "evidence": [{
            "key": "filings",
            "value": answer,
            "source": "filings_agent",
            "as_of": datetime.date.today().isoformat(),
        }],
        "visited": ["filings_agent"],
    }


def market_agent(state: ResearchState) -> dict:
    """Agent that fetches stock price history and market data."""
    ticker = state.get("ticker", "the company")
    agent  = create_react_agent(get_worker_llm(), [get_price_history])
    answer = _run_agent(agent, f"What is the 1-year price range and recent return for {ticker}?")

    return {
        "evidence": [{
            "key": "market",
            "value": answer,
            "source": "market_agent",
            "as_of": datetime.date.today().isoformat(),
        }],
        "visited": ["market_agent"],
    }

