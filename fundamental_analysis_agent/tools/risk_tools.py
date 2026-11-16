"""The risk register and stress test, worked out in code so the verdict is exact.

Tool: assess_risk

It reuses compute_key_ratios from financial_tools.py for the ratios and checks, adds a
stress test (what if revenue fell 20%?), and counts risk points:
0-1 LOW, 2-3 MODERATE, 4-5 ELEVATED, 6 or more HIGH.
"""

import yfinance as yf
from strands import tool

from ..india import format_money
from .financial_tools import _number, compute_key_ratios

REVENUE_DROP = 0.20  # the stress test: revenue falls 20%


@tool
def assess_risk(ticker: str, news_risk_flags: list[str]) -> dict:
    """Build the risk register, run a stress test and give a risk verdict:
    LOW, MODERATE, ELEVATED or HIGH.

    Args:
        ticker: The stock symbol, such as TCS.NS or RELIANCE.NS.
        news_risk_flags: Risks found in recent headlines, one short line each, such as
            "SEBI order against the promoters". Pass an empty list if there are none.
    """
    key = compute_key_ratios(ticker)  # the same numbers FinancialDataAgent uses
    ratios = key["ratios"]
    checks = key["checks"]
    profitability = key["profitability"]

    stock = yf.Ticker(ticker)
    income = stock.income_stmt
    cash_flow = stock.cashflow
    balance = stock.balance_sheet
    info = stock.info
    beta = info.get("beta")
    currency = info.get("financialCurrency")

    # Stress test: revenue falls 20%, the gross margin stays the same and running
    # costs don't shrink, so operating profit loses 20% of the gross profit.
    gross_profit = _number(income, "Gross Profit")
    operating_income = _number(income, "Operating Income")
    interest = _number(income, "Interest Expense")
    stressed_operating_income = operating_income - REVENUE_DROP * gross_profit
    stress_test = {
        "scenario": "revenue falls 20%",
        "operating_profit_now": format_money(operating_income, currency),
        "operating_profit_after": format_money(stressed_operating_income, currency),
        "still_profitable": stressed_operating_income > 0,
    }
    if interest > 0:
        stress_test["interest_coverage_after"] = round(stressed_operating_income / interest, 2)

    # How many years the cash lasts if the company keeps burning it
    free_cash_flow = _number(cash_flow, "Free Cash Flow")
    cash = _number(balance, "Cash Cash Equivalents And Short Term Investments")
    if cash == 0:  # some companies only report plain cash
        cash = _number(balance, "Cash And Cash Equivalents")
    if free_cash_flow < 0:
        stress_test["years_of_cash_left"] = round(cash / -free_cash_flow, 1)

    # The risk register: every risk found, with its points
    register = []
    if profitability["status"] == "LOSS-MAKING":
        register.append({"risk": "Loss-making", "points": 2,
                         "detail": f"net loss of {format_money(-_number(income, 'Net Income'), currency)}"})
    if not checks["Debt to equity below 1"]:
        if ratios["debt_to_equity"] == 0:  # _divide gives 0 when equity is negative
            detail = "equity is negative: the company owes more than it owns"
        else:
            detail = f"debt to equity {ratios['debt_to_equity']}"
        register.append({"risk": "High debt", "points": 1, "detail": detail})
    if not checks["Current ratio above 1"]:
        register.append({"risk": "Short-term bills exceed short-term assets", "points": 1,
                         "detail": f"current ratio {ratios['current_ratio']}"})
    if not checks["Interest covered 3x or no interest"]:
        register.append({"risk": "Interest barely covered", "points": 1,
                         "detail": f"interest coverage {ratios['interest_coverage']}"})
    if not checks["Free cash flow is positive"]:
        register.append({"risk": "Burning cash", "points": 1,
                         "detail": f"free cash flow {format_money(free_cash_flow, currency)}"})
    if profitability["status"] == "PROFITABLE" and not profitability["profit_backed_by_cash"]:
        register.append({"risk": "Profit not backed by cash", "points": 1,
                         "detail": f"cash to profit ratio {profitability['cash_to_profit_ratio']}"})
    if not checks["Revenue grew over 3 years"]:
        register.append({"risk": "Revenue shrinking", "points": 1,
                         "detail": "revenue is lower than 3 years ago"})
    if beta and beta > 1.5:
        register.append({"risk": "Very volatile share price", "points": 1,
                         "detail": f"beta {round(beta, 2)}: moves about {round(beta, 1)}x as much as the market"})
    if not stress_test["still_profitable"]:
        register.append({"risk": "Fails the stress test", "points": 1,
                         "detail": "operating profit turns negative if revenue falls 20%"})
    if stress_test.get("years_of_cash_left", 99) < 2:
        register.append({"risk": "Cash runs out soon", "points": 1,
                         "detail": f"about {stress_test['years_of_cash_left']} years of cash at today's burn"})
    for flag in news_risk_flags[:2]:  # news counts for at most 2 points
        register.append({"risk": "In the news", "points": 1, "detail": flag})

    points = sum(item["points"] for item in register)
    if points >= 6:
        verdict = "HIGH"
    elif points >= 4:
        verdict = "ELEVATED"
    elif points >= 2:
        verdict = "MODERATE"
    else:
        verdict = "LOW"

    return {"register": register, "stress_test": stress_test, "beta": beta,
            "points": points, "verdict": verdict}
