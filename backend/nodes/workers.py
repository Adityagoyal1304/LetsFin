import datetime
from langgraph.prebuilt import create_react_agent
from state import ResearchState
from llm_config import worker_llm
from tools import get_financials, compute_ratios, get_price_history, search_filings

def fundamentals_agent(state: ResearchState) -> dict:
    """Agent that uses financial tools to answer fundamental questions."""
    agent = create_react_agent(worker_llm, [get_financials, compute_ratios])
    result = agent.invoke({"messages": state["messages"]})
    last_msg = result["messages"][-1].content
    
    return {
        "evidence": [{
            "key": "fundamentals",
            "value": last_msg,
            "source": "fundamentals_agent",
            "as_of": datetime.date.today().isoformat()
        }],
        "visited": ["fundamentals_agent"]
    }

def filings_agent(state: ResearchState) -> dict:
    """Agent that searches SEC filings for qualitative insights."""
    agent = create_react_agent(worker_llm, [search_filings])
    result = agent.invoke({"messages": state["messages"]})
    last_msg = result["messages"][-1].content
    
    return {
        "evidence": [{
            "key": "filings",
            "value": last_msg,
            "source": "filings_agent",
            "as_of": datetime.date.today().isoformat()
        }],
        "visited": ["filings_agent"]
    }

def market_agent(state: ResearchState) -> dict:
    """Agent that fetches price history and market data."""
    agent = create_react_agent(worker_llm, [get_price_history])
    result = agent.invoke({"messages": state["messages"]})
    last_msg = result["messages"][-1].content
    
    return {
        "evidence": [{
            "key": "market",
            "value": last_msg,
            "source": "market_agent",
            "as_of": datetime.date.today().isoformat()
        }],
        "visited": ["market_agent"]
    }
