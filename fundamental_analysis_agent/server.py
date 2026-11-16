"""A local web server for the team, so you can test it with curl.

Same pattern as the course's Section 6 lab (agentcore-runtime/agent.py):
  1. import BedrockAgentCoreApp
  2. app = BedrockAgentCoreApp()
  3. @app.entrypoint on the handler
  4. app.run() in __main__

Start it from the project folder (it keeps running until you press Ctrl+C):
    python -m fundamental_analysis_agent.server

Then, in another terminal:
    curl -X POST http://localhost:8080/invocations \
         -H "Content-Type: application/json" -d '{"ticker": "TCS"}'

It runs on your laptop only and needs no AWS account. The same file is what AgentCore
Runtime would run if the agent were deployed.
"""

from bedrock_agentcore import BedrockAgentCoreApp

from .agents.orchestrator import orchestrator_agent
from .india import nse_ticker

app = BedrockAgentCoreApp()


@app.entrypoint
def handle(payload):
    """Called for every POST to /invocations. payload is the JSON body as a dict."""
    ticker = payload.get("ticker", "").strip()
    if not ticker:
        return {"error": 'Send an NSE symbol, such as {"ticker": "TCS"}.'}
    ticker = nse_ticker(ticker)  # TCS becomes TCS.NS

    # Start each request with an empty conversation, so one stock's reports
    # don't leak into the next one's brief.
    orchestrator_agent.messages.clear()
    brief = orchestrator_agent(f"Produce the fundamental analysis brief for {ticker}.")
    return {"ticker": ticker, "brief": str(brief)}


if __name__ == "__main__":
    app.run()  # listens on http://localhost:8080
