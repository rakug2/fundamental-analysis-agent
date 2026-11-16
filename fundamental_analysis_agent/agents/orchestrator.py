"""OrchestratorAgent: the director of research. Assigns the work and returns the final
brief word for word.

Its tools are the five specialists, each wrapped with .as_tool(). It runs three phases:

1. FinancialDataAgent, NewsAndSentimentAgent and RiskAgent, all at once
2. ValuationAgent, using the financial context from phase 1
3. ReportWriterAgent, using all four reports

Phase 1 runs in parallel because the model asks for all three tools in one reply, and
Strands runs tool calls from the same reply at the same time by default.

Run it through main.py, from the project folder:
    python -m fundamental_analysis_agent.main RELIANCE
"""

from strands import Agent

from ..model import model
from .financial_data_agent import financial_data_agent
from .news_sentiment_agent import news_sentiment_agent
from .report_writer_agent import report_writer_agent
from .risk_agent import risk_agent
from .valuation_agent import valuation_agent

INSTRUCTIONS = """You are the director of research on an equity research team.
You never analyse anything yourself. You hand the work to your five specialists, in
three phases, and pass their reports along.

Phase 1, all at once: in a single reply, call financial_data_agent,
news_sentiment_agent and risk_agent together. They don't depend on each other.
Give each one the ticker.

Phase 2, after all three have answered: call valuation_agent. Give it the ticker and,
as context, the full report from financial_data_agent.

Phase 3: call report_writer_agent. Give it the ticker and all four reports, each pasted
in full under its own heading:
FINANCIAL HEALTH REPORT:
VALUATION REPORT:
NEWS SENTIMENT REPORT:
RISK REPORT:
Never shorten, summarise or change a report. report_writer_agent's brief goes back to the
user exactly as written."""

orchestrator_agent = Agent(
    name="OrchestratorAgent",
    model=model,
    system_prompt=INSTRUCTIONS,
    tools=[
        financial_data_agent.as_tool(
            name="financial_data_agent",
            description="What the business is and how it performs: profit, cash, revenue, "
                        "margins and debt. Returns STRONG, SOLID, MIXED or WEAK."),
        news_sentiment_agent.as_tool(
            name="news_sentiment_agent",
            description="The last 30 days of news and the analysts' view, scored with FinBERT. "
                        "Returns STRONGLY BULLISH to STRONGLY BEARISH, with risk flags."),
        risk_agent.as_tool(
            name="risk_agent",
            description="The risk register and a stress test. Returns LOW, MODERATE, ELEVATED or HIGH."),
        valuation_agent.as_tool(
            name="valuation_agent",
            description="Is the price fair? DCF, the stock's own past P/E and its peers. "
                        "Returns SIGNIFICANTLY UNDERVALUED to SIGNIFICANTLY OVERVALUED."),
        # delegate=True: the writer's brief is the final answer, returned word for word
        report_writer_agent.as_tool(
            name="report_writer_agent",
            description="Turns the four reports into the final brief with a rating from "
                        "STRONG BUY to STRONG SELL.",
            delegate=True),
    ],
    callback_handler=None,  # don't stream; main.py prints the final brief
)
