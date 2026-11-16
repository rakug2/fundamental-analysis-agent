"""ValuationAgent: is the share price fair?

Checks the price three ways (against future cash, against the stock's own past P/E,
and against its peers), then combines them into one verdict.
Verdict: SIGNIFICANTLY UNDERVALUED, SLIGHTLY UNDERVALUED, FAIRLY VALUED,
SLIGHTLY OVERVALUED or SIGNIFICANTLY OVERVALUED

Test it alone, from the project folder:
    python -m fundamental_analysis_agent.agents.valuation_agent RELIANCE
"""

import sys

from strands import Agent

from ..india import DEFAULT_TICKER, nse_ticker
from ..model import model
from ..tools.financial_tools import get_company_profile
from ..tools.valuation_tools import (
    combine_valuation_signals,
    get_historical_valuation,
    get_peer_multiples,
    run_dcf_model,
)

INSTRUCTIONS = """You are the valuation analyst on an equity research team.
Your job: decide whether the share price is fair. Don't judge whether the business is
good. That is another agent's job.

Steps:
1. Call get_company_profile to learn the company's industry.
2. Call run_dcf_model and get_historical_valuation.
3. Choose 3 or 4 well-known direct competitors listed on India's National Stock
   Exchange that sell similar products, as NSE tickers ending in .NS, such as
   ["INFY.NS", "WIPRO.NS", "HCLTECH.NS"] for TCS.NS. Call get_peer_multiples with them.
4. Call combine_valuation_signals with the signal from each check that worked.
   Its verdict is your verdict. Don't change it.

Never invent a number. Copy the comparison text from the tools, such as
"60.7% below the market price", and the prices exactly as written, such as ₹1,324.40.
Reply in exactly this format:

VALUATION: <verdict>
- DCF: <dcf_value_per_share> per share vs price <current_price>, <dcf_value_vs_price>: <signal>
- Own history: P/E <current> today vs <average> average (<first year>-<last year>), <current_vs_average>: <signal>
- Peers (<peer tickers used>): P/E <company> vs peer median <median>, a <vs_peers>: <signal>
Points: <every number in points, such as -2, -1, -2> (average <average>)
Main reason: <one sentence>

If a check returned an error, write "not available" and the reason on its line.
Write nothing after the Main reason line."""

valuation_agent = Agent(
    name="ValuationAgent",
    model=model,
    system_prompt=INSTRUCTIONS,
    tools=[
        get_company_profile,
        run_dcf_model,
        get_historical_valuation,
        get_peer_multiples,
        combine_valuation_signals,
    ],
    callback_handler=None,  # don't stream; we print the final answer ourselves
)


if __name__ == "__main__":
    ticker = nse_ticker(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TICKER
    result = valuation_agent(f"Value the stock {ticker}.")
    print(result)
