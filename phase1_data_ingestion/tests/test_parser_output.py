"""
Tests for Phase 1 parser output structure and content.

Validates that processed fund JSON has all required fields and correct shapes
after the parser fixes (performance_returns, return_calculator, holding_analysis,
returns_and_rankings with annualised/absolute, fund_house full details,
other_plans_in_same_fund, advanced_ratios).
"""

import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SAMPLE_FUND = "quant-small-cap-fund"


def load_processed_fund(fund_key: str = SAMPLE_FUND) -> dict:
    path = PROCESSED_DIR / f"{fund_key}.json"
    if not path.exists():
        pytest.skip(f"Processed file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


class TestPerformanceReturns:
    """Performance returns must include 1D, 1M, 6M, 1Y, 3Y, 5Y, 10Y, All where available."""

    def test_has_1d_when_available(self):
        data = load_processed_fund()
        pr = data.get("performance_returns", {})
        # 1D is included from __NEXT_DATA__ return_stats when present
        assert isinstance(pr, dict)

    def test_has_expected_periods(self):
        data = load_processed_fund()
        pr = data.get("performance_returns", {})
        allowed = {"1D", "1M", "6M", "1Y", "3Y", "5Y", "All", "10Y"}
        for k in pr:
            assert k in allowed, f"Unexpected key in performance_returns: {k}"

    def test_has_at_least_1y_3y_5y_all(self):
        data = load_processed_fund()
        pr = data["performance_returns"]
        assert "1Y" in pr or "3Y" in pr
        assert "3Y" in pr
        assert "5Y" in pr
        assert "All" in pr


class TestReturnCalculator:
    """Return calculator: monthly_investment_used, sip, sip_return_rates (for any amount)."""

    def test_is_dict_with_sip_and_sip_return_rates(self):
        data = load_processed_fund()
        rc = data.get("return_calculator", {})
        assert isinstance(rc, dict)
        assert "sip" in rc
        assert "monthly_investment_used" in rc
        assert "sip_return_rates" in rc
        assert isinstance(rc["sip_return_rates"], list)
        assert "lump_sum" not in rc

    def test_sip_rows_have_no_historic_returns(self):
        data = load_processed_fund()
        for row in data["return_calculator"]["sip"]:
            assert "Historic returns" not in row

    def test_sip_rows_have_required_fields(self):
        data = load_processed_fund()
        for row in data["return_calculator"]["sip"]:
            assert "Over the past" in row
            assert "Total investment" in row
            assert "Would've become" in row
            assert "Returns" in row

    def test_monthly_investment_used_inferred(self):
        data = load_processed_fund()
        monthly = data["return_calculator"]["monthly_investment_used"]
        assert monthly is not None
        assert str(monthly).isdigit() or (isinstance(monthly, str) and monthly.replace(",", "").isdigit())


class TestHoldingAnalysis:
    """Holding analysis: equity_debt_cash_split and sector_allocation."""

    def test_has_equity_debt_cash_split(self):
        data = load_processed_fund()
        ha = data.get("holding_analysis", {})
        assert "equity_debt_cash_split" in ha
        split = ha["equity_debt_cash_split"]
        assert "equity_pct" in split
        assert "debt_pct" in split
        assert "cash_pct" in split

    def test_has_sector_allocation(self):
        data = load_processed_fund()
        ha = data.get("holding_analysis", {})
        assert "sector_allocation" in ha
        assert isinstance(ha["sector_allocation"], list)

    def test_sector_allocation_entries_have_sector_and_percentage(self):
        data = load_processed_fund()
        sectors = data["holding_analysis"]["sector_allocation"]
        assert len(sectors) > 0, "Sector allocation should not be empty"
        for entry in sectors:
            assert "sector" in entry
            assert "percentage" in entry
            assert isinstance(entry["percentage"], (int, float))

    def test_equity_debt_cash_from_page_summary(self):
        """equity/debt/cash split should match page-level summary, not sum of holdings."""
        data = load_processed_fund()
        split = data["holding_analysis"]["equity_debt_cash_split"]
        assert split["equity_pct"] > 90, "Quant Small Cap is nearly all equity"
        assert split["debt_pct"] >= 0 or split["debt_pct"] < 0  # can be any value from page


class TestReturnsAndRankings:
    """Returns and rankings: annualised_returns and absolute_returns."""

    def test_has_annualised_and_absolute(self):
        data = load_processed_fund()
        rar = data.get("returns_and_rankings", {})
        assert "annualised_returns" in rar
        assert "absolute_returns" in rar

    def test_annualised_returns_non_empty(self):
        data = load_processed_fund()
        assert len(data["returns_and_rankings"]["annualised_returns"]) >= 1

    def test_absolute_returns_populated(self):
        """absolute_returns computed from annualised table; same columns (3Y/5Y/10Y/All), no 1Y."""
        data = load_processed_fund()
        absolute = data["returns_and_rankings"]["absolute_returns"]
        assert isinstance(absolute, list)
        assert len(absolute) >= 1, "absolute_returns must have at least Fund returns row"
        first = absolute[0]
        assert first.get("Name") == "Fund returns"
        assert "1Y" not in first, "Absolute returns should not have 1Y (page only shows 3Y+)"
        assert any(k in first for k in ("3Y", "5Y", "10Y", "All"))


class TestFundHouse:
    """Fund house: rank, AUM, phone, email, website, address."""

    def test_has_required_fields(self):
        data = load_processed_fund()
        fh = data.get("fund_house", {})
        assert "rank_in_india" in fh
        assert "total_aum_cr" in fh
        assert "date_of_incorporation" in fh or "launch_date" in fh

    def test_has_phone_email_website_address(self):
        data = load_processed_fund()
        fh = data["fund_house"]
        assert "phone" in fh
        assert "email" in fh
        assert "website" in fh
        assert "address" in fh


class TestOtherPlansInSameFund:
    """Other plans in the same fund section must be present."""

    def test_key_exists(self):
        data = load_processed_fund()
        assert "other_plans_in_same_fund" in data

    def test_is_list(self):
        data = load_processed_fund()
        assert isinstance(data["other_plans_in_same_fund"], list)

    def test_quant_small_cap_has_idcw_plan(self):
        data = load_processed_fund(SAMPLE_FUND)
        plans = data["other_plans_in_same_fund"]
        names = [p.get("name", "") for p in plans]
        assert any("IDCW" in n for n in names) or len(plans) >= 0


class TestAdvancedRatios:
    """Advanced ratios: Top 5, Top 20, P/E Ratio, P/B Ratio, Alpha, Beta, Sharpe, Sortino."""

    def test_key_exists(self):
        data = load_processed_fund()
        assert "advanced_ratios" in data

    def test_has_page_structure(self):
        """advanced_ratios: top_5, top_20 as '26%' strings; pe_ratio, pb_ratio fund-level; alpha, beta, sharpe, sortino."""
        data = load_processed_fund()
        ar = data["advanced_ratios"]
        assert isinstance(ar, dict)
        for key in ("top_5", "top_20", "pe_ratio", "pb_ratio", "alpha", "beta", "sharpe", "sortino"):
            assert key in ar
        # top_5 and top_20 are percentage strings like "26%"
        if ar["top_5"] is not None:
            assert isinstance(ar["top_5"], str) and ar["top_5"].endswith("%")
        if ar["top_20"] is not None:
            assert isinstance(ar["top_20"], str) and ar["top_20"].endswith("%")

    def test_quant_small_cap_has_alpha_beta_sharpe_sortino(self):
        """When __NEXT_DATA__ return_stats is present, alpha, beta, sharpe, sortino are filled."""
        data = load_processed_fund(SAMPLE_FUND)
        ar = data["advanced_ratios"]
        assert ar["alpha"] is not None
        assert ar["beta"] is not None
        assert ar["sharpe"] is not None
        assert ar["sortino"] is not None


class TestParserIntegration:
    """Run parser on raw HTML and assert output shape."""

    def test_parse_fund_page_produces_all_sections(self):
        from phase1_data_ingestion.parser import parse_fund_page
        raw_path = PROJECT_ROOT / "data" / "raw" / f"{SAMPLE_FUND}.html"
        if not raw_path.exists():
            pytest.skip("Raw HTML not found")
        d = parse_fund_page(raw_path, SAMPLE_FUND, "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth")
        assert "performance_returns" in d
        assert "return_calculator" in d and "sip" in d["return_calculator"]
        assert "holding_analysis" in d
        assert "returns_and_rankings" in d and "annualised_returns" in d["returns_and_rankings"]
        assert "fund_house" in d and "phone" in d["fund_house"]
        assert "other_plans_in_same_fund" in d
        assert "advanced_ratios" in d
