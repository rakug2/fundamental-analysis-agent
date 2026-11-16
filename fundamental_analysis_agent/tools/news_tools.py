"""Recent news, analyst ratings and headline sentiment.

Tools: search_recent_news, analyze_sentiment

News comes from Tavily (needs TAVILY_API_KEY in .env), from Indian business sites only.
Analyst ratings come from Yahoo Finance. Sentiment comes from FinBERT, the course's finance classifier
(Section 1.3): headline in, label and confidence out. It runs on the laptop CPU,
and the first run downloads the model (about 440MB).
"""

import os

import yfinance as yf
from strands import tool
from tavily import TavilyClient
from transformers import pipeline

from ..india import format_price

# Load FinBERT once, when this file is imported, so every call reuses it.
finbert = pipeline("text-classification", model="ProsusAI/finbert")

# Indian business news sites the search is limited to
INDIAN_NEWS_SITES = ["economictimes.indiatimes.com", "moneycontrol.com", "livemint.com",
                     "business-standard.com", "thehindubusinessline.com", "financialexpress.com"]


@tool
def search_recent_news(ticker: str) -> dict:
    """News headlines from the last 30 days and the analysts' consensus rating.

    Args:
        ticker: The stock symbol, such as TCS.NS or RELIANCE.NS.
    """
    info = yf.Ticker(ticker).info
    company = info.get("longName", ticker)

    tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    # "<name> stock analysts results", without "Limited", kept headlines on topic best in
    # tests: 8 of 8 for Reliance and Infosys, 7 of 7 for TCS and HDFC Bank
    name = company.replace(" Limited", "").replace(" Ltd.", "").replace(" Ltd", "")
    response = tavily.search(query=f"{name} stock analysts results",
                             topic="news", days=30, max_results=8,
                             include_domains=INDIAN_NEWS_SITES)
    headlines = [{"title": r["title"], "date": r.get("published_date"), "url": r["url"]}
                 for r in response["results"]]

    price = info.get("currentPrice")
    target = info.get("targetMeanPrice")
    analysts = {
        "consensus": info.get("recommendationKey"),
        "number_of_analysts": info.get("numberOfAnalystOpinions"),
        "mean_price_target": format_price(target, info.get("currency")) if target else None,
        "current_price": format_price(price, info.get("currency")) if price else None,
    }
    if price and target:
        gap = round((target - price) / price * 100, 1)
        if gap >= 0:
            analysts["target_vs_price"] = f"{gap}% above the current price"
        else:
            analysts["target_vs_price"] = f"{-gap}% below the current price"

    return {"company": company, "headlines": headlines, "analysts": analysts}


@tool
def analyze_sentiment(headlines: list[str]) -> dict:
    """Label each headline positive, negative or neutral with FinBERT, then give an
    overall label from STRONGLY BULLISH to STRONGLY BEARISH.

    Args:
        headlines: The news headlines to score.
    """
    if not headlines:
        return {"error": "No headlines to score."}

    results = finbert(headlines)  # one {"label": ..., "score": ...} per headline

    counts = {"positive": 0, "negative": 0, "neutral": 0}
    scored = []
    for headline, result in zip(headlines, results):
        counts[result["label"]] += 1
        scored.append({"headline": headline, "sentiment": result["label"],
                       "confidence": round(result["score"], 2)})

    # +1 if every headline is positive, -1 if every headline is negative
    net = (counts["positive"] - counts["negative"]) / len(headlines)
    if net >= 0.5:
        signal = "STRONGLY BULLISH"
    elif net >= 0.15:
        signal = "BULLISH"
    elif net > -0.15:
        signal = "NEUTRAL"
    elif net > -0.5:
        signal = "BEARISH"
    else:
        signal = "STRONGLY BEARISH"

    return {"counts": counts, "net_score": round(net, 2), "sentiment_signal": signal,
            "headlines": scored}
