from langchain_groq import ChatGroq
import os

_router_llm = None
_worker_llm = None

def get_router_llm():
    global _router_llm
    if _router_llm is None:
        if not os.environ.get("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY environment variable is missing.")
        _router_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    return _router_llm

def get_worker_llm():
    global _worker_llm
    if _worker_llm is None:
        if not os.environ.get("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY environment variable is missing.")
        _worker_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    return _worker_llm

def get_writer_llm():
    return get_worker_llm()

def get_critic_llm():
    return get_worker_llm()
