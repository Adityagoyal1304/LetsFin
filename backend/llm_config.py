from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv, find_dotenv

def _ensure_groq_key():
    if not os.environ.get("GROQ_API_KEY"):
        backend_env = os.path.join(os.path.dirname(__file__), ".env")
        root_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        for env_path in [backend_env, root_env]:
            if os.path.isfile(env_path):
                load_dotenv(env_path, override=True)
                if os.environ.get("GROQ_API_KEY"):
                    break
        if not os.environ.get("GROQ_API_KEY"):
            for env_path in [backend_env, root_env]:
                if os.path.isfile(env_path):
                    try:
                        with open(env_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f:
                                line = line.strip()
                                if line.startswith("GROQ_API_KEY="):
                                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                                    if key:
                                        os.environ["GROQ_API_KEY"] = key
                                        break
                    except Exception:
                        pass
                if os.environ.get("GROQ_API_KEY"):
                    break

_ensure_groq_key()

_router_llm = None
_worker_llm = None

def get_router_llm():
    global _router_llm
    if _router_llm is None:
        _ensure_groq_key()
        if not os.environ.get("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY environment variable is missing.")
        model = os.environ.get("GROQ_ROUTER_MODEL", "openai/gpt-oss-20b")
        _router_llm = ChatGroq(model=model, temperature=0)
    return _router_llm

def get_worker_llm():
    global _worker_llm
    if _worker_llm is None:
        _ensure_groq_key()
        if not os.environ.get("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY environment variable is missing.")
        model = os.environ.get("GROQ_WORKER_MODEL", "openai/gpt-oss-120b")
        _worker_llm = ChatGroq(model=model, temperature=0)
    return _worker_llm

def get_writer_llm():
    return get_worker_llm()

def get_critic_llm():
    return get_worker_llm()
