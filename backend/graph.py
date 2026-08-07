import os
import sqlite3
import pprint
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, START
from langgraph.checkpoint.sqlite import SqliteSaver

from state import ResearchState
from nodes.workers import fundamentals_agent, filings_agent, market_agent
from nodes.supervisor import supervisor_agent

def build_graph():
    builder = StateGraph(ResearchState)
    
    # Add nodes
    builder.add_node("supervisor", supervisor_agent)
    builder.add_node("fundamentals_agent", fundamentals_agent)
    builder.add_node("filings_agent", filings_agent)
    builder.add_node("market_agent", market_agent)
    
    # Entry point
    builder.add_edge(START, "supervisor")
    
    # Worker nodes return to supervisor
    # The supervisor's edges are dynamically determined by returning Command(goto="...")
    builder.add_edge("fundamentals_agent", "supervisor")
    builder.add_edge("filings_agent", "supervisor")
    builder.add_edge("market_agent", "supervisor")
    
    # Setup persistence
    conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
    memory = SqliteSaver(conn)
    
    graph = builder.compile(checkpointer=memory)
    return graph

if __name__ == "__main__":
    import sys
    
    # Create the graph and save a visualization
    graph = build_graph()
    try:
        png_data = graph.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as f:
            f.write(png_data)
        print("Saved graph architecture to graph.png")
    except Exception as e:
        print(f"Warning: could not generate graph.png: {e}")
        
    thread_id = "test_thread_1"
    if len(sys.argv) > 1:
        thread_id = sys.argv[1]
        
    config = {"configurable": {"thread_id": thread_id}}
    
    ticker = "AAPL"
    question = f"What is the return on equity and 52-week high for {ticker}?"
    
    print(f"\nRunning query: {question}")
    print(f"Thread ID: {thread_id}\n")
    
    initial_state = {
        "ticker": ticker,
        "question": question,
        "messages": [{"role": "user", "content": question}],
        "evidence": [],
        "visited": []
    }
    
    # Run the graph
    result = graph.invoke(initial_state, config)
    
    print("\n" + "="*60)
    print("FINAL EVIDENCE GATHERED:")
    print("="*60)
    pprint.pprint(result.get("evidence", []))
    print("="*60)
    print(f"Workers visited: {result.get('visited', [])}")
