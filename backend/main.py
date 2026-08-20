"""
main.py

FastAPI application entry point.
Phase 5: Adds /research and /resume endpoints for streaming graph updates via SSE.
"""
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.types import Command

from graph import build_graph

app = FastAPI(title="Equity Research API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app_graph = build_graph()

class ResearchRequest(BaseModel):
    ticker: str
    question: str
    thread_id: str

class ResumeRequest(BaseModel):
    thread_id: str
    decision: str

def stream_graph_updates(graph_iterator, config):
    """
    Consumes graph.stream(...) and yields SSE formatted strings.
    Handles the GraphInterrupt gracefully and emits 'interrupt' or 'final' events.
    """
    try:
        for update in graph_iterator:
            for node_name, node_output in update.items():
                yield f"data: {json.dumps({'type': 'node', 'node': node_name, 'summary': f'Finished {node_name}'})}\n\n"
    except Exception as exc:
        if "interrupt" in type(exc).__name__.lower():
            # Graph interrupted!
            snap = app_graph.get_state(config)
            interrupt_val = {}
            if snap.tasks:
                for task in snap.tasks:
                    if task.interrupts:
                        interrupt_val = task.interrupts[0].value
                        break
            draft = interrupt_val.get("draft") or snap.values.get("draft", "")
            yield f"data: {json.dumps({'type': 'interrupt', 'draft': draft})}\n\n"
            return
        else:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
            return
    
    # Check if graph ended normally or just returned pending without exception
    snap = app_graph.get_state(config)
    if snap.next:
        interrupt_val = {}
        if snap.tasks:
            for task in snap.tasks:
                if task.interrupts:
                    interrupt_val = task.interrupts[0].value
                    break
        draft = interrupt_val.get("draft") or snap.values.get("draft", "")
        yield f"data: {json.dumps({'type': 'interrupt', 'draft': draft})}\n\n"
    else:
        # Final output
        memo_str = snap.values.get("draft", "{}")
        try:
            memo = json.loads(memo_str)
        except json.JSONDecodeError:
            memo = {"thesis": memo_str}
            
        yield f"data: {json.dumps({'type': 'final', 'memo': memo})}\n\n"

@app.post("/research")
async def research(req: ResearchRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    
    # If the state is already in progress and the user hits research again,
    # it's safe to just call stream on the existing config. But LangGraph
    # requires an initial input if it's a new run.
    # To handle "refreshing mid-run", we just fetch state.
    snap = app_graph.get_state(config)
    if snap.next or snap.values:
        # Already exists! Just resume with no new state to fetch the stream
        # Or wait, if we are mid run, we shouldn't overwrite initial state.
        # But if we want to "pick up the existing run", if it's interrupted, we just yield the interrupt.
        if snap.next:
            # We are currently paused at an interrupt, just yield the interrupt state immediately.
            def fast_interrupt():
                interrupt_val = {}
                if snap.tasks:
                    for task in snap.tasks:
                        if task.interrupts:
                            interrupt_val = task.interrupts[0].value
                            break
                draft = interrupt_val.get("draft") or snap.values.get("draft", "")
                yield f"data: {json.dumps({'type': 'interrupt', 'draft': draft})}\n\n"
            return StreamingResponse(fast_interrupt(), media_type="text/event-stream")
            
        # If it's already completely done:
        if snap.values.get("approved"):
            def fast_final():
                memo_str = snap.values.get("draft", "{}")
                try:
                    memo = json.loads(memo_str)
                except json.JSONDecodeError:
                    memo = {"thesis": memo_str}
                yield f"data: {json.dumps({'type': 'final', 'memo': memo})}\n\n"
            return StreamingResponse(fast_final(), media_type="text/event-stream")

    # New run
    initial_state = {
        "ticker": req.ticker,
        "question": req.question,
        "messages": [{"role": "user", "content": req.question}],
        "evidence": [],
        "visited": [],
        "valuation": None,
        "draft": None,
        "critique": None,
        "revision_count": 0,
        "approved": False,
    }
    iterator = app_graph.stream(initial_state, config, stream_mode="updates")
    return StreamingResponse(stream_graph_updates(iterator, config), media_type="text/event-stream")

@app.post("/resume")
async def resume(req: ResumeRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    iterator = app_graph.stream(Command(resume=req.decision), config, stream_mode="updates")
    return StreamingResponse(stream_graph_updates(iterator, config), media_type="text/event-stream")

@app.get("/health")
def health() -> dict:
    """Liveness check — returns 200 as long as the process is running."""
    return {"status": "ok"}
