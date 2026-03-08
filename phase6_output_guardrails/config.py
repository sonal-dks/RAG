"""
Phase 6 configuration — allowed URLs, canned responses, formatting limits.
"""

# Allowed citation URLs (whitelist from architecture — 10 Groww fund pages)
ALLOWED_URLS = [
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

# Canned response when PII is detected in LLM output (6.1)
CANNED_PII_RESPONSE = (
    "I cannot process personal information. Please do not share sensitive details "
    "like PAN, Aadhaar, or bank information."
)

# Canned response when advice leak is detected (6.2) — redirect to fund page
CANNED_ADVICE_RESPONSE_TEMPLATE = (
    "I'm unable to provide investment advice or compare fund performance. "
    "You can review the fund details here: {url}"
)
DEFAULT_FUND_PAGE_URL = "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth"

# Formatting (6.4)
MAX_SENTENCES = 5
CITATION_PREFIX = "Last updated from sources:"
