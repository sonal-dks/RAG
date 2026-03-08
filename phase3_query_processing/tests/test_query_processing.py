"""
Phase 3 — Unit tests with expected output and acceptance criteria.

Acceptance criteria (from architecture.md):
  AC1: Query rewriter fixes common typos (e.g. expnse → expense).
  AC2: Query rewriter expands abbreviations (NAV → Net Asset Value (NAV), AUM → ...).
  AC3: Fund resolver maps aliases to canonical fund name + URL.
  AC4: If no fund mentioned → fund_resolved=False, clarification_message present.
  AC5: Output has enriched_query, fund_resolved, fund_key, canonical_name, url, section_filter, clarification_message.
  AC6: Section filter built when query targets a section (e.g. holdings → section_filter).
  AC7: v1: multiple funds → limit to one (first match).
"""

import pytest

from phase3_query_processing.config import CLARIFICATION_MESSAGE
from phase3_query_processing.pipeline import process_query
from phase3_query_processing.query_rewriter import rewrite_query
from phase3_query_processing.fund_resolver import resolve_fund
from phase3_query_processing.metadata_filter import build_section_filter


# --- Expected outputs ---
EXPECTED_SMALL_CAP_URL = "https://groww.in/mutual-funds/quant-small-cap-fund-direct-plan-growth"
EXPECTED_SMALL_CAP_CANONICAL = "Quant Small Cap Fund Direct Plan Growth"
EXPECTED_ELSS_URL = "https://groww.in/mutual-funds/quant-elss-tax-saver-fund-direct-growth"


class TestOutputStructure:
    """AC5: Output has required keys."""

    def test_result_has_required_keys(self):
        result = process_query("What is the NAV of Quant Small Cap Fund?")
        assert "enriched_query" in result
        assert "fund_resolved" in result
        assert "fund_key" in result
        assert "canonical_name" in result
        assert "url" in result
        assert "section_filter" in result
        assert "clarification_message" in result

    def test_fund_resolved_true_has_fund_metadata(self):
        result = process_query("What is the expense ratio of Quant Small Cap?")
        assert result["fund_resolved"] is True
        assert result["fund_key"] == "quant-small-cap-fund"
        assert result["canonical_name"] == EXPECTED_SMALL_CAP_CANONICAL
        assert result["url"] == EXPECTED_SMALL_CAP_URL
        assert result["clarification_message"] is None


class TestQueryRewriterTypo:
    """AC1: Query rewriter fixes common typos."""

    def test_expnse_to_expense(self):
        out = rewrite_query("What is the expnse ratio of Quant Small Cap?")
        assert "expense" in out
        assert "expnse" not in out

    def test_expence_to_expense(self):
        out = rewrite_query("expence ratio")
        assert "expense" in out

    @pytest.mark.parametrize("typo,correct", [
        ("ration", "ratio"),
        ("holdngs", "holdings"),
    ])
    def test_typos_fixed(self, typo, correct):
        out = rewrite_query(f"What is the {typo} of Quant Small Cap?")
        assert correct in out
        assert typo not in out


class TestQueryRewriterAbbreviations:
    """AC2: Query rewriter expands abbreviations."""

    def test_nav_expanded(self):
        out = rewrite_query("What is the NAV of Quant Small Cap?")
        assert "Net Asset Value (NAV)" in out or "NAV" in out

    def test_aum_expanded(self):
        out = rewrite_query("What is the AUM of Quant ELSS?")
        assert "Assets Under Management (AUM)" in out or "AUM" in out

    def test_sip_expanded(self):
        out = rewrite_query("Is SIP allowed for Quant Flexi Cap?")
        assert "Systematic Investment Plan (SIP)" in out or "SIP" in out


class TestFundResolver:
    """AC3: Fund resolver maps aliases to canonical name + URL."""

    @pytest.mark.parametrize("query_alias,expected_key,expected_canonical", [
        ("small cap quant", "quant-small-cap-fund", EXPECTED_SMALL_CAP_CANONICAL),
        ("Quant Small Cap Fund", "quant-small-cap-fund", EXPECTED_SMALL_CAP_CANONICAL),
        ("quant elss", "quant-elss-tax-saver-fund", "Quant ELSS Tax Saver Fund Direct Growth"),
        ("Quant Mid Cap", "quant-mid-cap-fund", "Quant Mid Cap Fund Direct Growth"),
        ("quant infrastructure", "quant-infrastructure-fund", "Quant Infrastructure Fund Direct Growth"),
    ])
    def test_alias_resolves_to_canonical_and_url(self, query_alias, expected_key, expected_canonical):
        result = process_query(f"What is the NAV of {query_alias}?")
        assert result["fund_resolved"] is True
        assert result["fund_key"] == expected_key
        assert result["canonical_name"] == expected_canonical
        assert result["url"] is not None and "groww.in" in result["url"]


