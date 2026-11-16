"""Is the share price fair? Three checks from Yahoo Finance (yfinance), then one verdict.

Tools: run_dcf_model, get_historical_valuation, get_peer_multiples, combine_valuation_signals

Each check returns a signal, from SIGNIFICANTLY UNDERVALUED to SIGNIFICANTLY OVERVALUED,
using the same cut-offs: within 10% of fair is FAIRLY VALUED, 10-30% off is SLIGHTLY,
and more than 30% off is SIGNIFICANTLY. combine_valuation_signals averages them.

The DCF settings are our own simple choices for Indian companies: 10% growth for 5
years, a 12% discount rate (what Indian investors typically expect from shares) and 5%
growth after that (roughly India's long-run inflation plus some real growth).
"""

import statistics

import yfinance as yf
from strands import tool

from ..india import format_price

GROWTH = 0.10          # free cash flow grows 10% a year for the first 5 years
DISCOUNT = 0.12        # the yearly return an Indian investor expects from shares
FOREVER_GROWTH = 0.05  # growth every year after that
YEARS = 5

POINTS = {
    "SIGNIFICANTLY UNDERVALUED": 2,
    "SLIGHTLY UNDERVALUED": 1,
    "FAIRLY VALUED": 0,
    "SLIGHTLY OVERVALUED": -1,
    "SIGNIFICANTLY OVERVALUED": -2,
}


def _signal(premium_pct):
    """Turn how expensive the stock looks into a label.
    premium_pct is how far the price sits above fair: +40 means 40% too expensive,
    -20 means 20% cheaper than fair."""
    if premium_pct > 30:
        return "SIGNIFICANTLY OVERVALUED"
    if premium_pct > 10:
        return "SLIGHTLY OVERVALUED"
    if premium_pct >= -10:
        return "FAIRLY VALUED"
    if premium_pct >= -30:
        return "SLIGHTLY UNDERVALUED"
    return "SIGNIFICANTLY UNDERVALUED"


def _above_or_below(pct, word_above="above", word_below="below"):
    """Write 21.4 as '21.4% above' and -15.2 as '15.2% below'."""
    return f"{abs(pct):.1f}% {word_above if pct > 0 else word_below}"


def _exchange_rates(info):
    """Daily exchange rates for the last 5 years, to turn statement money into price money.

    Some companies report their statements in one currency and trade in another:
    Infosys (INFY.NS) reports in USD but its price is in INR. Statement numbers must be
    multiplied by the rate before they're compared with the price.
    Returns None when both use the same currency, so nothing needs converting.
    """
    statement_currency = info.get("financialCurrency")
    price_currency = info.get("currency")
    if not statement_currency or not price_currency or statement_currency == price_currency:
        return None
    # Yahoo names exchange rates like "USDINR=X": how many INR one USD buys
    rates = yf.Ticker(f"{statement_currency}{price_currency}=X").history(period="5y")["Close"]
    rates.index = rates.index.tz_localize(None)  # drop the time zone so dates compare
    return rates


@tool
def run_dcf_model(ticker: str) -> dict:
    """Estimate the stock's value per share from its future free cash flow (a DCF),
    and compare it with today's price.

    Args:
        ticker: The stock symbol, such as TCS.NS or RELIANCE.NS.
    """
    stock = yf.Ticker(ticker)
    free_cash_flow = stock.cashflow.loc["Free Cash Flow"].iloc[0]
    if not free_cash_flow > 0:
        return {"error": "Free cash flow is missing or negative, so a DCF doesn't work here."}

    # 1. Grow the free cash flow for 5 years, converting each year to today's money
    value_today = 0
    for year in range(1, YEARS + 1):
        future_cash = free_cash_flow * (1 + GROWTH) ** year
        value_today += future_cash / (1 + DISCOUNT) ** year

    # 2. Add the value of every year after that (the "terminal value"), in today's money
    last_cash = free_cash_flow * (1 + GROWTH) ** YEARS
    terminal_value = last_cash * (1 + FOREVER_GROWTH) / (DISCOUNT - FOREVER_GROWTH)
    value_today += terminal_value / (1 + DISCOUNT) ** YEARS

    # 3. Add the cash and subtract the debt: the whole company's value
    balance = stock.balance_sheet
    cash = balance.loc["Cash And Cash Equivalents"].iloc[0]
    debt = balance.loc["Total Debt"].iloc[0] if "Total Debt" in balance.index else 0
    company_value = value_today + cash - debt

    # 4. If the statements use another currency than the price, convert at today's rate
    info = stock.info
    rates = _exchange_rates(info)
    exchange_rate = float(rates.iloc[-1]) if rates is not None else 1
    company_value = company_value * exchange_rate

    # 5. Split it across all the shares and compare with today's price
    value_per_share = company_value / info["sharesOutstanding"]
    if value_per_share <= 0:
        return {"error": "The debt is larger than the future cash flows are worth, so the "
                         "DCF value is below zero and doesn't mean anything."}
    price = info["currentPrice"]
    value_vs_price = (value_per_share / price - 1) * 100  # negative: the value is below the price

    result = {
        "currency": info.get("currency"),
        "dcf_value_per_share": format_price(value_per_share, info.get("currency")),
        "current_price": format_price(price, info.get("currency")),
        "dcf_value_vs_price": _above_or_below(value_vs_price) + " the market price",
        "signal": _signal(-value_vs_price),
        "assumptions": {"growth": GROWTH, "discount_rate": DISCOUNT,
                        "growth_after_5_years": FOREVER_GROWTH},
    }
    if rates is not None:
        result["converted"] = (f"statements in {info['financialCurrency']}, converted to "
                               f"{info['currency']} at {exchange_rate:.4g}")  # 4 significant digits: 93.92 or 0.01065
    return result


