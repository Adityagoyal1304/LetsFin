# Phase 1 — Verification Guide

Run every block below in order.  
All commands assume your terminal is at the repo root (`letsfin/`).

---

## 1. Create and activate the virtual environment

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

> **If pip reports a version conflict**, drop the pinned version of the
> conflicting package (e.g. change `langchain==0.3.14` to `langchain`)
> and re-run. Pin it again once pip resolves it.

---

## 2. Copy and fill in the secrets file

```bash
cp .env.example .env
# Open .env and add your OPENAI_API_KEY value.
```

---

## 3. Verify `finance_core.py` — pure Python, no API calls needed

```bash
python - <<'EOF'
from finance_core import roe, debt_to_equity, free_cash_flow, cagr, simple_dcf

# ROE: Apple FY2023 rough numbers
print("ROE:          ", roe(97_000, 62_000))          # ~1.565

# D/E: company with $50 B debt, $25 B equity
print("D/E:          ", debt_to_equity(50_000, 25_000)) # 2.0

# FCF: $120 B operating cash, $11 B capex
print("FCF:          ", free_cash_flow(120_000, 11_000)) # 109_000

# CAGR: $100 growing to $161 over 5 years
print("CAGR:         ", round(cagr(100, 161, 5), 4))    # ~0.10 (10 %)

# DCF: FCF=$5 B, growth=8%, discount=10%, terminal=15x, 5 years
print("DCF:          ", round(simple_dcf(5_000, 0.08, 0.10, 15), 2))

# Edge cases — all should print None, not crash
print("ROE None:     ", roe(None, 100))
print("D/E zero eq:  ", debt_to_equity(50, 0))
print("CAGR neg:     ", cagr(-100, 200, 5))
EOF
```

**Expected output** (values are approximate):
```
ROE:           1.5645...
D/E:           2.0
FCF:           109000
CAGR:          0.1
DCF:           <positive number, roughly 85 000 – 110 000>
ROE None:      None
D/E zero eq:   None
CAGR neg:      None
```

---

## 4. Verify `ingest.py` — requires OPENAI_API_KEY and a PDF

### 4a. Build an index

```bash
# Replace sample.pdf with any PDF you have on hand.
python ingest.py --pdf sample.pdf --index ./indexes/sample
```

**Expected output:**
```
Loading PDF: sample.pdf
  Pages loaded: <N>
  Chunks created: <M>
Embedding chunks (this calls the OpenAI API) …
  Index saved to: ./indexes/sample
Done. <M> chunks indexed.
```

Two files will appear in `./indexes/sample/`: `index.faiss` and `index.pkl`.

### 4b. Query the index

```bash
python ingest.py --index ./indexes/sample --query "revenue growth"
```

**Expected output:** 4 numbered chunks printed with their source filename and page number.  
The content should be topically related to "revenue growth" — not random pages.

---

## 5. Verify `main.py` — FastAPI health check

```bash
uvicorn main:app --reload --port 8000
```

In a second terminal (still inside `backend/`):

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{"status":"ok"}
```

You can also open `http://localhost:8000/docs` in a browser to see the
auto-generated Swagger UI — it should list one endpoint: `GET /health`.

---

## 6. Confirm `.env` is not tracked by git

```bash
# From repo root (letsfin/)
git init
git status
```

`.env` must appear under **"Untracked files"** or not appear at all —  
it must NOT appear under "Changes to be committed".

---

## What was uncertain

- **Pinned versions in `requirements.txt`** were current at time of writing (Aug 2026).
  If `pip install` fails with a resolver error, drop the pin on the conflicting
  package, let pip choose, then re-pin to whatever it resolved to.
- **`allow_dangerous_deserialization=True`** in `ingest.py` is a LangChain guard
  introduced in v0.2.x. It is required for local FAISS loads; the flag is intentional.
- **`pypdf`** (not `PyPDF2`) is the backend required by the current `PyPDFLoader`.
  If you see an import error mentioning `pypdf`, confirm `pypdf` (not `PyPDF2`) is installed.
