"""Phase 1 configuration — URLs, scraping settings, and paths."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CACHE_DIR = Path(__file__).resolve().parent / "cache"

FUND_URLS: dict[str, str] = {
    "quant-small-cap-fund": "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth",
    "quant-infrastructure-fund": "https://groww.in/mutual-funds/quant-infrastructure-fund-direct-growth",
    "quant-flexi-cap-fund": "https://groww.in/mutual-funds/quant-flexi-cap-fund-direct-growth",
    "quant-elss-tax-saver-fund": "https://groww.in/mutual-funds/quant-elss-tax-saver-fund-direct-growth",
    "quant-large-cap-fund": "https://groww.in/mutual-funds/quant-large-cap-fund-direct-growth",
    "quant-esg-integration-strategy-fund": "https://groww.in/mutual-funds/quant-esg-integration-strategy-fund-direct-growth",
    "quant-mid-cap-fund": "https://groww.in/mutual-funds/quant-mid-cap-fund-direct-growth",
    "quant-multi-cap-fund": "https://groww.in/mutual-funds/quant-multi-cap-fund-direct-growth",
    "quant-aggressive-hybrid-fund": "https://groww.in/mutual-funds/quant-aggressive-hybrid-fund-direct-growth",
    "quant-focused-fund": "https://groww.in/mutual-funds/quant-focused-fund-direct-growth",
}

# Polite scraping settings
REQUEST_DELAY_SECONDS = 3
PAGE_LOAD_TIMEOUT_MS = 60_000
NAVIGATION_WAIT_UNTIL = "networkidle"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
