from langchain_groq import ChatGroq
import os

# Ensure the Groq API key is present
if not os.environ.get("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY environment variable is missing.")

# Fast, cheap model for routing and decision making
router_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

# Larger, more capable model for tool calling, reasoning, and synthesis
worker_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
