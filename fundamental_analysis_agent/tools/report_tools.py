"""The rating table: valuation verdict + risk verdict -> final rating.

Tool: apply_rating_table

The course's full table isn't available to us. Its sample run gives one row:
SIGNIFICANTLY OVERVALUED with ELEVATED risk is a STRONG SELL. The rest is our own,
built on two ideas: a cheaper stock earns a better rating, and more risk pulls the
rating down. Sentiment is shown in the brief but doesn't change the rating, as in the
course.
"""

from strands import tool

# One row per valuation verdict, one column per risk verdict
RATING_TABLE = {
    "SIGNIFICANTLY UNDERVALUED": {"LOW": "STRONG BUY", "MODERATE": "STRONG BUY", "ELEVATED": "BUY", "HIGH": "HOLD"},
    "SLIGHTLY UNDERVALUED": {"LOW": "BUY", "MODERATE": "BUY", "ELEVATED": "HOLD", "HIGH": "SELL"},
    "FAIRLY VALUED": {"LOW": "HOLD", "MODERATE": "HOLD", "ELEVATED": "HOLD", "HIGH": "SELL"},
    "SLIGHTLY OVERVALUED": {"LOW": "HOLD", "MODERATE": "SELL", "ELEVATED": "SELL", "HIGH": "STRONG SELL"},
    "SIGNIFICANTLY OVERVALUED": {"LOW": "SELL", "MODERATE": "SELL", "ELEVATED": "STRONG SELL", "HIGH": "STRONG SELL"},
    # no valuation check worked, so the risk alone decides
    "NOT AVAILABLE": {"LOW": "HOLD", "MODERATE": "HOLD", "ELEVATED": "SELL", "HIGH": "SELL"},
}


@tool
def apply_rating_table(valuation_verdict: str, risk_verdict: str) -> dict:
    """Look up the final rating, STRONG BUY to STRONG SELL, from the valuation and
    risk verdicts.

    Args:
        valuation_verdict: From ValuationAgent, such as SIGNIFICANTLY OVERVALUED.
        risk_verdict: From RiskAgent: LOW, MODERATE, ELEVATED or HIGH.
    """
    valuation = valuation_verdict.strip().upper()
    risk = risk_verdict.strip().upper().replace(" RISK", "")  # "ELEVATED RISK" -> "ELEVATED"

    if valuation not in RATING_TABLE:
        return {"error": f"Unknown valuation verdict: {valuation_verdict}",
                "allowed": list(RATING_TABLE)}
    if risk not in RATING_TABLE[valuation]:
        return {"error": f"Unknown risk verdict: {risk_verdict}",
                "allowed": ["LOW", "MODERATE", "ELEVATED", "HIGH"]}

    return {"valuation": valuation, "risk": risk, "rating": RATING_TABLE[valuation][risk]}
