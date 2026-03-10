"""
Playwright-based scraper with polite scraping practices.

- Request throttling (configurable delay between requests)
- Content-hash caching (skip re-download if page unchanged)
- Headless Chromium for JS-rendered Groww pages
"""

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path

from playwright.async_api import async_playwright

from .config import (
    CACHE_DIR,
    FUND_URLS,
    NAVIGATION_WAIT_UNTIL,
    PAGE_LOAD_TIMEOUT_MS,
    RAW_DIR,
    REQUEST_DELAY_SECONDS,
    USER_AGENT,
)

logger = logging.getLogger(__name__)

CACHE_INDEX_FILE = CACHE_DIR / "cache_index.json"


def _load_cache_index() -> dict:
    if CACHE_INDEX_FILE.exists():
        return json.loads(CACHE_INDEX_FILE.read_text())
    return {}


def _save_cache_index(index: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_INDEX_FILE.write_text(json.dumps(index, indent=2))


def _content_hash(html: str) -> str:
    return hashlib.sha256(html.encode("utf-8")).hexdigest()


async def scrape_all_funds(force_refresh: bool = False) -> dict[str, Path]:
    """
    Scrape all fund URLs and return a mapping of fund_key → saved HTML path.
    Skips a URL if the cached content hash is identical (page unchanged).
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache_index = _load_cache_index()
    saved_files: dict[str, Path] = {}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()
        page.set_default_timeout(PAGE_LOAD_TIMEOUT_MS)

        for i, (fund_key, url) in enumerate(FUND_URLS.items()):
            if i > 0:
                logger.info("Throttling: waiting %ss before next request", REQUEST_DELAY_SECONDS)
                await asyncio.sleep(REQUEST_DELAY_SECONDS)

            logger.info("Scraping [%d/%d]: %s", i + 1, len(FUND_URLS), url)

            try:
                await page.goto(url, wait_until=NAVIGATION_WAIT_UNTIL, timeout=PAGE_LOAD_TIMEOUT_MS)
                await page.wait_for_timeout(2000)
                # Scroll to bottom to trigger lazy-loaded sections (e.g. Returns and rankings, Advanced ratios)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2500)

                html = await page.content()
                new_hash = _content_hash(html)

                if not force_refresh and cache_index.get(fund_key, {}).get("hash") == new_hash:
                    logger.info("  ↳ Content unchanged (cached). Skipping write.")
                    saved_files[fund_key] = Path(cache_index[fund_key]["file"])
                    continue

                out_path = RAW_DIR / f"{fund_key}.html"
                out_path.write_text(html, encoding="utf-8")

                cache_index[fund_key] = {
                    "hash": new_hash,
                    "file": str(out_path),
                    "url": url,
                    "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                }
                saved_files[fund_key] = out_path
                logger.info("  ↳ Saved → %s", out_path)

            except Exception:
                logger.exception("  ✗ Failed to scrape %s", url)

        _save_cache_index(cache_index)
        await browser.close()

    logger.info("Scraping complete. %d/%d pages saved.", len(saved_files), len(FUND_URLS))
    return saved_files


async def scrape_single_fund(fund_key: str) -> Path | None:
    """Scrape a single fund by its key (for testing / ad-hoc runs)."""
    url = FUND_URLS.get(fund_key)
    if not url:
        logger.error("Unknown fund key: %s", fund_key)
        return None

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()
        page.set_default_timeout(PAGE_LOAD_TIMEOUT_MS)

        logger.info("Scraping: %s", url)
        await page.goto(url, wait_until=NAVIGATION_WAIT_UNTIL, timeout=PAGE_LOAD_TIMEOUT_MS)
        await page.wait_for_timeout(2000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2500)

        html = await page.content()
        out_path = RAW_DIR / f"{fund_key}.html"
        out_path.write_text(html, encoding="utf-8")
        logger.info("Saved → %s", out_path)

        await browser.close()
        return out_path
