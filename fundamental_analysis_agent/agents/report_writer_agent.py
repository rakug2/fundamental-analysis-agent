"""ReportWriterAgent: the managing director. Turns the four reports into one brief.

It fetches no data. Its only tool is the rating table, so the final rating is an
exact lookup rather than the model's guess.
Rating: STRONG BUY, BUY, HOLD, SELL or STRONG SELL

Test it alone, from the project folder (runs the other four agents first, one after
another, then writes the brief):
    python -m fundamental_analysis_agent.agents.report_writer_agent RELIANCE
"""

import sys

from strands import Agent

from ..india import DEFAULT_TICKER, nse_ticker
from ..model import model
from ..tools.report_tools import apply_rating_table

INSTRUCTIONS = """You are the managing director of an equity research team.
You receive four reports about one stock: financial health, valuation, news sentiment
and risk. Turn them into one brief.

Where each verdict is: the first line of each report.
- Valuation verdict: the words after "VALUATION:". Not the labels at the end of the DCF,
  Own history or Peers lines; those are single checks, not the verdict.
- Risk verdict: the word after "RISK:".
- Sentiment verdict: the words after "NEWS SENTIMENT:".
- Health verdict: the words after "FINANCIAL HEALTH:".

Steps:
1. Call apply_rating_table with the valuation verdict and the risk verdict.
2. Use its rating as the final rating. Never change it.
3. Write the brief using only facts and numbers from the four reports. Never invent a
   number. Sentiment is reported but does not change the rating.

Reply in exactly this format, keeping the lines of = signs:

==================================================
FUNDAMENTAL ANALYSIS BRIEF
<company name> (<ticker>) | <sector>
==================================================
INVESTMENT VERDICT
  Valuation verdict (from ValuationAgent): <valuation verdict>
  Risk verdict (from RiskAgent):           <risk verdict> RISK
  Applying rating table =>                 <rating>

  Sentiment:        <sentiment verdict>
  Intrinsic Value:  <DCF value> per share (DCF)
  Current Price:    <price>
  Upside/Downside:  <+ or -><x>%
FINANCIAL HEALTH: <health verdict> (<score>)
  - <3 or 4 bullets from the financial report: profit and cash, revenue, margins, debt>
VALUATION ANALYSIS
  - DCF: <value> per share, <x>% <above or below> the market price
  - Own history: <one line>
  - Peers: <one line>
MARKET SENTIMENT
  - <2 or 3 bullets: headline counts, analysts' view, the key headline>
RISK FACTORS
  - <one bullet per item in the risk register, or "No major risks found">
  - Stress test: <one line>
BULL / BASE / BEAR CASE
  Bull: <one sentence: what has to go right>
  Base: <one sentence: the most likely path>
  Bear: <one sentence: what could go wrong>
CONCLUSION
  <two or three sentences explaining the rating; say plainly if sentiment points the other way>

This report is for educational purposes only. Not financial advice.

Upside/Downside is the DCF value compared with the price: "60.7% below the market price"
becomes -60.7%, and "12.0% above the market price" becomes +12.0%.
If the DCF is not available, write "not available" for Intrinsic Value and Upside/Downside.
If any valuation check is not available, write "not available" on its line. Never fill
the gap with your own opinion.
Copy money exactly as the reports write it, such as ₹1,324.40 per share or
₹10,57,219 Cr. Never convert it or change its units. Write percentages with 1 decimal.
Write nothing after the disclaimer line."""

report_writer_agent = Agent(
    name="ReportWriterAgent",
    model=model,
    system_prompt=INSTRUCTIONS,
    tools=[apply_rating_table],
    callback_handler=None,  # don't stream; we print the final answer ourselves
)


if __name__ == "__main__":
    # Imported here so the test below can run the other agents; the orchestrator
    # will do this job for real.
    from .financial_data_agent import financial_data_agent
    from .news_sentiment_agent import news_sentiment_agent
    from .risk_agent import risk_agent
    from .valuation_agent import valuation_agent

    ticker = nse_ticker(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TICKER
    financial = financial_data_agent(f"Analyse the financial health of {ticker}.")
    valuation = valuation_agent(f"Value the stock {ticker}.")
    news = news_sentiment_agent(f"Report the news sentiment for {ticker}.")
    risk = risk_agent(f"Assess the risks of {ticker}.")

    reports = (f"FINANCIAL HEALTH REPORT:\n{financial}\n\n"
               f"VALUATION REPORT:\n{valuation}\n\n"
               f"NEWS SENTIMENT REPORT:\n{news}\n\n"
               f"RISK REPORT:\n{risk}")
    print(report_writer_agent(f"Write the brief for {ticker} from these reports.\n\n{reports}"))
