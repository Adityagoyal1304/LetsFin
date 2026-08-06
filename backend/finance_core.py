"""
finance_core.py

Pure Python financial math — no LangChain, no LLMs.
These functions are imported by the agent's tools later (Phase 3).
Keeping them here means the logic can be unit-tested independently
and the tool layer stays thin.

Why return None instead of raising?
  The agent will call these inside tool functions. A None result lets
  the critic node flag "data unavailable" rather than crashing the graph.
"""


def roe(net_income: float | None, shareholders_equity: float | None) -> float | None:
    """Return on Equity = Net Income / Shareholders' Equity.

    Tells you how much profit the company generates per dollar of equity.
    """
    if net_income is None or shareholders_equity is None:
        return None
    if shareholders_equity == 0:
        return None
    return net_income / shareholders_equity


def debt_to_equity(total_debt: float | None, total_equity: float | None) -> float | None:
    """Debt-to-Equity = Total Debt / Total Equity.

    A higher ratio means more leverage; above ~2 is generally considered risky.
    """
    if total_debt is None or total_equity is None:
        return None
    if total_equity == 0:
        return None
    return total_debt / total_equity


def free_cash_flow(
    operating_cashflow: float | None, capex: float | None
) -> float | None:
    """Free Cash Flow = Operating Cash Flow - Capital Expenditures.

    Capex is often reported as a negative number in financial statements;
    pass the raw value and the subtraction handles sign correctly either way.
    """
    if operating_cashflow is None or capex is None:
        return None
    return operating_cashflow - capex


def cagr(
    start_value: float | None, end_value: float | None, years: float | None
) -> float | None:
    """Compound Annual Growth Rate = (end / start) ^ (1 / years) - 1.

    Expresses the steady annual growth rate that gets you from start to end.
    """
    if start_value is None or end_value is None or years is None:
        return None
    if start_value == 0 or years == 0:
        return None
    # Negative start values produce complex numbers; guard against that.
    if start_value < 0:
        return None
    return (end_value / start_value) ** (1 / years) - 1


def simple_dcf(
    fcf: float | None,
    growth_rate: float | None,
    discount_rate: float | None,
    terminal_multiple: float | None,
    years: int = 5,
) -> float | None:
    """Discounted Cash Flow valuation: sum of PV of projected FCFs plus terminal value.

    Projects FCF forward for `years` periods at `growth_rate`, discounts each
    period at `discount_rate`, then adds a terminal value = final_FCF * terminal_multiple
    also discounted back to today.

    All rates should be decimals (e.g., 0.10 for 10 %).
    """
    if any(v is None for v in [fcf, growth_rate, discount_rate, terminal_multiple]):
        return None
    # Asserts let the type checker know these are non-None beyond this point.
    assert fcf is not None
    assert growth_rate is not None
    assert discount_rate is not None
    assert terminal_multiple is not None
    if discount_rate == 0:
        return None
    if years < 1:
        return None

    pv_sum = 0.0
    current_fcf: float = fcf

    for t in range(1, years + 1):
        current_fcf = current_fcf * (1 + growth_rate)
        # Why discount_rate + 1? Each period's cash is worth less today by (1+r)^t.
        pv_sum += current_fcf / (1 + discount_rate) ** t

    # Terminal value: the business keeps generating cash beyond the forecast window.
    terminal_value = current_fcf * terminal_multiple
    pv_terminal = terminal_value / (1 + discount_rate) ** years

    return pv_sum + pv_terminal
