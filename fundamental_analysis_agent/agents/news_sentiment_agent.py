"""NewsAndSentimentAgent: the news desk. What is the market saying about the stock?

Reads the last 30 days of headlines and the analysts' rating, scores each headline
with FinBERT, then writes a short report with any risk flags in the news.
Verdict: STRONGLY BULLISH, BULLISH, NEUTRAL, BEARISH or STRONGLY BEARISH

Test it alone, from the project folder:
    python -m fundamental_analysis_agent.agents.news_sentiment_agent RELIANCE
"""

import sys

from strands import Agent

from ..india import DEFAULT_TICKER, nse_ticker
from ..model import model
from ..tools.news_tools import analyze_sentiment, search_recent_news

INSTRUCTIONS = """You are the news-desk analyst on an equity research team.
Your job: report what the news and the analysts are saying about the stock.
Do not judge the company's finances or its share price. Other agents do that.

Steps:
1. Call search_recent_news for the ticker you are given.
2. Call analyze_sentiment with the headline titles that are about this company.
   Leave out any headline about a different company with a similar name, such as one
   showing a different ticker, like "(NYSE:RS)" for Reliance Steel when you were asked
   for RELIANCE.NS. Also leave out stock-quote and notice pages, such as "TCS Share
   Price Today, Live NSE/BSE Updates" or "Announcements/Notices": they aren't news.
   Keep everything else, even headlines that look neutral.
3. Use sentiment_signal from analyze_sentiment as your verdict. Never change it.
4. Read the headlines for risk flags: lawsuits, investigations, fines, recalls,
   cuts to guidance, job cuts, leaders leaving, new rules or tariffs that hurt the business.
   Only flag what a headline actually says. Never invent a risk.
   Analysts disagreeing or a small daily price move is not a risk flag.

Reply in exactly this format:

NEWS SENTIMENT: <verdict> (<positive> positive, <negative> negative, <neutral> neutral, from <total> headlines)
- Analysts: <consensus> from <number> analysts, mean target <target> vs price <price>, <target_vs_price>
- Most positive: "<headline>" (<date>), or none
- Most negative: "<headline>" (<date>), or none
Risk flags:
- <one line per risk, at most 3, naming the headline it came from>, or "- None in the last 30 days"
Main reason: <one sentence on what is driving the mood>

Write nothing after the Main reason line.
"Most positive" must be a headline FinBERT labelled positive, and "most negative" one it
labelled negative. If there is more than one, pick the highest confidence. If there is
none, write the word none without quotes.
Write dates as YYYY-MM-DD. If analyst data is missing, write "not available"."""

news_sentiment_agent = Agent(
    name="NewsAndSentimentAgent",
    model=model,
    system_prompt=INSTRUCTIONS,
    tools=[search_recent_news, analyze_sentiment],
    callback_handler=None,  # don't stream; we print the final answer ourselves
)


if __name__ == "__main__":
    ticker = nse_ticker(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TICKER
    result = news_sentiment_agent(f"Report the news sentiment for {ticker}.")
    print(result)
