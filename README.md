# Fundamental Analysis Agent

A team of AI agents that works like an equity research team, set up for Indian stocks on the NSE. Give it an NSE symbol such as TCS, and it returns a one-page brief with a rating from STRONG BUY to STRONG SELL, the stock's estimated value, its risk level and the news sentiment.

Plain Python fetches the data and does the calculations. The agents read the results, decide and explain. It's for learning only and isn't financial advice.

Based on Section 4 of the AI Agents in Finance course. The agents use Strands with OpenAI's gpt-4o-mini (set in `model.py`), the data comes from yfinance, the news from Tavily (Indian business sites only), and headline sentiment from FinBERT. Money is shown in rupees and crores, such as ₹10,57,219 Cr.

Run the whole team (see Setup first):

```bash
.venv/bin/python -m fundamental_analysis_agent.main TCS
```

## Setup

Run these from this folder. The project needs Python 3.11 to 3.13.

```bash
uv venv --python 3.11
uv pip install -r fundamental_analysis_agent/requirements.txt
cp fundamental_analysis_agent/.env.example fundamental_analysis_agent/.env
```

Then paste your OpenAI and Tavily keys into `fundamental_analysis_agent/.env`, which git ignores. The news tool needs the Tavily key.

## Run

Run this from this folder, using `-m` as shown:

```bash
.venv/bin/python -m fundamental_analysis_agent.main TCS
```

It takes about a minute and prints the brief. Type the NSE symbol (`TCS`, `INFY`, `HDFCBANK`); `.NS` is added for you. With no symbol it uses Reliance. For the Bombay Stock Exchange, type the full ticker, such as `RELIANCE.BO`.

### Test with curl

