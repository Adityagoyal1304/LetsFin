"""
tools.py

LangChain @tool wrappers that give the agent access to financial data and filings.

Design rules applied here:
  1. Tools NEVER raise. Any exception is caught and returned as a readable string.
     If a tool raises into the agent loop, LangGraph treats it as a node crash —
     much harder to debug than "Could not fetch X: reason".
  2. The FAISS index is loaded ONCE at module import (see comment below).
  3. Docstrings are written for the model, not for the developer. They become the
     tool description the LLM reads when deciding which tool to call.
"""

import os
import warnings

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from langchain_core.tools import tool

# Suppress the langchain-community sunset warning.
# The standalone replacements are not yet on PyPI; community imports are correct.
warnings.filterwarnings("ignore", message=".*langchain-community.*")

load_dotenv()

import finance_core  # sibling module — pure Python, no AI

# ── Load the FAISS retriever once at module import ───────────────────────────
# WHY here and not inside search_filings()?
#   Every call to search_filings would pay two cold-start costs:
#     - OpenAI embedding client initialisation:  ~200 ms
#     - FAISS index file read from disk:          ~300 ms for a 100-page PDF
#   At module level, these costs are paid once when `tools` is first imported
#   and the retriever object lives in memory for every subsequent call.
#   The trade-off: if the index is missing or torch fails to load, the module
#   still imports cleanly — search_filings returns a helpful message instead.

_FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./indexes/sample")
_retriever = None

try:
    # These imports live inside try because they chain-import torch, which
    # can fail on Windows if the Visual C++ runtime DLLs are missing.
    # Keeping them here means a torch failure degrades only search_filings —
    # the other three tools are completely unaffected.
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS

    _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    _db = FAISS.load_local(
        _FAISS_INDEX_PATH,
        _embeddings,
        allow_dangerous_deserialization=True,
    )
    _retriever = _db.as_retriever(search_kwargs={"k": 4})
except Exception:
    # Silently skip — search_filings will report the issue to the agent.
    pass


# ── Private helpers ───────────────────────────────────────────────────────────

def _safe_val(df: pd.DataFrame, row: str, col: int = 0):
    """Return float at df.loc[row].iloc[col], or None if missing / NaN."""
    try:
        if df is None or df.empty:
            return None
        if row in df.index and col < len(df.columns):
            v = df.loc[row].iloc[col]
            # df.loc[row] returns a DataFrame when the index has duplicates;
            # squeeze to a scalar before the isna check.
            if hasattr(v, "iloc"):
                v = v.iloc[0]
            return None if pd.isna(v) else float(v.item() if hasattr(v, "item") else v)  # type: ignore[arg-type]
    except Exception:
        pass
    return None


def _fy(df: pd.DataFrame) -> str:
    """Return 'FY2024' from the first (most-recent) Timestamp column."""
    try:
        col = df.columns[0]
        # Always coerce to pd.Timestamp — handles both Timestamp and string columns
        ts = pd.to_datetime(col)
        return "FY" + str(ts.year)
    except Exception:
        return "FY?"


def _b(v) -> str:
    """Format a dollar value in billions, or 'N/A'."""
    return f"${v / 1e9:.2f}B" if v is not None else "N/A"


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def get_financials(ticker: str) -> str:
    """
    Fetch key income-statement, balance-sheet and cash-flow figures for a stock.

    Returns revenue, net income, total debt, stockholders equity, operating cash
    flow, and capital expenditure for the most recent fiscal year, each labelled
    with the fiscal year it covers.

    Use this tool when you need the raw numbers before computing ratios, or when
    the user asks 'what was revenue / net income / debt?'
    """
    try:
        t = yf.Ticker(ticker)
        inc = t.income_stmt
        bs  = t.balance_sheet
        cf  = t.cash_flow

        if inc is None or inc.empty:
            return f"Could not fetch financials for {ticker}: no data returned. Check the ticker symbol."

        fy      = _fy(inc)
        revenue = _safe_val(inc, "Total Revenue")
        ni      = _safe_val(inc, "Net Income")
        debt    = _safe_val(bs,  "Total Debt")
        equity  = _safe_val(bs,  "Stockholders Equity")
        op_cf   = _safe_val(cf,  "Operating Cash Flow")
        capex   = _safe_val(cf,  "Capital Expenditure")

        return (
            f"Financials for {ticker.upper()} ({fy}):\n"
            f"  Revenue:              {_b(revenue)}\n"
            f"  Net Income:           {_b(ni)}\n"
            f"  Total Debt:           {_b(debt)}\n"
            f"  Stockholders Equity:  {_b(equity)}\n"
            f"  Operating Cash Flow:  {_b(op_cf)}\n"
            f"  Capital Expenditure:  {_b(capex)}\n"
        )
    except Exception as e:
        return f"Could not fetch financials for {ticker}: {e}"


