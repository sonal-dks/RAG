"""
Phase 3 configuration — fund lookup table, typos, and abbreviation expansions.

Maps aliases/partial names to canonical fund name + URL for the 10 allowed schemes.
"""

# Canonical scheme names and URLs (from architecture.md)
FUND_LOOKUP: list[dict] = [
    {
        "fund_key": "quant-small-cap-fund",
        "canonical_name": "Quant Small Cap Fund Direct Plan Growth",
        "url": "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
        "aliases": ["small cap", "quant small cap", "small cap quant", "quant small cap fund"],
    },
    {
        "fund_key": "quant-infrastructure-fund",
        "canonical_name": "Quant Infrastructure Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/quant-infrastructure-fund-direct-growth",
        "aliases": ["infrastructure", "quant infrastructure", "quant infra"],
    },
    {
        "fund_key": "quant-flexi-cap-fund",
        "canonical_name": "Quant Flexi Cap Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/quant-flexi-cap-fund-direct-growth",
        "aliases": ["flexi cap", "quant flexi cap", "flexicap"],
    },
    {
        "fund_key": "quant-elss-tax-saver-fund",
        "canonical_name": "Quant ELSS Tax Saver Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/quant-elss-tax-saver-fund-direct-growth",
        "aliases": ["elss", "quant elss", "tax saver", "quant elss tax saver"],
    },
    {
        "fund_key": "quant-large-cap-fund",
        "canonical_name": "Quant Large Cap Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/quant-large-cap-fund-direct-growth",
        "aliases": ["large cap", "quant large cap", "quant large"],
    },
    {
        "fund_key": "quant-esg-integration-strategy-fund",
        "canonical_name": "Quant ESG Integration Strategy Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/quant-esg-integration-strategy-fund-direct-growth",
        "aliases": ["esg", "quant esg", "esg integration", "quant esg fund"],
    },
    {
        "fund_key": "quant-mid-cap-fund",
        "canonical_name": "Quant Mid Cap Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/quant-mid-cap-fund-direct-growth",
        "aliases": ["mid cap", "quant mid cap", "quant midcap"],
    },
    {
        "fund_key": "quant-multi-cap-fund",
        "canonical_name": "Quant Multi Cap Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/quant-multi-cap-fund-direct-growth",
        "aliases": ["multi cap", "quant multi cap", "multicap"],
    },
    {
        "fund_key": "quant-aggressive-hybrid-fund",
        "canonical_name": "Quant Aggressive Hybrid Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/quant-aggressive-hybrid-fund-direct-growth",
        "aliases": ["aggressive hybrid", "quant aggressive", "quant hybrid", "aggressive hybrid fund"],
    },
    {
        "fund_key": "quant-focused-fund",
        "canonical_name": "Quant Focused Fund Direct Growth",
        "url": "https://groww.in/mutual-funds/quant-focused-fund-direct-growth",
        "aliases": ["focused", "quant focused", "quant focused fund"],
    },
]

# Common typos (query rewriter)
TYPO_CORRECTIONS: dict[str, str] = {
    "expnse": "expense",
    "expence": "expense",
    "ration": "ratio",
    "holdngs": "holdings",
    "managemant": "management",
    "retuns": "returns",
    "anualised": "annualised",
    "annualized": "annualised",
}

# Abbreviation expansions (architecture: NAV → Net Asset Value (NAV), AUM → Assets Under Management (AUM))
ABBREVIATION_EXPANSIONS: dict[str, str] = {
    "nav": "Net Asset Value (NAV)",
    "aum": "Assets Under Management (AUM)",
    "sip": "Systematic Investment Plan (SIP)",
    "elss": "Equity Linked Savings Scheme (ELSS)",
    "amc": "Asset Management Company (AMC)",
    "sid": "Scheme Information Document (SID)",
    "kim": "Key Information Memorandum (KIM)",
}

# Message when no fund is mentioned
CLARIFICATION_MESSAGE = (
    "I can only answer questions about a specific Quant Mutual Fund. "
    "Please mention which fund you're asking about (e.g. Quant Small Cap Fund, Quant ELSS)."
)

# Section keywords -> section filter for metadata (must match Phase 4 chunking section names)
SECTION_KEYWORDS: dict[str, str] = {
    "holdings": "holdings",
    "portfolio": "holdings",
    "top holdings": "holdings",
    "returns": "performance_returns",
    "performance": "performance_returns",
    "nav": "basic_info",
    "expense ratio": "basic_info",
    "exit load": "exit_load",
    "tax": "tax_implication",
    "fund manager": "fund_managers",
    "manager": "fund_managers",
}
