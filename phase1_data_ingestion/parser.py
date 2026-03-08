"""
Parse raw Groww mutual-fund HTML into structured JSON.

Uses BeautifulSoup to extract tables, headings, and key-value sections.
"""

import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


def _clean(text: str) -> str:
    """Collapse whitespace and strip."""
    return re.sub(r"\s+", " ", text).strip()


def _get_next_data_mf(soup: BeautifulSoup) -> dict:
    """Extract mfServerSideData from __NEXT_DATA__ script if present."""
    import json as _json
    script = soup.find("script", id="__NEXT_DATA__", type="application/json")
    if not script or not script.string:
        return {}
    try:
        data = _json.loads(script.string)
        return data.get("props", {}).get("pageProps", {}).get("mfServerSideData", {}) or {}
    except Exception:
        return {}


def _parse_table(table: Tag) -> list[dict[str, str]]:
    """Parse an HTML <table> into a list of row dicts keyed by header text."""
    headers: list[str] = []
    head = table.find("thead")
    if head:
        headers = [_clean(th.get_text()) for th in head.find_all(["th", "td"])]

    rows: list[dict[str, str]] = []
    body = table.find("tbody") or table
    for tr in body.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if not headers:
            headers = [_clean(c.get_text()) for c in cells]
            continue
        row = {}
        for idx, cell in enumerate(cells):
            key = headers[idx] if idx < len(headers) else f"col_{idx}"
            row[key] = _clean(cell.get_text())
        if row:
            rows.append(row)
    return rows


def _extract_basic_info(soup: BeautifulSoup, page_text: str) -> dict:
    """Extract NAV, fund size, expense ratio, min SIP from the page."""
    info: dict = {}

    nav_match = re.search(r"NAV[:\s]*\d{2}\s\w+\s['\u2019]?\d{2,4}\s*[₹Rs.]*\s*([\d,]+(?:\.\d+)?)", page_text)
    if nav_match:
        info["nav"] = nav_match.group(1)

    nav_date_match = re.search(r"NAV[:\s]*(\d{2}\s\w+\s['\u2019]?\d{2,4})", page_text)
    if nav_date_match:
        info["nav_date"] = nav_date_match.group(1)

    fund_size_match = re.search(r"Fund\s*size\s*[₹Rs.]*\s*([\d,]+(?:\.\d+)?)\s*(Cr|Lakh|L)?", page_text, re.I)
    if fund_size_match:
        info["fund_size_cr"] = fund_size_match.group(1)

    expense_match = re.search(r"Expense\s*ratio\s*([\d.]+)%", page_text, re.I)
    if expense_match:
        info["expense_ratio_pct"] = expense_match.group(1)

    sip_match = re.search(r"Min\.?\s*(?:for\s)?SIP\s*[₹Rs.]*\s*([\d,]+)", page_text, re.I)
    if sip_match:
        info["min_sip"] = sip_match.group(1)

    return info


