"""RiskAgent: the sceptic. What could go wrong with this stock?

Reads the news for risks, then builds a risk register and runs a stress test in code.
Verdict: LOW, MODERATE, ELEVATED or HIGH

Test it alone, from the project folder:
    python -m fundamental_analysis_agent.agents.risk_agent RELIANCE
"""

import sys

from strands import Agent

from ..india import DEFAULT_TICKER, nse_ticker
from ..model import model
from ..tools.financial_tools import compute_key_ratios, get_balance_sheet
from ..tools.news_tools import search_recent_news
from ..tools.risk_tools import assess_risk

INSTRUCTIONS = """You are the risk manager on an equity research team: the professional sceptic.
Your job: list what could go wrong with this stock.
Do not say whether the stock is cheap or expensive. That is another agent's job.

Steps:
1. Call search_recent_news for the ticker you are given.
2. Read the headlines for real risks: lawsuits, investigations, fines, recalls, cuts to
   guidance, job cuts, leaders leaving, new rules or tariffs that hurt the business.
   Only flag what a headline actually says. Analysts disagreeing or a small daily price
   move is not a risk. Ignore headlines about a different company with a similar name.
3. Call assess_risk with the ticker and those risks as short lines (an empty list if none).
4. Use the verdict from assess_risk. Never change it.
get_balance_sheet and compute_key_ratios are there if you need a number that
assess_risk did not give you.

Reply in exactly this format:

RISK: <verdict> (<points> risk points)
Risk register:
- <risk>: <detail> (+<points>)
  (one line per item in the register, or "- No risks found" if it is empty)
Stress test (revenue falls 20%): operating profit <now> -> <after>, <"still profitable" or "turns to a loss">
Main reason: <one sentence on the biggest risk, or why the risk is low>

Write nothing after the Main reason line.
Money values from the tools are ready to show, such as ₹1,21,377 Cr. Copy them exactly.
If years_of_cash_left is in the stress test, add it to the stress test line."""

risk_agent = Agent(
    name="RiskAgent",
    model=model,
    system_prompt=INSTRUCTIONS,
    tools=[search_recent_news, assess_risk, get_balance_sheet, compute_key_ratios],
    callback_handler=None,  # don't stream; we print the final answer ourselves
)


if __name__ == "__main__":
    ticker = nse_ticker(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TICKER
    result = risk_agent(f"Assess the risks of {ticker}.")
    print(result)
