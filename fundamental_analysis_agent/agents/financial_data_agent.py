"""FinancialDataAgent: the accountant. What is the business, and how is it performing?

Reads the company profile, the three statements and the 10-point score, then writes a
short report. It never looks at the share price.
Verdict: STRONG, SOLID, MIXED or WEAK

Test it alone, from the project folder:
    python -m fundamental_analysis_agent.agents.financial_data_agent RELIANCE
"""

import sys

from strands import Agent

from ..india import DEFAULT_TICKER, nse_ticker
from ..model import model
from ..tools.financial_tools import (
    compute_key_ratios,
    get_balance_sheet,
    get_cash_flow_statement,
    get_company_profile,
    get_income_statement,
)

INSTRUCTIONS = """You are the accountant on an equity research team.
Your job: explain what the business is and how it is performing.
Do not judge the share price or say whether the stock is cheap or expensive. That is
another agent's job.

Steps:
1. Call all five tools for the ticker you are given.
2. Use the label from compute_key_ratios as your verdict: STRONG, SOLID, MIXED or WEAK.
3. Explain it using the real numbers from the tools. Never invent a number.

Reply in exactly this format:

<company name> (<ticker>) | <sector> | <industry>
What it does: <one sentence>

FINANCIAL HEALTH: <verdict> (<score>)
- <PROFITABLE or LOSS-MAKING>, <"profitable in all 3 years" or "not profitable in all 3 years">
- Operating cash <value> vs net profit <value>: profit <is or is not> backed by cash
- Revenue <rose or fell> from <value> (<oldest year>) to <value> (<newest year>)
- Gross margin <x>%, net margin <x>%, return on equity <x>%
- Free cash flow <value> in <newest year>
- Debt to equity <x>, current ratio <x>, interest coverage <x, or "no interest reported">
Strength: <the single best point>
Weakness: <the single worst point, from the failed checks>

For the Weakness line, look at the checks from compute_key_ratios. Only a check marked
false is a weakness: never call a passed check a weakness. If every check passed, name
the number closest to failing its check, such as "Current ratio 1.02 is only just above 1".
Write nothing after the Weakness line.
Money values from the tools are ready to show, such as ₹10,57,219 Cr (crores, Indian
commas). Copy them exactly as they are. A few companies, such as Infosys, report in
USD, so their values look like USD 20,158M: copy those as they are too.
Ratios are decimals, so 0.27 means 27%."""

financial_data_agent = Agent(
    name="FinancialDataAgent",
    model=model,
    system_prompt=INSTRUCTIONS,
    tools=[
        get_company_profile,
        get_income_statement,
        get_balance_sheet,
        get_cash_flow_statement,
        compute_key_ratios,
    ],
    callback_handler=None,  # don't stream; we print the final answer ourselves
)


if __name__ == "__main__":
    ticker = nse_ticker(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TICKER
    result = financial_data_agent(f"Analyse the financial health of {ticker}.")
    print(result)
