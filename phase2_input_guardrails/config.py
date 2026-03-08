"""Phase 2 configuration — canned messages and fund URLs for redirects."""

# Canned responses per architecture.md
CANNED_PII = (
    "I cannot process personal information. Please do not share sensitive details "
    "like PAN, Aadhaar, or bank information."
)

CANNED_ADVICE_REDIRECT = (
    "I'm unable to provide investment advice or compare fund performance. "
    "You can review the fund details here: {url}"
)

CANNED_OFF_TOPIC = (
    "I can only answer factual questions about the listed Quant Mutual Funds."
)

CANNED_GREETING = (
    "Hello! I can answer factual questions about the 10 Quant Mutual Fund schemes "
    "on Groww. Ask about a specific fund's details, NAV, holdings, or other facts. "
    "I don't provide investment advice or comparisons."
)

# Default fund page URL when no specific fund is mentioned in advice/comparison block
DEFAULT_FUND_PAGE_URL = "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth"

# Allowed fund URLs for citation (from architecture)
FUND_URLS = [
    "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/quant-infrastructure-fund-direct-growth",
    "https://groww.in/mutual-funds/quant-flexi-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/quant-elss-tax-saver-fund-direct-growth",
    "https://groww.in/mutual-funds/quant-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/quant-esg-integration-strategy-fund-direct-growth",
    "https://groww.in/mutual-funds/quant-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/quant-multi-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/quant-aggressive-hybrid-fund-direct-growth",
    "https://groww.in/mutual-funds/quant-focused-fund-direct-growth",
]
