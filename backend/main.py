"""
main.py

FastAPI application entry point.
Phase 1: only a health endpoint so we can confirm the server boots.
Later phases will add the /stream and /report endpoints.
"""

from fastapi import FastAPI

app = FastAPI(title="Equity Research API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    """Liveness check — returns 200 as long as the process is running."""
    return {"status": "ok"}
