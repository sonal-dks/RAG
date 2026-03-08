"""
Phase 1 — Data Ingestion entry point.

Usage:
    python -m phase1_data_ingestion.run_ingestion            # scrape all funds
    python -m phase1_data_ingestion.run_ingestion --fund KEY # scrape one fund
"""

import argparse
import asyncio
import logging
import sys

from .config import FUND_URLS, RAW_DIR
from .parser import parse_fund_page
from .scraper import scrape_all_funds, scrape_single_fund
from .storage import save_all_funds, save_fund_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def run_full_pipeline() -> None:
    """Scrape → Parse → Store for all 10 funds."""
    logger.info("Starting full ingestion pipeline for %d funds", len(FUND_URLS))

    saved_files = await scrape_all_funds()

    all_parsed: list[dict] = []
    for fund_key, html_path in saved_files.items():
        url = FUND_URLS[fund_key]
        parsed = parse_fund_page(html_path, fund_key, url)
        save_fund_data(parsed)
        all_parsed.append(parsed)

    save_all_funds(all_parsed)
    logger.info("Pipeline complete. %d funds ingested.", len(all_parsed))


def run_parse_only() -> None:
    """Re-parse all existing raw HTML files and save. No scraping. Use for uniform output."""
    logger.info("Re-parsing existing raw HTML for %d funds (no scrape)", len(FUND_URLS))
    all_parsed: list[dict] = []
    for fund_key, url in FUND_URLS.items():
        html_path = RAW_DIR / f"{fund_key}.html"
        if not html_path.exists():
            logger.warning("No raw HTML for '%s', skipping", fund_key)
            continue
        parsed = parse_fund_page(html_path, fund_key, url)
        save_fund_data(parsed)
        all_parsed.append(parsed)
    if all_parsed:
        save_all_funds(all_parsed)
    logger.info("Parse-only complete. %d funds updated.", len(all_parsed))


async def run_single(fund_key: str) -> None:
    """Scrape → Parse → Store for one fund."""
    url = FUND_URLS.get(fund_key)
    if not url:
        logger.error("Unknown fund key '%s'. Valid keys:\n  %s", fund_key, "\n  ".join(FUND_URLS))
        sys.exit(1)

    html_path = await scrape_single_fund(fund_key)
    if not html_path:
        sys.exit(1)

    parsed = parse_fund_page(html_path, fund_key, url)
    save_fund_data(parsed)
    logger.info("Single-fund ingestion complete for '%s'.", fund_key)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1 — Data Ingestion")
    parser.add_argument(
        "--fund",
        type=str,
        default=None,
        help="Scrape a single fund by key (e.g. quant-small-cap-fund). "
        "Omit to scrape all 10 funds.",
    )
    parser.add_argument(
        "--parse-only",
        action="store_true",
        help="Re-parse existing raw HTML and save (no scrape). Use for uniform output.",
    )
    args = parser.parse_args()

    if args.parse_only:
        run_parse_only()
    elif args.fund:
        asyncio.run(run_single(args.fund))
    else:
        asyncio.run(run_full_pipeline())


if __name__ == "__main__":
    main()
