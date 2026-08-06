import operator
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class ResearchState(TypedDict):
    ticker: str
    question: str
    messages: Annotated[list, add_messages]
    
    # We use Annotated with operator.add so that each node can return a list
    # of new evidence dicts, and LangGraph will append them to the existing list.
    # If this were a plain list, returning new evidence from a node would overwrite
    # all previous evidence gathered by earlier nodes.
    evidence: Annotated[list[dict], operator.add]
    
    # We use Annotated with operator.add so nodes can append their names.
    visited: Annotated[list[str], operator.add]
    
    next_agent: str
