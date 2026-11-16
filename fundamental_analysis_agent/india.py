"""Everything that makes the team Indian: NSE tickers, rupees and crores.

    nse_ticker("tcs")                        -> "TCS.NS"
    format_money(10_572_190_000_000, "INR")  -> "₹10,57,219 Cr"
    format_price(1324.4, "INR")              -> "₹1,324.40"

The formatting is done here in code, because LLMs often get Indian commas
(12,34,567) and crores wrong.
"""

DEFAULT_TICKER = "RELIANCE.NS"
CRORE = 10_000_000  # 1 crore = 100 lakh = 10 million


def nse_ticker(ticker):
    """Add .NS (the National Stock Exchange) when no exchange is given.
    TCS becomes TCS.NS; RELIANCE.BO (the Bombay Stock Exchange) stays as it is."""
    ticker = ticker.strip().upper()
    if "." not in ticker:
        ticker = ticker + ".NS"
    return ticker


def indian_commas(number):
    """Group the digits the Indian way: 1234567 becomes 12,34,567.
    The last three digits form one group, then every two digits before them."""
    sign = "-" if number < 0 else ""
    digits = str(round(abs(number)))
    if len(digits) <= 3:
        return sign + digits

    last_three = digits[-3:]
    rest = digits[:-3]
    groups = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])  # take two digits from the right
        rest = rest[:-2]
    groups.insert(0, rest)
    return sign + ",".join(groups) + "," + last_three


def format_money(amount, currency):
    """A company-sized amount, ready to show: rupees in crores, other currencies in
    millions. 10572190000000 INR gives "₹10,57,219 Cr"; 4039000000 USD gives "USD 4,039M".
    A few Indian companies, such as Infosys, report in USD, so the currency is kept."""
    sign = "-" if amount < 0 else ""  # a loss reads -₹3,646 Cr
    if currency == "INR":
        return f"{sign}₹{indian_commas(abs(amount) / CRORE)} Cr"
    return f"{sign}{currency} {abs(amount) / 1_000_000:,.0f}M"


def format_price(amount, currency):
    """A per-share amount with 2 decimals: 1324.4 INR gives "₹1,324.40"."""
    sign = "-" if amount < 0 else ""
    if currency != "INR":
        return f"{sign}{currency} {abs(amount):,.2f}"
    rupees, paise = f"{abs(amount):.2f}".split(".")
    return f"{sign}₹{indian_commas(int(rupees))}.{paise}"