Start the local server (the same pattern as the course's Section 6 AgentCore lab). It needs no AWS account and keeps running until you press Ctrl+C:

```bash
.venv/bin/python -m fundamental_analysis_agent.server
```

Then, in a second terminal, send a ticker. Each request takes about a minute, and `jq -r '.brief'` prints the brief as plain text:

```bash
curl -s -X POST http://localhost:8080/invocations -H "Content-Type: application/json" -d '{"ticker": "TCS"}' | jq -r '.brief'
```

`curl http://localhost:8080/ping` checks that the server is up. Send one request at a time: the server has a single orchestrator, so two at once would mix their conversations.

To test one agent on its own, run its file the same way. Each one prints its own report, and `report_writer_agent` runs the other four first, one after another:

```bash
.venv/bin/python -m fundamental_analysis_agent.agents.financial_data_agent TCS
.venv/bin/python -m fundamental_analysis_agent.agents.valuation_agent TCS
.venv/bin/python -m fundamental_analysis_agent.agents.news_sentiment_agent TCS
.venv/bin/python -m fundamental_analysis_agent.agents.risk_agent TCS
.venv/bin/python -m fundamental_analysis_agent.agents.report_writer_agent TCS
```

Running a file directly breaks its imports, because the files import each other as parts of the `fundamental_analysis_agent` package. `-m` runs them as part of the package.

## The team

| Agent | Job | Tools | Verdict |
|---|---|---|---|
| `FinancialDataAgent` | What the business is and how it performs, with no share price | `get_company_profile`, `get_income_statement`, `get_balance_sheet`, `get_cash_flow_statement`, `compute_key_ratios` | STRONG to WEAK |
| `NewsAndSentimentAgent` | News mood and risk flags | `search_recent_news`, `analyze_sentiment` | STRONGLY BULLISH to STRONGLY BEARISH |
| `RiskAgent` | Risk register and stress test | `search_recent_news`, `assess_risk`, `get_balance_sheet`, `compute_key_ratios` | LOW to HIGH |
| `ValuationAgent` | Is the price fair: against its cash, its own past and its peers | `get_company_profile`, `run_dcf_model`, `get_historical_valuation`, `get_peer_multiples`, `combine_valuation_signals` | SIGNIFICANTLY UNDERVALUED to SIGNIFICANTLY OVERVALUED |
| `ReportWriterAgent` | Writes the final brief | `apply_rating_table` (the course uses none) | STRONG BUY to STRONG SELL |
| `OrchestratorAgent` | Assigns the work | The five agents above, using `.as_tool()` | Returns the brief word for word |

It runs in three phases:

1. **All at once:** `FinancialDataAgent`, `NewsAndSentimentAgent` and `RiskAgent`, because none depends on another.
2. **Then:** `ValuationAgent`, which needs the financial numbers.
3. **Finally:** `ReportWriterAgent`, which needs all four reports.

The order comes from the orchestrator's instructions, as in the course. Phase 1 really runs in parallel: the model asks for all three agents in one reply, and Strands runs tool calls from the same reply at the same time. In a test on Apple (before the switch to India), all three started together and phase 1 took 10 seconds; the whole run took 48. The writer is wrapped with `as_tool(delegate=True)`, so its brief comes back word for word instead of being retold by the orchestrator.

## Layout

```
fundamental_analysis_agent/
├── agents/
│   ├── financial_data_agent.py
│   ├── news_sentiment_agent.py
│   ├── risk_agent.py
│   ├── valuation_agent.py
│   ├── report_writer_agent.py
│   └── orchestrator.py
├── tools/
│   ├── financial_tools.py
│   ├── valuation_tools.py
│   ├── news_tools.py
│   ├── risk_tools.py
│   └── report_tools.py
├── india.py               NSE tickers, rupees and crores
├── main.py
├── server.py              local web server for curl (POST /invocations)
├── requirements.txt
└── .env
```

## Status

The tools, `FinancialDataAgent`, `ValuationAgent`, `NewsAndSentimentAgent`, `RiskAgent`, `ReportWriterAgent` and `OrchestratorAgent` are built. The whole team is tested on Reliance, TCS, Infosys and Vodafone Idea (a loss-maker with negative equity), and the news on HDFC Bank too. Before the switch to India it was also tested on Apple, Microsoft and Tesla. Every tool uses Strands' `@tool` decorator, so it can be called directly in a test or given to an agent. Progress is tracked in [CHECKLIST.md](CHECKLIST.md).

## How the tools decide

These are our own simple choices, because the course's versions weren't in the notes:

- **Profitable or loss-making:** from the newest net profit. The profit counts as backed by cash when operating cash flow is at least 90% of it.
- **Health score:** 10 checks, 1 point each: revenue, profit and EPS grew over 3 years (profit and EPS also need a real profit, so a smaller loss doesn't count); profit is backed by cash; free cash flow is positive; net margin above 10%; return on equity above 15%; debt to equity below 1; current ratio above 1; interest covered 3 times or no interest. 8-10 is STRONG, 6-7 SOLID, 4-5 MIXED and 0-3 WEAK.
- **Past P/E:** the year-end share price divided by that year's EPS, for each of the last 3-4 years, compared with today's P/E.
- **Valuation verdict:** the DCF, past P/E and peer checks each give a signal worth +2 (SIGNIFICANTLY UNDERVALUED) to -2 (SIGNIFICANTLY OVERVALUED). `combine_valuation_signals` averages them in code, so the agent can't get the sums wrong.
- **DCF:** set for Indian companies: 10% growth for 5 years, a 12% discount rate (what Indian investors typically expect from shares) and 5% growth after that, set at the top of `valuation_tools.py`. If the debt is bigger than the cash flows are worth, the DCF says "not available" rather than showing a negative value.
- **Rupees and crores:** `india.py` formats money in code, because LLMs often get Indian commas wrong. Company amounts are crores (₹10,57,219 Cr) and per-share amounts keep paise (₹1,324.40). Typing `TCS` becomes `TCS.NS`.
- **News:** Tavily searches `<company> stock analysts results` on Economic Times, Moneycontrol, Mint, Business Standard, BusinessLine and Financial Express only. That wording kept 7-8 of 8 headlines on topic in tests. The news agent also drops stock-quote pages.
- **Currencies:** some companies report their statements in one currency and trade in another (Infosys reports in USD and trades in INR, so its statements show as USD 20,158M while its price is in ₹). The DCF converts the statement numbers at today's exchange rate, and the past P/E converts each year's EPS at that year-end's rate, using Yahoo's rates such as `USDINR=X`. The financial report writes the reporting currency before every amount.
- **Sentiment:** FinBERT (`ProsusAI/finbert`, the classifier from Section 1.3 of the course) labels each headline positive, negative or neutral, with a confidence. Positive minus negative headlines, divided by the total, sets the label: 0.5 or more is STRONGLY BULLISH, 0.15 or more BULLISH, above -0.15 NEUTRAL, above -0.5 BEARISH, and anything lower STRONGLY BEARISH. FinBERT runs on the laptop CPU, and the first run downloads it (about 440MB).
- **Risk:** `assess_risk` builds a risk register in code. One point each for: high debt, current ratio below 1, interest covered less than 3 times, negative free cash flow, profit not backed by cash, revenue lower than 3 years ago, beta above 1.5 (the share price swings much more than the market), failing the stress test, and less than 2 years of cash left. Being loss-making counts 2 points. Risks the agent reads in the news add 1 point each, at most 2. 0-1 is LOW, 2-3 MODERATE, 4-5 ELEVATED and 6 or more HIGH.
- **Stress test:** revenue falls 20% while the gross margin and running costs stay the same, so operating profit loses 20% of the gross profit. The company fails if operating profit turns negative.

### Why FinBERT and not FinGPT

The course names both. FinGPT's models are add-ons (LoRA adapters) for 6-8 billion parameter base models, with no hosted API, so they need a large download and a GPU to run well. FinBERT is small, runs on a CPU, and is the one the course gives runnable code for. Labelling short headlines is one narrow job, which is where the course says a small specialised model beats a large chat model.

### The rating table

The course gives `ReportWriterAgent` no tools, but we look the rating up in code with `apply_rating_table`, so it can't be misread. The course's full table isn't available; its sample run shows only one row (SIGNIFICANTLY OVERVALUED with ELEVATED risk is a STRONG SELL). The rest is ours: a cheaper stock earns a better rating, and more risk pulls it down. Sentiment is shown in the brief but doesn't change the rating, as in the course.

| Valuation \ Risk | LOW | MODERATE | ELEVATED | HIGH |
|---|---|---|---|---|
| SIGNIFICANTLY UNDERVALUED | STRONG BUY | STRONG BUY | BUY | HOLD |
| SLIGHTLY UNDERVALUED | BUY | BUY | HOLD | SELL |
| FAIRLY VALUED | HOLD | HOLD | HOLD | SELL |
| SLIGHTLY OVERVALUED | HOLD | SELL | SELL | STRONG SELL |
| SIGNIFICANTLY OVERVALUED | SELL | SELL | STRONG SELL | STRONG SELL |
| NOT AVAILABLE | HOLD | HOLD | SELL | SELL |
