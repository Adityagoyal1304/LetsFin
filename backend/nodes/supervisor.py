from typing import Literal
from pydantic import BaseModel
from langgraph.graph import END
from langgraph.types import Command
from state import ResearchState
from llm_config import get_router_llm

class Route(BaseModel):
    next_agent: Literal["fundamentals_agent", "filings_agent", "market_agent", "FINISH"]

def supervisor_agent(state: ResearchState) -> Command:
    """Routes to the next appropriate worker agent or finishes."""
    visited = state.get("visited", [])
    
    # Hard safety cap
    if len(visited) >= 3:
        return Command(goto=END)

    system_prompt = (
        "You are a research supervisor. Based on the user's question and the evidence gathered so far, "
        "decide which worker should go next to gather missing information. "
        "Workers available:\n"
        "- fundamentals_agent: for financial metrics, income statements, balance sheets, and ratios.\n"
        "- filings_agent: for qualitative SEC filings text, risk factors, supply chain, management discussion.\n"
        "- market_agent: for stock price history, 52-week highs/lows, returns.\n"
        "Do NOT pick a worker that has already been visited.\n"
        f"Visited workers: {visited}\n"
        "If you have enough information to answer the question, or all necessary workers have been visited, pick FINISH."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": state["question"]}
    ]
    
    # Include current evidence context if any
    if state.get("evidence"):
        evidence_str = "\n".join([f"{e['key']}: {e['value']}" for e in state["evidence"]])
        messages.append({"role": "user", "content": f"Evidence so far:\n{evidence_str}"})

    router_llm = get_router_llm()
    router = router_llm.with_structured_output(Route)
    decision = router.invoke(messages)
    
    if decision.next_agent == "FINISH":
        return Command(goto=END)
    
    # Fallback to prevent cycles if model disobeys instructions
    if decision.next_agent in visited:
        return Command(goto=END)
        
    return Command(goto=decision.next_agent)