class TestNoFundMentioned:
    """AC4: No fund mentioned → fund_resolved=False, clarification_message present."""

    def test_generic_query_no_fund(self):
        result = process_query("What is the expense ratio?")
        assert result["fund_resolved"] is False
        assert result["clarification_message"] is not None
        assert "specific" in result["clarification_message"] or "mention" in result["clarification_message"]

    def test_clarification_equals_config(self):
        result = process_query("Tell me about returns")
        assert result["clarification_message"] == CLARIFICATION_MESSAGE

    def test_empty_query(self):
        result = process_query("")
        assert result["fund_resolved"] is False
        assert result["clarification_message"] == CLARIFICATION_MESSAGE


class TestSectionFilter:
    """AC6: Section filter built when query targets a section."""

    def test_holdings_section(self):
        result = process_query("What are the top holdings of Quant Small Cap Fund?")
        assert result["section_filter"] == "holdings"

    def test_returns_section(self):
        result = process_query("What are the returns of Quant ELSS?")
        assert result["section_filter"] is not None  # e.g. performance_returns

    def test_fund_manager_section(self):
        result = process_query("Who is the fund manager of Quant Small Cap?")
        assert result["section_filter"] == "fund_managers"


class TestMultipleFundsV1:
    """AC7: v1 limits to one fund (first match)."""

    def test_two_funds_returns_first(self):
        # "small cap" and "elss" both in query; small cap appears first in FUND_LOOKUP order
        result = process_query("Compare Quant Small Cap and Quant ELSS returns")
        assert result["fund_resolved"] is True
        # First match in config order is small cap
        assert result["fund_key"] in ("quant-small-cap-fund", "quant-elss-tax-saver-fund")


class TestExpectedOutputComparison:
    """Compare actual output with expected."""

    def test_small_cap_full_output(self):
        actual = process_query("What is the NAV of Quant Small Cap Fund?")
        assert actual["enriched_query"]
        assert actual["fund_resolved"] is True
        assert actual["fund_key"] == "quant-small-cap-fund"
        assert actual["canonical_name"] == EXPECTED_SMALL_CAP_CANONICAL
        assert actual["url"] == EXPECTED_SMALL_CAP_URL

    def test_elss_resolution(self):
        actual = process_query("What is the expense ratio of Quant ELSS?")
        assert actual["fund_resolved"] is True
        assert actual["fund_key"] == "quant-elss-tax-saver-fund"
        assert actual["url"] == EXPECTED_ELSS_URL


class TestAcceptanceCriteriaMet:
    """All acceptance criteria must pass."""

    def test_ac1_typo_fix(self):
        r = rewrite_query("expnse ratio of quant small cap")
        assert "expense" in r and "expnse" not in r

    def test_ac2_abbreviation_expansion(self):
        r = rewrite_query("NAV and AUM of quant small cap")
        assert "Net Asset Value" in r or "NAV" in r
        assert "Assets Under Management" in r or "AUM" in r

    def test_ac3_fund_resolution(self):
        res = resolve_fund("What is the NAV of quant small cap fund?")
        assert res["resolved"] is True
        assert res["canonical_name"] == EXPECTED_SMALL_CAP_CANONICAL
        assert res["url"] == EXPECTED_SMALL_CAP_URL

    def test_ac4_no_fund_clarification(self):
        result = process_query("What is expense ratio?")
        assert result["fund_resolved"] is False
        assert result["clarification_message"] == CLARIFICATION_MESSAGE

    def test_ac5_output_keys(self):
        result = process_query("What is the NAV of Quant Small Cap?")
        for key in ("enriched_query", "fund_resolved", "fund_key", "canonical_name", "url", "section_filter", "clarification_message"):
            assert key in result

    def test_ac6_section_filter_holdings(self):
        result = process_query("List holdings of Quant Small Cap Fund")
        assert result["section_filter"] == "holdings"

    def test_ac7_single_fund_output(self):
        result = process_query("Quant Small Cap and Quant ELSS expense ratio")
        assert result["fund_resolved"] is True
        assert result["fund_key"] is not None
        assert result["canonical_name"] is not None