@tool
def compute_ratios(ticker: str) -> str:
    """
    Compute ROE, debt-to-equity ratio, and free cash flow for a stock using
    deterministic Python formulas — the model must not perform any arithmetic.

    Formulas used:
      ROE = Net Income / Stockholders Equity
      D/E = Total Debt / Stockholders Equity
      FCF = Operating Cash Flow - Capital Expenditure

    Use this tool whenever the user asks about financial health, profitability,
    or leverage, or asks 'is this company in good financial shape?'
    """
    try:
        t = yf.Ticker(ticker)
        inc = t.income_stmt
        bs  = t.balance_sheet
        cf  = t.cash_flow

        if inc is None or inc.empty:
            return f"Could not compute ratios for {ticker}: no data returned. Check the ticker symbol."

        fy     = _fy(inc)
        ni     = _safe_val(inc, "Net Income")
        equity = _safe_val(bs,  "Stockholders Equity")
        debt   = _safe_val(bs,  "Total Debt")
        op_cf  = _safe_val(cf,  "Operating Cash Flow")
        capex  = _safe_val(cf,  "Capital Expenditure")

        roe_v = finance_core.roe(ni, equity)
        de_v  = finance_core.debt_to_equity(debt, equity)
        fcf_v = finance_core.free_cash_flow(op_cf, capex)

        roe_str = f"{roe_v * 100:.1f}%" if roe_v is not None else "N/A"
        de_str  = f"{de_v:.2f}x"        if de_v  is not None else "N/A"

        return (
            f"Ratios for {ticker.upper()} ({fy}):\n"
            f"  ROE:             {roe_str}  (>15% is generally considered strong)\n"
            f"  Debt-to-Equity:  {de_str}   (>2x is often considered high leverage)\n"
            f"  Free Cash Flow:  {_b(fcf_v)}\n"
        )
    except Exception as e:
        return f"Could not compute ratios for {ticker}: {e}"


@tool
def get_price_history(ticker: str, period: str = "1y") -> str:
    """
    Fetch the latest closing price, the period high and low, and the total
    price return over the requested period for a stock.

    'period' must be a valid yfinance period string:
      1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max

    Use this tool for questions about recent price performance, momentum, or
    how far the stock is from its high.
    """
    try:
        t    = yf.Ticker(ticker)
        hist = t.history(period=period)

        if hist is None or hist.empty:
            return f"Could not fetch price history for {ticker}: no data returned. Check the ticker symbol."

        latest  = hist["Close"].iloc[-1]
        high    = hist["Close"].max()
        low     = hist["Close"].min()
        start   = hist["Close"].iloc[0]
        ret_pct = (latest - start) / start * 100

        return (
            f"Price data for {ticker.upper()} (period={period}):\n"
            f"  Latest Close:   ${latest:.2f}\n"
            f"  Period High:    ${high:.2f}\n"
            f"  Period Low:     ${low:.2f}\n"
            f"  Period Return:  {ret_pct:+.1f}%\n"
        )
    except Exception as e:
        return f"Could not fetch price history for {ticker}: {e}"


@tool
def search_filings(query: str) -> str:
    """
    Search the pre-indexed annual report PDF for passages relevant to the query.
    Returns the top 4 matching text chunks, each prefixed with its source
    filename and page number so the answer can cite a specific page.

    Use this tool for qualitative questions: risk factors, business strategy,
    management discussion, competitive landscape, or any question that needs
    the company's own words rather than numbers from a live data feed.

    Prerequisite: run `python ingest.py --pdf <file.pdf> --index ./indexes/sample`
    once before using this tool.
    """
    if _retriever is None:
        return (
            f"Filing index is not loaded. "
            f"Run: python ingest.py --pdf <your_pdf> --index {_FAISS_INDEX_PATH}"
        )
    try:
        docs = _retriever.invoke(query)
        if not docs:
            return f"No relevant passages found for: '{query}'"

        parts = []
        for i, doc in enumerate(docs, 1):
            src  = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", "?")
            # Page from PyPDFLoader is 0-indexed; add 1 for human-readable citation.
            try:
                page_num = int(page) + 1  # PyPDFLoader is 0-indexed
            except (ValueError, TypeError):
                page_num = page  # fallback: show raw value if not an int
            parts.append(f"[{i}] {src}, page {page_num}:\n{doc.page_content[:400]}")

        return "\n\n".join(parts)
    except Exception as e:
        return f"Could not search filings: {e}"