def _format_return(val) -> str | None:
    """Format numeric return as +X.XX% or -X.XX%."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return f"{val:+.2f}%" if val >= 0 else f"{val:.2f}%"
    return str(val).strip() or None


def _extract_returns(page_text: str, tables_by_type: dict, fund_name: str, soup: BeautifulSoup | None = None) -> dict:
    """Extract performance return percentages for 1D, 1M, 6M, 1Y, 3Y, 5Y, 10Y, All."""
    returns: dict = {"1D": None, "1M": None, "6M": None, "1Y": None, "3Y": None, "5Y": None, "10Y": None, "All": None}

    mf = _get_next_data_mf(soup) if soup else {}
    return_stats = mf.get("return_stats") or []
    if return_stats and isinstance(return_stats[0], dict):
        rs = return_stats[0]
        mapping = (
            ("return1d", "1D"),
            ("return1m", "1M"),
            ("return6m", "6M"),
            ("return1y", "1Y"),
            ("return3y", "3Y"),
            ("return5y", "5Y"),
            ("return10y", "10Y"),
            ("return_since_created", "All"),
        )
        for key, out_key in mapping:
            val = rs.get(key)
            if val is not None:
                returns[out_key] = _format_return(val)

    raw_rankings = tables_by_type.get("returns_and_rankings", [])
    rankings = raw_rankings[0] if raw_rankings and isinstance(raw_rankings[0], list) else raw_rankings
    for row in rankings if isinstance(rankings, list) else []:
        if not isinstance(row, dict):
            continue
        name = row.get("Name", "").lower()
        if "fund return" in name:
            for period in ("3Y", "5Y", "10Y", "All"):
                if returns.get(period) is None:
                    val = row.get(period)
                    if val and val != "--":
                        returns[period] = val
            break

    similar = tables_by_type.get("similar_funds", [])
    for row in similar:
        if fund_name and _clean(fund_name).lower() in row.get("Name", "").lower():
            if returns.get("1Y") is None:
                val = row.get("1Y")
                if val:
                    returns["1Y"] = val
            break

    return {k: v for k, v in returns.items() if v is not None}


def _extract_fund_category_and_risk(page_text: str) -> dict:
    """Extract category, type, and risk level from the About section."""
    info: dict = {}

    cat_match = re.search(r"is\s+a\s+(Equity|Debt|Hybrid|Other)\s+Mutual\s+Fund", page_text, re.I)
    if cat_match:
        info["fund_category"] = cat_match.group(1).title()

    type_match = re.search(
        r"(Small\s*Cap|Mid\s*Cap|Large\s*Cap|Flexi\s*Cap|Multi\s*Cap|Infrastructure|ELSS|ESG|Focused|Aggressive\s*Hybrid|Tax\s*Saver)",
        page_text,
        re.I,
    )
    if type_match:
        info["fund_type"] = type_match.group(1).strip()

    risk_match = re.search(r"(Very\s*High|High|Moderate(?:ly\s*High)?|Low(?:\s*to\s*Moderate)?)\s*[Rr]isk", page_text)
    if risk_match:
        info["risk_level"] = risk_match.group(1).strip() + " Risk"

    return info


def _classify_table(rows: list[dict], table_index: int) -> str | None:
    """Guess which section a table belongs to based on its column headers."""
    if not rows:
        return None
    keys_lower = {k.lower().strip() for k in rows[0].keys()}

    if {"name", "sector", "instruments", "assets"} <= keys_lower:
        return "holdings"
    if "over the past" in keys_lower or "total investment" in keys_lower:
        return "return_calculator"
    if "fund size(cr)" in keys_lower or any("fund size" in k for k in keys_lower):
        return "similar_funds"
    if "3y" in keys_lower and ("5y" in keys_lower or "all" in keys_lower):
        return "returns_and_rankings"
    if keys_lower == {"name"} and len(rows) <= 5:
        first_val = list(rows[0].values())[0] if rows else ""
        if "IDCW" in first_val or "Growth" in first_val or "Direct" in first_val:
            return "other_plans"
    return None


def _parse_return_pct(s: str) -> float | None:
    """Parse return string like '+27.16%' or '-13.08%' to float."""
    if not s:
        return None
    s = str(s).replace("%", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def _extract_return_calculator(tables_by_type: dict, soup: BeautifulSoup | None = None) -> dict:
    """Return calculator: monthly_investment_used, sip rows, sip_return_rates (for any amount), lump_sum."""
    raw_rows = tables_by_type.get("return_calculator", [])
    sip_rows: list[dict] = []
    sip_return_rates: list[dict] = []
    monthly_used: str | None = None
    for row in raw_rows:
        total_inv = row.get("Total investment", "").replace("₹", "").replace(",", "").strip()
        over = row.get("Over the past", "")
        ret_str = row.get("Returns", "")
        if total_inv and over and "year" in over.lower():
            try:
                years = 1 if "1 year" in over.lower() else int(re.search(r"\d+", over).group())
                inv_num = int(total_inv)
                if years > 0 and inv_num % (12 * years) == 0:
                    monthly_used = str(inv_num // (12 * years))
            except (ValueError, AttributeError):
                pass
        sip_rows.append({
            "Over the past": row.get("Over the past"),
            "Total investment": row.get("Total investment"),
            "Would've become": row.get("Would've become"),
            "Returns": ret_str,
        })
        pct = _parse_return_pct(ret_str)
        if pct is not None and over:
            sip_return_rates.append({"period": over.strip(), "return_pct": round(pct, 2)})

    result: dict = {
        "monthly_investment_used": monthly_used or "1000",
        "sip": sip_rows,
        "sip_return_rates": sip_return_rates,
    }
    return result


def _extract_holdings(tables_by_type: dict) -> list[dict]:
    return tables_by_type.get("holdings", [])


def _extract_holding_analysis(holdings: list[dict], page_text: str = "") -> dict:
    """Extract equity/debt/cash split and sector allocation from the page text.

    The Groww page displays explicit summary figures (e.g. Equity 98.27%,
    Debt 5.48%, Cash -3.75%) and a dedicated sector allocation section
    that differ from naively summing individual holdings.  We parse these
    directly from the rendered text instead.
    """
    # --- equity / debt / cash split ---
    equity_pct = 0.0
    debt_pct = 0.0
    cash_pct = 0.0

    lines = page_text.split("\n") if page_text else []
    for i, line in enumerate(lines):
        label = line.strip()
        if label in ("Equity", "Debt", "Cash") and i + 1 < len(lines):
            next_val = lines[i + 1].strip().replace("%", "")
            try:
                val = float(next_val)
            except ValueError:
                continue
            if label == "Equity":
                equity_pct = val
            elif label == "Debt":
                debt_pct = val
            elif label == "Cash":
                cash_pct = val

    # --- sector allocation from "sector allocation" section ---
    sector_allocation: list[dict] = []
    m = re.search(r"sector allocation(.*?)(?=₹|Advanced|About|Fund management|Understand|$)", page_text, re.S | re.I)
    if m:
        block = m.group(1)
        pairs = re.findall(r"([A-Za-z &]+?)\s*\n\s*([\d.]+%)", block)
        for sector_name, pct_str in pairs:
            try:
                sector_allocation.append({"sector": sector_name.strip(), "percentage": float(pct_str.replace("%", ""))})
            except ValueError:
                continue

    return {
        "equity_debt_cash_split": {
            "equity_pct": equity_pct,
            "debt_pct": debt_pct,
            "cash_pct": cash_pct,
        },
        "sector_allocation": sector_allocation,
    }


def _format_pct(val: float) -> str:
    """Format float as +X.XX% or -X.XX%."""
    return f"{val:+.2f}%" if val >= 0 else f"{val:.2f}%"


def _extract_returns_and_rankings(tables_by_type: dict, soup: BeautifulSoup | None = None) -> dict:
    """Return annualised_returns and absolute_returns.

    The Groww page shows a table with two tabs — "Annualised returns" and
    "Absolute returns".  The HTML table only contains the annualised view.
    The absolute returns come from ``simple_return`` in ``__NEXT_DATA__``
    which holds the actual total returns over each period.
    """
    raw = tables_by_type.get("returns_and_rankings", [])
    annualised: list[dict] = []
    if raw:
        annualised = raw[0] if isinstance(raw[0], list) else raw

    # Column label → simple_return key mapping
    col_to_key: dict[str, str] = {
        "6M": "return6m", "1Y": "return1y", "3Y": "return3y",
        "5Y": "return5y", "10Y": "return10y", "All": "return_since_created",
    }
    cat_col_to_key: dict[str, str] = {
        "6M": "cat_return6m", "1Y": "cat_return1y", "3Y": "cat_return3y",
        "5Y": "cat_return5y", "10Y": "cat_return10y", "All": "cat_return_since_launch",
    }

    mf = _get_next_data_mf(soup) if soup else {}
    simple_ret = mf.get("simple_return") or {}

    absolute: list[dict] = []
    for ann_row in annualised:
        name = ann_row.get("Name", "")
        is_rank = "rank" in name.lower()
        is_category = "category" in name.lower()
        abs_row: dict = {"Name": name}
        for col in ann_row:
            if col == "Name":
                continue
            if is_rank:
                abs_row[col] = ann_row[col]
                continue
            # Look up the real absolute value from simple_return
            lookup = cat_col_to_key if is_category else col_to_key
            sr_key = lookup.get(col)
            sr_val = simple_ret.get(sr_key) if sr_key else None
            if sr_val is not None:
                try:
                    abs_row[col] = _format_pct(float(sr_val))
                except (TypeError, ValueError):
                    abs_row[col] = ann_row.get(col, "--")
            else:
                abs_row[col] = "--"
        if len(abs_row) > 1:
            absolute.append(abs_row)

    return {"annualised_returns": annualised, "absolute_returns": absolute}


def _extract_advanced_ratios(page_text: str, soup: BeautifulSoup, mf: dict | None = None) -> dict:
    """
    Extract advanced ratios: Top 5 %, Top 20 % (concentration), P/E Ratio, P/B Ratio (fund-level), Alpha, Beta, Sharpe, Sortino.
    Top 5 and Top 20 are single numbers (percentage); P/E and P/B are separate fund-level, not under top_5/top_20.
    """
    ratios: dict = {
        "top_5": None,
        "top_20": None,
        "pe_ratio": None,
        "pb_ratio": None,
        "alpha": None,
        "beta": None,
        "sharpe": None,
        "sortino": None,
    }

    if mf is None:
        mf = _get_next_data_mf(soup)

    return_stats = mf.get("return_stats") or []
    if return_stats and isinstance(return_stats[0], dict):
        rs = return_stats[0]
        for key, out_key in (
            ("alpha", "alpha"),
            ("beta", "beta"),
            ("sharpe_ratio", "sharpe"),
            ("sortino_ratio", "sortino"),
        ):
            val = rs.get(key)
            if val is not None:
                ratios[out_key] = round(float(val), 2) if isinstance(val, (int, float)) else val

    add = mf.get("additional_details")
    if isinstance(add, dict):
        for key in ("pe_ratio", "pb_ratio"):
            val = add.get(key) or add.get("pe" if key == "pe_ratio" else "pb")
            if val is not None:
                try:
                    ratios[key] = round(float(val), 2)
                except (TypeError, ValueError):
                    ratios[key] = val

    holdings = mf.get("holdings") or []
    if isinstance(holdings, list) and holdings:
        sorted_h = sorted(
            (h for h in holdings if isinstance(h, dict) and h.get("corpus_per") is not None),
            key=lambda x: float(x.get("corpus_per", 0)),
            reverse=True,
        )
        top5_sum = sum(float(h.get("corpus_per", 0)) for h in sorted_h[:5])
        top20_sum = sum(float(h.get("corpus_per", 0)) for h in sorted_h[:20])
        ratios["top_5"] = f"{round(top5_sum):.0f}%"
        ratios["top_20"] = f"{round(top20_sum):.0f}%"

    if ratios["pe_ratio"] is None:
        pe_match = re.search(r"P/E\s*ratio[:\s]*([\d.]+)", page_text, re.I)
        if pe_match:
            try:
                ratios["pe_ratio"] = round(float(pe_match.group(1)), 2)
            except ValueError:
                ratios["pe_ratio"] = pe_match.group(1)
    if ratios["pb_ratio"] is None:
        pb_match = re.search(r"P/B\s*ratio[:\s]*([\d.]+)", page_text, re.I)
        if pb_match:
            try:
                ratios["pb_ratio"] = round(float(pb_match.group(1)), 2)
            except ValueError:
                ratios["pb_ratio"] = pb_match.group(1)
    # Fallback: search __NEXT_DATA__ for portfolio-level pe/pb keys (avoid matching sharpe_ratio/sortino_ratio)
    if (ratios["pe_ratio"] is None or ratios["pb_ratio"] is None) and mf:
        try:
            import json as _json
            js_str = _json.dumps(mf)
            if ratios["pe_ratio"] is None:
                pe_m = re.search(r'"(?:portfolio_pe|pe_ratio|weighted_pe)"\s*:\s*([0-9.]+)', js_str)
                if pe_m and 10 <= float(pe_m.group(1)) <= 50:
                    ratios["pe_ratio"] = round(float(pe_m.group(1)), 2)
            if ratios["pb_ratio"] is None:
                pb_m = re.search(r'"(?:portfolio_pb|pb_ratio|weighted_pb)"\s*:\s*([0-9.]+)', js_str)
                if pb_m and 0.5 <= float(pb_m.group(1)) <= 10:
                    ratios["pb_ratio"] = round(float(pb_m.group(1)), 2)
        except Exception:
            pass
    if ratios["sharpe"] is None:
        sharpe_match = re.search(r"Sharpe\s*ratio[:\s]*([\d.]+)", page_text, re.I)
        if sharpe_match:
            try:
                ratios["sharpe"] = round(float(sharpe_match.group(1)), 2)
            except ValueError:
                pass

    return ratios


def _extract_other_plans(tables_by_type: dict) -> list[dict]:
    """Extract other plans in the same fund (e.g. IDCW, Growth)."""
    rows = tables_by_type.get("other_plans", [])
    return [{"name": _clean(list(r.values())[0])} for r in rows if r and list(r.values())[0]]


def _extract_similar_funds(tables_by_type: dict) -> list[dict]:
    return tables_by_type.get("similar_funds", [])


def _extract_minimum_investments(page_text: str) -> dict:
    inv: dict = {}
    first_match = re.search(r"Min\.?\s*(?:for\s)?1st\s*investment\s*[₹Rs.]*\s*([\d,]+)", page_text, re.I)
    if first_match:
        inv["min_first_investment"] = first_match.group(1)

    second_match = re.search(r"Min\.?\s*(?:for\s)?2nd\s*investment\s*[₹Rs.]*\s*([\d,]+)", page_text, re.I)
    if second_match:
        inv["min_second_investment"] = second_match.group(1)

    sip_match = re.search(r"Min\.?\s*(?:for\s)?SIP\s*[₹Rs.]*\s*([\d,]+)", page_text, re.I)
    if sip_match:
        inv["min_sip"] = sip_match.group(1)
    return inv


def _extract_exit_load(page_text: str) -> str | None:
    m = re.search(r"Exit\s*load\s+of\s+(\d+%\s*if\s*redeemed.*?)(?:\n|$)", page_text, re.I)
    if m:
        return _clean(m.group(0))
    m2 = re.search(r"Exit\s*[Ll]oad\s*[:\s]*(.*?)(?:\n|$)", page_text)
    return _clean(m2.group(0)) if m2 else None


def _extract_stamp_duty(page_text: str) -> str | None:
    m = re.search(r"[Ss]tamp\s*duty\s*on\s*investment[:\s]*([\d.]+%)", page_text)
    return f"Stamp duty on investment: {m.group(1)}" if m else None


def _extract_tax_implication(page_text: str) -> str | None:
    m = re.search(
        r"(If\s+you\s+redeem\s+within.*?taxed\s+at\s+[\d.]+%\.?"
        r"(?:\s*If\s+you\s+redeem\s+after.*?taxed\s+at\s+[\d.]+%\.?)?)",
        page_text, re.I | re.DOTALL,
    )
    return _clean(m.group(1)) if m else None


def _extract_fund_managers(soup: BeautifulSoup) -> list[dict]:
    """Extract fund manager names, tenure, education, and experience from the HTML."""
    managers: list[dict] = []
    accordions = soup.find_all(class_=re.compile(r"fundManagement_accordion__"))
    for acc in accordions:
        text = acc.get_text(separator="|", strip=True)
        mgr: dict = {}

        name_match = re.search(r"[A-Z]{2,4}\|([A-Z][a-z][\w\s.]+?)(?:\||$)", text)
        if name_match:
            mgr["name"] = name_match.group(1).strip()

        months = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        tenure_match = re.search(
            rf"({months}\s*\d{{4}})\s*\|?\s*[-–]\s*\|?\s*(Present|{months}\s*\d{{4}})", text
        )
        if tenure_match:
            mgr["tenure"] = f"{tenure_match.group(1)} - {tenure_match.group(2)}"

        edu_match = re.search(r"Education\|?(.*?)(?:\|?Experience|\|?Also)", text)
        if edu_match:
            mgr["education"] = edu_match.group(1).replace("|", " ").strip()

        exp_match = re.search(r"Experience\|?(.*?)(?:\|?Also manages|$)", text)
        if exp_match:
            mgr["experience"] = exp_match.group(1).replace("|", " ").strip()

        if mgr.get("name"):
            managers.append(mgr)
    return managers


def _extract_faqs(soup: BeautifulSoup) -> list[dict]:
    """Extract FAQ Q&A pairs from the JSON-LD structured data."""
    import json as _json

    faqs: list[dict] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = _json.loads(script.get_text())
        except _json.JSONDecodeError:
            continue
        if data.get("@type") != "FAQPage":
            continue
        for entity in data.get("mainEntity", []):
            question = entity.get("name", "")
            answer_html = entity.get("acceptedAnswer", {}).get("text", "")
            answer_text = BeautifulSoup(answer_html, "html.parser").get_text(strip=True)
            if question:
                faqs.append({"question": question, "answer": _clean(answer_text)})
    return faqs


def _extract_about_fund(page_text: str) -> dict:
    about: dict = {}

    about_match = re.search(r"About\s+(?:Quant\s+)?([\w\s]+?Fund.*?Growth)\s+(.*?)(?:Investment\s*Objective|Fund\s*benchmark)", page_text, re.DOTALL | re.I)
    if about_match:
        about["description"] = _clean(about_match.group(2))

    obj_match = re.search(r"Investment\s*Objective\s+(.*?)(?:Fund\s*benchmark|Scheme\s*Information|$)", page_text, re.DOTALL | re.I)
    if obj_match:
        about["investment_objective"] = _clean(obj_match.group(1))

    bench_match = re.search(r"Fund\s*benchmark\s*(.*?)(?:\n|Scheme)", page_text, re.I)
    if bench_match:
        about["benchmark"] = _clean(bench_match.group(1))

    return about


def _extract_fund_house(page_text: str) -> dict:
    house: dict = {}

    rank_match = re.search(r"Rank\s*\(total\s*assets\)\s*#?(\d+)\s*in\s*India", page_text, re.I)
    if rank_match:
        house["rank_in_india"] = int(rank_match.group(1))

    aum_match = re.search(r"Total\s*AUM\s*[₹Rs.]*\s*([\d,]+(?:\.\d+)?)\s*Cr", page_text, re.I)
    if aum_match:
        house["total_aum_cr"] = aum_match.group(1)

    inc_match = re.search(r"Date\s*of\s*Incorporation\s*(\d{1,2}\s+\w+\s+\d{4})", page_text, re.I)
    if inc_match:
        house["date_of_incorporation"] = inc_match.group(1)

    launch_match = re.search(r"Launch\s*Date\s*(\d{1,2}\s+\w+\s+\d{4})", page_text, re.I)
    if launch_match:
        house["launch_date"] = launch_match.group(1)

    phone_match = re.search(r"Phone\s*(\d{2,4}[-]?\d{6,8})", page_text, re.I)
    if phone_match:
        house["phone"] = phone_match.group(1).strip()

    email_match = re.search(r"E-mail\s*([^\n]+?)(?=\n\w|\n\s*Website|\Z)", page_text, re.I)
    if email_match:
        house["email"] = _clean(email_match.group(1))

    website_match = re.search(r"Website\s*(https?://[^\s\n]+|www\.[^\s\n]+)", page_text, re.I)
    if website_match:
        house["website"] = _clean(website_match.group(1))

    address_match = re.search(r"Address\s*(\d+.*?)(?=\s*Custodian|\s*Contact|\s*Email|\s*Website|\Z)", page_text, re.I | re.DOTALL)
    if address_match:
        house["address"] = _clean(address_match.group(1))

    return house


def parse_fund_page(html_path: Path, fund_key: str, source_url: str) -> dict:
    """
    Parse a single fund's raw HTML file into structured data.

    Returns a dict with all extracted sections.
    """
    html = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(separator="\n", strip=False)

    title_tag = soup.find("title")
    fund_name = _clean(title_tag.get_text()).split(" - ")[0] if title_tag else fund_key

    tables = soup.find_all("table")
    tables_by_type: dict = {}
    for idx, tbl in enumerate(tables):
        rows = _parse_table(tbl)
        ttype = _classify_table(rows, idx)
        if ttype:
            if ttype == "returns_and_rankings":
                tables_by_type.setdefault("returns_and_rankings", []).append(rows)
            else:
                tables_by_type[ttype] = rows

    holdings = _extract_holdings(tables_by_type)
    returns_rankings = _extract_returns_and_rankings(tables_by_type, soup)
    mf = _get_next_data_mf(soup)

    faqs = _extract_faqs(soup)

    data: dict = {
        "fund_key": fund_key,
        "fund_name": fund_name,
        "source_url": source_url,
        "basic_info": _extract_basic_info(soup, page_text),
        "fund_category_and_risk": _extract_fund_category_and_risk(page_text),
        "performance_returns": _extract_returns(page_text, tables_by_type, fund_name, soup),
        "return_calculator": _extract_return_calculator(tables_by_type, soup),
        "holdings": holdings,
        "holding_analysis": _extract_holding_analysis(holdings, page_text),
        "minimum_investments": _extract_minimum_investments(page_text),
        "returns_and_rankings": returns_rankings,
        "exit_load": _extract_exit_load(page_text),
        "stamp_duty": _extract_stamp_duty(page_text),
        "tax_implication": _extract_tax_implication(page_text),
        "similar_funds": _extract_similar_funds(tables_by_type),
        "fund_managers": _extract_fund_managers(soup),
        "about_fund": _extract_about_fund(page_text),
        "fund_house": _extract_fund_house(page_text),
        "advanced_ratios": _extract_advanced_ratios(page_text, soup, mf),
        "other_plans_in_same_fund": _extract_other_plans(tables_by_type),
        "faqs": faqs,
    }

    logger.info(
        "Parsed %s — %d holdings, %d managers, %d FAQs",
        fund_name, len(data["holdings"]), len(data["fund_managers"]), len(faqs),
    )
    return data