@tool
def get_historical_valuation(ticker: str) -> dict:
    """Compare today's P/E with the stock's own P/E at the end of each past year.
    A P/E well above its past average means the price has run ahead of profits.

    Args:
        ticker: The stock symbol, such as TCS.NS or RELIANCE.NS.
    """
    stock = yf.Ticker(ticker)
    info = stock.info
    eps_by_year = stock.income_stmt.loc["Diluted EPS"]
    prices = stock.history(period="5y")["Close"]
    prices.index = prices.index.tz_localize(None)  # drop the time zone so dates compare
    rates = _exchange_rates(info)  # None when EPS and price use the same currency

    past_pe = {}
    for year_end, eps in eps_by_year.items():
        if not eps > 0:
            continue  # skip missing years and loss years, where P/E means nothing
        price_then = prices[prices.index <= year_end]
        if price_then.empty:
            continue
        if rates is not None:
            rate_then = rates[rates.index <= year_end]
            if rate_then.empty:
                continue
            eps = eps * rate_then.iloc[-1]  # that year's EPS in the price's currency
        past_pe[str(year_end.year)] = round(price_then.iloc[-1] / eps, 1)

    current_pe = info.get("trailingPE")
    if not past_pe or not current_pe:
        return {"error": "No P/E history, usually because the company makes a loss."}

    average = statistics.mean(past_pe.values())
    premium = (current_pe / average - 1) * 100
    return {
        "past_pe_by_year": past_pe,
        "average_past_pe": round(average, 1),
        "current_pe": round(current_pe, 1),
        "current_vs_average": _above_or_below(premium) + " its average",
        "signal": _signal(premium),
    }


@tool
def get_peer_multiples(ticker: str, peers: list[str]) -> dict:
    """Compare the stock's P/E with its competitors. A premium means investors pay
    more for each unit of profit than they do for the peers.

    Args:
        ticker: The stock symbol, such as TCS.NS.
        peers: 3 or 4 NSE-listed competitors, such as ["INFY.NS", "WIPRO.NS", "HCLTECH.NS"].
    """
    company_pe = yf.Ticker(ticker).info.get("trailingPE")
    peer_pe = {}
    for peer in peers:
        pe = yf.Ticker(peer).info.get("trailingPE")
        if pe and pe > 0:
            peer_pe[peer] = round(pe, 1)

    if not company_pe or not peer_pe:
        return {"peer_pe": peer_pe,
                "error": "No P/E to compare, usually because the company makes a loss."}

    median = statistics.median(peer_pe.values())
    premium = (company_pe / median - 1) * 100
    return {
        "company_pe": round(company_pe, 1),
        "peer_pe": peer_pe,
        "peer_median_pe": round(median, 1),
        "vs_peers": _above_or_below(premium, "premium", "discount"),
        "signal": _signal(premium),
    }


@tool
def combine_valuation_signals(signals: list[str]) -> dict:
    """Combine the signals from the other valuation tools into one verdict.
    Each signal gets points (+2 SIGNIFICANTLY UNDERVALUED to -2 SIGNIFICANTLY
    OVERVALUED), and the average decides the verdict.

    Args:
        signals: The signal from each valuation tool that worked, such as
            ["SIGNIFICANTLY OVERVALUED", "SLIGHTLY OVERVALUED"].
    """
    points = [POINTS[s.strip().upper()] for s in signals if s.strip().upper() in POINTS]
    if not points:
        return {"verdict": "NOT AVAILABLE",
                "reason": "No valuation check worked, usually because the company makes a loss."}

    average = sum(points) / len(points)
    if average >= 1.5:
        verdict = "SIGNIFICANTLY UNDERVALUED"
    elif average >= 0.5:
        verdict = "SLIGHTLY UNDERVALUED"
    elif average > -0.5:
        verdict = "FAIRLY VALUED"
    elif average > -1.5:
        verdict = "SLIGHTLY OVERVALUED"
    else:
        verdict = "SIGNIFICANTLY OVERVALUED"

    return {"points": points, "average": round(average, 2), "verdict": verdict}
