"""The three financial statements and the key ratios, from Yahoo Finance (yfinance).

Tools: get_company_profile, get_income_statement, get_balance_sheet,
       get_cash_flow_statement, compute_key_ratios

Money comes back ready to show, such as ₹10,57,219 Cr (see india.py).

compute_key_ratios says whether the company is profitable and whether cash backs the
profit, and scores it out of 10, one point per check:
8-10 STRONG, 6-7 SOLID, 4-5 MIXED, 0-3 WEAK.
"""

import pandas as pd
import yfinance as yf
from strands import tool

from ..india import format_money


def _three_years(table, rows, currency):
    """Keep the chosen rows for the newest three years, ready to show, such as ₹10,57,219 Cr."""
    result = {}
    for row in rows:
        if row not in table.index:
            continue
        result[row] = {}
        for date, value in table.loc[row].iloc[:3].items():
            if pd.notna(value):
                result[row][str(date.year)] = format_money(value, currency)
    return result


@tool
def get_income_statement(ticker: str) -> dict:
    """Revenue and profit for the last three years.

    Args:
        ticker: The stock symbol, such as TCS.NS or RELIANCE.NS.
    """
    stock = yf.Ticker(ticker)
    rows = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income", "Interest Expense"]
    return _three_years(stock.income_stmt, rows, stock.info.get("financialCurrency"))


@tool
def get_balance_sheet(ticker: str) -> dict:
    """What the company owns and owes for the last three years.

    Args:
        ticker: The stock symbol, such as TCS.NS or RELIANCE.NS.
    """
    stock = yf.Ticker(ticker)
    rows = ["Total Assets", "Total Liabilities Net Minority Interest", "Stockholders Equity",
            "Current Assets", "Current Liabilities", "Total Debt", "Cash And Cash Equivalents"]
    return _three_years(stock.balance_sheet, rows, stock.info.get("financialCurrency"))


@tool
def get_cash_flow_statement(ticker: str) -> dict:
    """Cash from the business, spending on equipment, and free cash flow.

    Args:
        ticker: The stock symbol, such as TCS.NS or RELIANCE.NS.
    """
    stock = yf.Ticker(ticker)
    rows = ["Operating Cash Flow", "Capital Expenditure", "Free Cash Flow"]
    return _three_years(stock.cashflow, rows, stock.info.get("financialCurrency"))


def _number(table, row, year=0):
    """One number from a statement. year=0 is the newest, year=2 is two years before.
    Returns 0 when Yahoo has no value."""
    if row not in table.index or year >= len(table.columns):
        return 0
    value = table.loc[row].iloc[year]
    return 0 if pd.isna(value) else float(value)


def _divide(top, bottom):
    """top / bottom, or 0 when bottom is 0 or negative."""
    return round(top / bottom, 2) if bottom > 0 else 0


@tool
def compute_key_ratios(ticker: str) -> dict:
    """Key ratios, a health score out of 10 and a label: STRONG, SOLID, MIXED or WEAK.

    Args:
        ticker: The stock symbol, such as TCS.NS or RELIANCE.NS.
    """
    stock = yf.Ticker(ticker)
    income = stock.income_stmt
    balance = stock.balance_sheet
    cash_flow = stock.cashflow
    currency = stock.info.get("financialCurrency")

    revenue = _number(income, "Total Revenue")
    profit = _number(income, "Net Income")
    interest = _number(income, "Interest Expense")
    equity = _number(balance, "Stockholders Equity")
    operating_cash = _number(cash_flow, "Operating Cash Flow")
    # real profit, and at least 90% of it arrived as cash
    backed_by_cash = profit > 0 and operating_cash >= profit * 0.9

    ratios = {
        "gross_margin": _divide(_number(income, "Gross Profit"), revenue),
        "net_margin": _divide(profit, revenue),
        "return_on_equity": _divide(profit, equity),
        "debt_to_equity": _divide(_number(balance, "Total Debt"), equity),
        "current_ratio": _divide(_number(balance, "Current Assets"), _number(balance, "Current Liabilities")),
        "interest_coverage": _divide(_number(income, "Operating Income"), interest),
    }

    checks = {
        "Revenue grew over 3 years": revenue > _number(income, "Total Revenue", year=2),
        # a smaller loss isn't growth, so these two also need a real profit
        "Net profit grew over 3 years": profit > 0 and profit > _number(income, "Net Income", year=2),
        "EPS grew over 3 years": profit > 0 and _number(income, "Diluted EPS") > _number(income, "Diluted EPS", year=2),
        "Profit backed by cash": backed_by_cash,
        "Free cash flow is positive": _number(cash_flow, "Free Cash Flow") > 0,
        "Net margin above 10%": ratios["net_margin"] > 0.10,
        "Return on equity above 15%": ratios["return_on_equity"] > 0.15,
        "Debt to equity below 1": equity > 0 and ratios["debt_to_equity"] < 1,
        "Current ratio above 1": ratios["current_ratio"] > 1,
        "Interest covered 3x or no interest": interest == 0 or ratios["interest_coverage"] > 3,
    }
    score = sum(checks.values())  # True counts as 1, False as 0

    if score >= 8:
        label = "STRONG"
    elif score >= 6:
        label = "SOLID"
    elif score >= 4:
        label = "MIXED"
    else:
        label = "WEAK"

    # Is it making a profit, and is that profit backed by real cash coming in?
    profit_by_year = [_number(income, "Net Income", year) for year in range(3)]
    profitability = {
        "status": "PROFITABLE" if profit > 0 else "LOSS-MAKING",
        "profitable_all_3_years": all(p > 0 for p in profit_by_year),
        "net_profit": format_money(profit, currency),
        "operating_cash_flow": format_money(operating_cash, currency),
        # 1.0 or more means every unit of profit arrived as cash
        "cash_to_profit_ratio": _divide(operating_cash, profit),
        "profit_backed_by_cash": backed_by_cash,
    }

    return {"profitability": profitability, "ratios": ratios, "checks": checks,
            "score": f"{score}/10", "label": label}


@tool
def get_company_profile(ticker: str) -> dict:
    """What the company is: name, sector, industry, country and what it sells.

    Args:
        ticker: The stock symbol, such as TCS.NS or RELIANCE.NS.
    """
    info = yf.Ticker(ticker).info
    return {
        "name": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "country": info.get("country"),
        "employees": info.get("fullTimeEmployees"),
        "reporting_currency": info.get("financialCurrency"),
        "what_it_does": (info.get("longBusinessSummary") or "")[:600],
    }

