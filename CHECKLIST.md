# Checklist

Build from the bottom up: tools, then agents, then running it. Done items are struck off.

## 1. Setup

- [x] ~~Project folder and layout, as in the course~~
- [x] ~~Python 3.11 environment with the course's packages~~
- [x] ~~OpenAI and Tavily keys in `.env`~~

## 2. Tools (plain Python, no AI)

- [x] ~~`financial_tools.py`: income statement, balance sheet, cash flow, and the 10-point health score~~
- [x] ~~`valuation_tools.py`: DCF value per share and peer P/E comparison~~
- [x] ~~`news_tools.py`: Tavily news and analyst ratings~~
- [x] ~~Add gross margin~~
- [x] ~~Add company name and sector: `get_company_profile`~~
- [x] ~~Profitable or loss-making, and is the profit backed by cash~~
- [x] ~~Past P/E vs today's: `get_historical_valuation`~~
- [x] ~~Sentiment: `analyze_sentiment` uses FinBERT, as in the course~~

## 3. Agents (the LLM plus instructions plus tools)

- [x] ~~All tools use Strands' `@tool` decorator, as in the course~~

- [x] ~~`FinancialDataAgent` (Strands): what the business is and how it performs, no share price; STRONG, SOLID, MIXED or WEAK~~
- [x] ~~`NewsAndSentimentAgent` (Strands): FinBERT on Tavily headlines, plus risk flags; STRONGLY BULLISH to STRONGLY BEARISH~~
- [x] ~~`RiskAgent` (Strands): risk register and stress test in code (`assess_risk`), plus risks from the news; LOW, MODERATE, ELEVATED or HIGH~~
- [x] ~~`ValuationAgent` (Strands): DCF, own past P/E and peers, combined in code into SIGNIFICANTLY UNDERVALUED to SIGNIFICANTLY OVERVALUED~~
- [x] ~~`ReportWriterAgent` (Strands): the brief in the course's format, with the rating table looked up in code (`apply_rating_table`)~~
- [x] ~~`OrchestratorAgent` (Strands): the five agents with `.as_tool()`, three phases, phase 1 in parallel~~

## 4. Running it

- [x] ~~`main.py`: `python -m fundamental_analysis_agent.main TCS`~~
- [x] ~~Apple's brief matches the course's sample format~~
- [x] ~~Test Microsoft, Tesla and Reliance~~
- [x] ~~`server.py`: test with curl, using the course's `BedrockAgentCoreApp` pattern~~
- [x] ~~Stocks whose statements and price use different currencies (Infosys, Wipro, HDFC Bank ADR): converted with Yahoo's exchange rates~~

## 5. India

- [x] ~~NSE by default: `TCS` becomes `TCS.NS`, peers from NSE, Reliance as the default~~
- [x] ~~Indian DCF settings: 10% growth, 12% discount, 5% after~~
- [x] ~~Rupees and crores, formatted in code (`india.py`)~~
- [x] ~~News from Indian business sites only~~
- [x] ~~Test Reliance, TCS, Infosys and Vodafone Idea~~

## 6. Finish

- [x] ~~README: why FinBERT and not the FinGPT model~~
- [x] ~~README: how to run the whole team~~
- [x] ~~Commit on its own branch and push~~
