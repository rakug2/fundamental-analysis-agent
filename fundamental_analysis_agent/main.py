"""Entry point. Run from the folder above this one:

    python -m fundamental_analysis_agent.main RELIANCE

Type the NSE symbol (TCS, INFY, HDFCBANK); .NS is added for you.

Hands the ticker to the OrchestratorAgent and prints the final brief.
"""

import sys

from .agents.orchestrator import orchestrator_agent
from .india import DEFAULT_TICKER, nse_ticker


def main():
    ticker = nse_ticker(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TICKER
    print(f"Analysing {ticker}. This takes about a minute...\n")
    brief = orchestrator_agent(f"Produce the fundamental analysis brief for {ticker}.")
    print(brief)


if __name__ == "__main__":
    main()
