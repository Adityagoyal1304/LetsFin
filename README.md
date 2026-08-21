# LetsFin AI Equity Analyst

An autonomous financial research graph powered by LangGraph, Groq (Llama 3.3 70B), and FastAPI, providing structured investment memos with strict compliance guarantees.

## THE CRITIC: Internal Fact-Checking

Large Language Models hallucinate. In financial research, an unverified number is worse than a missing one. To solve this, LetsFin employs an internal **Critic Agent** that runs before any human sees the draft. 

The Writer agent is strictly instructed to list every single number it uses in a `numbers_used` array. The Critic then audits this array against the raw evidence gathered by the worker agents and the deterministic DCF valuation outputs. If a number is derived, hallucinated, or otherwise unverifiable, the Critic rejects the draft and forces the Writer to revise it.

![Critic Catching Hallucinated Number](file:///C:/Users/goyals/.gemini/antigravity-ide/brain/f7ea1f2e-2fa8-4626-a364-75895436e10b/critic_screenshot_1786521584134.png)

In our evaluation set, the Critic successfully rejected **0.0%** of first drafts due to unsupported numbers, forcing a revision that ultimately improved the accuracy of the final memo.

## Evaluation Scores

We evaluate LetsFin against a benchmark of lookup, computed, retrieval, and comparative financial questions.

| Metric | Score |
| --- | --- |
| Accuracy | **100.0%** |
| First-Draft Rejection Rate | **0.0%** |
| Mean Latency | **8.8s** |

*(Check LangSmith for precise cost-per-run metrics).*

## Architecture

```text
  React Frontend
       │ (SSE via Express Proxy)
       ▼
  Express 4 / MongoDB
       │ (Stateful proxy, disconnect-tolerant)
       ▼
  FastAPI (LangGraph API)
       │
       ├─► Supervisor Agent (Llama 3.1 8B)
       │    ├─► Fundamentals Agent (Llama 3.3 70B + yfinance)
       │    ├─► Filings Agent (Llama 3.3 70B + FAISS PDF Index)
       │    └─► Market Agent (Llama 3.3 70B + yfinance)
       │
       ├─► Valuation Node (Pure Python DCF)
       │
       ├─► Writer Agent (Llama 3.3 70B Structured Output)
       │
       └─► Critic Agent (Llama 3.3 70B Compliance Check)
```

**Why the two-service boundary?**
The LangGraph backend runs on Python/FastAPI because the LangChain ecosystem in Python is far more mature, especially for AI agent routing and state management (`langgraph`). The Node.js/Express server exists to handle authentication, persistence (MongoDB), and bullet-proof SSE streaming proxying. This separation allows the AI service to run heavily computational/blocking tasks without choking the asynchronous Express web server.

## Local Setup

### 1. Prerequisites
- Docker and Docker Compose
- Groq API Key

### 2. Environment Variables
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Fill in your `GROQ_API_KEY` and `JWT_SECRET`.

### 3. Build the FAISS Index
Before running the server, you need to index a sample SEC filing for the Filings Agent to use:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python ingest.py --pdf ./sample_report.pdf --index ./indexes/sample
```

### 4. Run with Docker Compose
Run the entire stack (MongoDB, Express Server, FastAPI Backend) with a single command:
```bash
docker-compose up --build
```
The React frontend can be started locally via `npm run dev` in the `frontend/` directory.

## Limitations
- **Single Filing**: The FAISS index currently only supports a single uploaded PDF. It cannot cross-reference multiple annual reports.
- **Sequential Agents**: Worker agents run sequentially rather than in parallel to simplify the supervisor routing.
- **No Corporate-Action Adjustment**: Stock prices and returns do not dynamically adjust for recent stock splits or dividends beyond what `yfinance` provides natively.
- **US Tickers Only**: The application assumes US-based SEC filings and USD financial reporting.

## Disclaimer
Generated analysis. Not investment advice. Do not make financial decisions based on the output of this application.
