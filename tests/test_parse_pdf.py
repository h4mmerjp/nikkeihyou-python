"""
Comprehensive test suite for parse_pdf() in api/parse_daily_report.py.

All tests mock pdfplumber so no real PDF file is needed.
The conftest.py module handles mocking of environment variables and
external modules (notion_client, utils.notion_uploader) before import.
"""
import io
from datetime import datetime
from unittest.mock import MagicMock, patch

from parse_daily_report import parse_pdf


# ============================================================
# Helper functions
# ============================================================

def make_mock_pdf(first_page_text, last_page_text):
    """Create a mock object that simulates pdfplumber.open() as a context manager.

    Parameters
    ----------
    first_page_text : str or None
        Text returned by ``pdf.pages[0].extract_text()``.
    last_page_text : str or None
        Text returned by ``pdf.pages[-1].extract_text()``.

    Returns
    -------
    MagicMock
        A mock that behaves like the object returned by ``pdfplumber.open()``.
    """
    mock_first_page = MagicMock()
    mock_first_page.extract_text.return_value = first_page_text

    mock_last_page = MagicMock()
    mock_last_page.extract_text.return_value = last_page_text

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_first_page, mock_last_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    return mock_pdf


def make_single_page_mock_pdf(page_text):
    """Create a mock PDF with a single page (pages[0] is also pages[-1])."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = page_text

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    return mock_pdf


# ============================================================
# Date extraction tests
# ============================================================

class TestDateExtraction:
    """Tests for Reiwa date parsing on the first page."""

    @patch("parse_daily_report.pdfplumber")
    def test_standard_date(self, mock_pdfplumber):
        """令和7年1月15日 should convert to 2025-01-15."""
        mock_pdf = make_mock_pdf("令和7年1月15日", "")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-01-15"

    @patch("parse_daily_report.pdfplumber")
    def test_date_with_spaces(self, mock_pdfplumber):
        """令和 7 年 1 月 15 日 (spaces between tokens) should still parse."""
        mock_pdf = make_mock_pdf("令和 7 年 1 月 15 日", "")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-01-15"

    @patch("parse_daily_report.pdfplumber")
    def test_date_with_extra_spaces(self, mock_pdfplumber):
        """Multiple spaces between date components should be tolerated."""
        mock_pdf = make_mock_pdf("令和  7  年  1  月  15  日", "")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-01-15"

    @patch("parse_daily_report.pdfplumber")
    def test_reiwa_1(self, mock_pdfplumber):
        """令和1年 is 2019."""
        mock_pdf = make_mock_pdf("令和1年4月1日", "")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2019-04-01"

    @patch("parse_daily_report.pdfplumber")
    def test_reiwa_6_december(self, mock_pdfplumber):
        """令和6年12月31日 should convert to 2024-12-31."""
        mock_pdf = make_mock_pdf("令和6年12月31日", "")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2024-12-31"

    @patch("parse_daily_report.pdfplumber")
    def test_date_embedded_in_text(self, mock_pdfplumber):
        """Date embedded in surrounding text should still be found."""
        first_text = "○○医院  日計表\n令和7年3月20日\n受付一覧"
        mock_pdf = make_mock_pdf(first_text, "")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-03-20"

    @patch("parse_daily_report.pdfplumber")
    def test_missing_date_falls_back_to_today(self, mock_pdfplumber):
        """When no date pattern is found, use today's date."""
        mock_pdf = make_mock_pdf("このページには日付がありません", "")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        expected = datetime.now().strftime("%Y-%m-%d")
        assert result["date"] == expected

    @patch("parse_daily_report.pdfplumber")
    def test_empty_first_page_falls_back_to_today(self, mock_pdfplumber):
        """None from extract_text() should not crash; falls back to today."""
        mock_pdf = make_mock_pdf(None, "")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        expected = datetime.now().strftime("%Y-%m-%d")
        assert result["date"] == expected

    @patch("parse_daily_report.pdfplumber")
    def test_month_and_day_zero_padded(self, mock_pdfplumber):
        """Single-digit month and day should be zero-padded in output."""
        mock_pdf = make_mock_pdf("令和7年2月5日", "")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-02-05"


# ============================================================
# Insurance category extraction tests
# ============================================================

class TestInsuranceCategoryExtraction:
    """Tests for the four insurance type patterns on the last page."""

    @patch("parse_daily_report.pdfplumber")
    def test_shaho_extraction(self, mock_pdfplumber):
        """社保 (employer insurance) count and amount."""
        last_text = "社保 10 50,000 30,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["shaho_count"] == 10
        assert result["shaho_amount"] == 30000

    @patch("parse_daily_report.pdfplumber")
    def test_kokuho_extraction(self, mock_pdfplumber):
        """国保 (national insurance) count and amount."""
        last_text = "国保 5 25,000 15,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["kokuho_count"] == 5
        assert result["kokuho_amount"] == 15000

    @patch("parse_daily_report.pdfplumber")
    def test_kouki_extraction(self, mock_pdfplumber):
        """後期 (late-stage elderly) count and amount."""
        last_text = "後期 8 40,000 24,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["kouki_count"] == 8
        assert result["kouki_amount"] == 24000

    @patch("parse_daily_report.pdfplumber")
    def test_hoken_nashi_extraction(self, mock_pdfplumber):
        """保険なし (no insurance) count and amount."""
        last_text = "保険なし 3 10,000 6,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["hoken_nashi_count"] == 3
        assert result["hoken_nashi_amount"] == 6000

    @patch("parse_daily_report.pdfplumber")
    def test_amounts_with_commas(self, mock_pdfplumber):
        """Amounts with comma separators (e.g. 1,234,567) should parse correctly."""
        last_text = "社保 100 5,000,000 1,234,567"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["shaho_count"] == 100
        assert result["shaho_amount"] == 1234567

    @patch("parse_daily_report.pdfplumber")
    def test_multiple_categories_in_same_text(self, mock_pdfplumber):
        """All four insurance categories present together."""
        last_text = (
            "社保 10 50,000 30,000\n"
            "国保 5 25,000 15,000\n"
            "後期 8 40,000 24,000\n"
            "保険なし 3 10,000 6,000\n"
        )
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["shaho_count"] == 10
        assert result["shaho_amount"] == 30000
        assert result["kokuho_count"] == 5
        assert result["kokuho_amount"] == 15000
        assert result["kouki_count"] == 8
        assert result["kouki_amount"] == 24000
        assert result["hoken_nashi_count"] == 3
        assert result["hoken_nashi_amount"] == 6000

    @patch("parse_daily_report.pdfplumber")
    def test_extra_whitespace_in_insurance_line(self, mock_pdfplumber):
        """Extra whitespace between columns should still match (\\s+)."""
        last_text = "社保   10   50,000   30,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["shaho_count"] == 10
        assert result["shaho_amount"] == 30000


# ============================================================
# Total (合計) extraction tests
# ============================================================

class TestTotalExtraction:
    """Tests for the 合計 (total) line."""

    @patch("parse_daily_report.pdfplumber")
    def test_total_extraction(self, mock_pdfplumber):
        """合計 line with count, intermediate value, and amount."""
        last_text = "合計 26 125,000 75,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["total_count"] == 26
        assert result["total_amount"] == 75000

    @patch("parse_daily_report.pdfplumber")
    def test_total_large_numbers(self, mock_pdfplumber):
        """合計 with large comma-separated amounts."""
        last_text = "合計 150 2,500,000 1,500,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["total_count"] == 150
        assert result["total_amount"] == 1500000

    @patch("parse_daily_report.pdfplumber")
    def test_total_missing(self, mock_pdfplumber):
        """When 合計 is missing, total_count and total_amount stay 0."""
        mock_pdf = make_mock_pdf("令和7年1月1日", "no totals here")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["total_count"] == 0
        assert result["total_amount"] == 0


# ============================================================
# Self-pay (自費) extraction tests
# ============================================================

class TestJihiExtraction:
    """Tests for the 自費 (self-pay) line."""

    @patch("parse_daily_report.pdfplumber")
    def test_jihi_extraction(self, mock_pdfplumber):
        """自費 followed by an amount."""
        last_text = "自費 50,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["jihi_amount"] == 50000

    @patch("parse_daily_report.pdfplumber")
    def test_jihi_no_comma(self, mock_pdfplumber):
        """自費 amount without comma separator."""
        last_text = "自費 8000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["jihi_amount"] == 8000

    @patch("parse_daily_report.pdfplumber")
    def test_jihi_missing(self, mock_pdfplumber):
        """When 自費 is absent, jihi_amount stays 0."""
        mock_pdf = make_mock_pdf("令和7年1月1日", "nothing here")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["jihi_amount"] == 0


# ============================================================
# Merchandise (物販合計) extraction tests
# ============================================================

class TestBushanExtraction:
    """Tests for the 物販合計 (merchandise total) line."""

    @patch("parse_daily_report.pdfplumber")
    def test_bushan_extraction(self, mock_pdfplumber):
        """物販合計 followed by an amount with commas."""
        last_text = "物販合計 12,500"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["bushan_amount"] == 12500

    @patch("parse_daily_report.pdfplumber")
    def test_bushan_no_comma(self, mock_pdfplumber):
        """物販合計 amount without comma."""
        last_text = "物販合計 500"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["bushan_amount"] == 500

    @patch("parse_daily_report.pdfplumber")
    def test_bushan_missing(self, mock_pdfplumber):
        """When 物販合計 is absent, bushan_amount stays 0."""
        mock_pdf = make_mock_pdf("令和7年1月1日", "nothing")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["bushan_amount"] == 0


# ============================================================
# Nursing care (介護) extraction tests
# ============================================================

class TestKaigoExtraction:
    """Tests for the 介護 (nursing care) line."""

    @patch("parse_daily_report.pdfplumber")
    def test_kaigo_extraction(self, mock_pdfplumber):
        """介護 followed by arbitrary text then an amount."""
        last_text = "介護保険 請求額 30,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["kaigo_amount"] == 30000

    @patch("parse_daily_report.pdfplumber")
    def test_kaigo_simple(self, mock_pdfplumber):
        """介護 directly followed by amount (non-greedy .*?)."""
        last_text = "介護 5,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["kaigo_amount"] == 5000

    @patch("parse_daily_report.pdfplumber")
    def test_kaigo_missing(self, mock_pdfplumber):
        """When 介護 is absent, kaigo_amount stays 0."""
        mock_pdf = make_mock_pdf("令和7年1月1日", "nothing")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["kaigo_amount"] == 0


# ============================================================
# All-zeros / empty data tests
# ============================================================

class TestAllZeros:
    """Tests that confirm default zeros when no data matches."""

    @patch("parse_daily_report.pdfplumber")
    def test_empty_last_page(self, mock_pdfplumber):
        """Empty last page text: all counts and amounts should be 0."""
        mock_pdf = make_mock_pdf("令和7年1月1日", "")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-01-01"
        assert result["shaho_count"] == 0
        assert result["shaho_amount"] == 0
        assert result["kokuho_count"] == 0
        assert result["kokuho_amount"] == 0
        assert result["kouki_count"] == 0
        assert result["kouki_amount"] == 0
        assert result["jihi_count"] == 0
        assert result["jihi_amount"] == 0
        assert result["hoken_nashi_count"] == 0
        assert result["hoken_nashi_amount"] == 0
        assert result["total_count"] == 0
        assert result["total_amount"] == 0
        assert result["bushan_amount"] == 0
        assert result["kaigo_amount"] == 0
        assert result["zenkai_sagaku"] == 0

    @patch("parse_daily_report.pdfplumber")
    def test_none_last_page(self, mock_pdfplumber):
        """None from extract_text() on last page: all values should be 0."""
        mock_pdf = make_mock_pdf("令和7年1月1日", None)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["shaho_count"] == 0
        assert result["total_amount"] == 0
        assert result["jihi_amount"] == 0
        assert result["bushan_amount"] == 0
        assert result["kaigo_amount"] == 0
        assert result["zenkai_sagaku"] == 0

    @patch("parse_daily_report.pdfplumber")
    def test_unrelated_text(self, mock_pdfplumber):
        """Completely unrelated text: all values should be 0."""
        mock_pdf = make_mock_pdf("令和7年1月1日", "本日は晴天なり。特に報告なし。")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["shaho_count"] == 0
        assert result["shaho_amount"] == 0
        assert result["kokuho_count"] == 0
        assert result["kokuho_amount"] == 0
        assert result["total_count"] == 0
        assert result["total_amount"] == 0
        assert result["jihi_amount"] == 0
        assert result["bushan_amount"] == 0
        assert result["kaigo_amount"] == 0
        assert result["zenkai_sagaku"] == 0


# ============================================================
# Return structure tests
# ============================================================

class TestReturnStructure:
    """Tests that verify the returned dict has all expected keys."""

    @patch("parse_daily_report.pdfplumber")
    def test_all_keys_present(self, mock_pdfplumber):
        """parse_pdf must return all 16 expected keys."""
        mock_pdf = make_mock_pdf("令和7年1月1日", "")
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))

        expected_keys = {
            "date",
            "shaho_count", "shaho_amount",
            "kokuho_count", "kokuho_amount",
            "kouki_count", "kouki_amount",
            "jihi_count", "jihi_amount",
            "hoken_nashi_count", "hoken_nashi_amount",
            "total_count", "total_amount",
            "bushan_amount",
            "kaigo_amount",
            "zenkai_sagaku",
        }
        assert set(result.keys()) == expected_keys

    @patch("parse_daily_report.pdfplumber")
    def test_numeric_types(self, mock_pdfplumber):
        """All non-date values should be int, including zenkai_sagaku."""
        last_text = "社保 10 50,000 30,000\n合計 10 50,000 30,000 0 0 5,000 1,000 -300 35,700 0\n物販合計 1,000\n介護 2,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))

        for key, value in result.items():
            if key == "date":
                assert isinstance(value, str)
            else:
                assert isinstance(value, int), f"{key} should be int, got {type(value)}"


# ============================================================
# Single-page PDF tests
# ============================================================

class TestSinglePagePdf:
    """Tests for PDFs that have only one page (pages[0] == pages[-1])."""

    @patch("parse_daily_report.pdfplumber")
    def test_single_page_with_date_and_data(self, mock_pdfplumber):
        """A single page acts as both first and last page."""
        page_text = (
            "令和7年6月10日\n"
            "社保 5 20,000 10,000\n"
            "合計 5 20,000 10,000\n"
            "自費 3,000\n"
        )
        mock_pdf = make_single_page_mock_pdf(page_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-06-10"
        assert result["shaho_count"] == 5
        assert result["shaho_amount"] == 10000
        assert result["total_count"] == 5
        assert result["total_amount"] == 10000
        assert result["jihi_amount"] == 3000


# ============================================================
# Full realistic scenario tests
# ============================================================

class TestFullRealisticScenario:
    """End-to-end test with realistic PDF text content."""

    @patch("parse_daily_report.pdfplumber")
    def test_full_realistic_pdf(self, mock_pdfplumber, realistic_first_page, realistic_last_page):
        """Parse a realistic two-page PDF with all categories populated."""
        mock_pdf = make_mock_pdf(realistic_first_page, realistic_last_page)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))

        # Date
        assert result["date"] == "2025-01-15"

        # Insurance categories
        assert result["shaho_count"] == 25
        assert result["shaho_amount"] == 360000
        assert result["kokuho_count"] == 10
        assert result["kokuho_amount"] == 135000
        assert result["kouki_count"] == 15
        assert result["kouki_amount"] == 240000
        assert result["hoken_nashi_count"] == 3
        assert result["hoken_nashi_amount"] == 15000

        # Total
        assert result["total_count"] == 53
        assert result["total_amount"] == 750000

        # Self-pay (extracted from overall 合計 row)
        assert result["jihi_amount"] == 50000

        # Zenkai sagaku (前回差額 from overall 合計 row)
        assert result["zenkai_sagaku"] == -500

        # Merchandise
        assert result["bushan_amount"] == 12500

        # Nursing care
        assert result["kaigo_amount"] == 30000

    @patch("parse_daily_report.pdfplumber")
    def test_partial_data(self, mock_pdfplumber):
        """Some categories present, others absent: absent ones stay 0."""
        last_text = (
            "社保 20 100,000 60,000\n"
            "合計 20 100,000 60,000\n"
            "自費 10,000\n"
        )
        mock_pdf = make_mock_pdf("令和7年5月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))

        assert result["date"] == "2025-05-01"
        assert result["shaho_count"] == 20
        assert result["shaho_amount"] == 60000
        assert result["kokuho_count"] == 0
        assert result["kokuho_amount"] == 0
        assert result["kouki_count"] == 0
        assert result["kouki_amount"] == 0
        assert result["hoken_nashi_count"] == 0
        assert result["hoken_nashi_amount"] == 0
        assert result["total_count"] == 20
        assert result["total_amount"] == 60000
        assert result["jihi_amount"] == 10000
        assert result["bushan_amount"] == 0
        assert result["kaigo_amount"] == 0

    @patch("parse_daily_report.pdfplumber")
    def test_jihi_count_always_zero(self, mock_pdfplumber):
        """jihi_count is always 0 because parse_pdf never sets it from regex."""
        last_text = "自費 99,999"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["jihi_count"] == 0
        assert result["jihi_amount"] == 99999


# ============================================================
# Overall total row extraction tests (自費・前回差額)
# ============================================================

class TestOverallTotalExtraction:
    """Tests for jihi and zenkai_sagaku extraction from the overall 合計 row."""

    @patch("parse_daily_report.pdfplumber")
    def test_jihi_from_overall_total(self, mock_pdfplumber):
        """jihi_amount should be extracted from the 6th column of the full 合計 row."""
        last_text = "合計 30 30,000 50,000 0 0 5,000 2,000 -500 56,500 0"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["jihi_amount"] == 5000

    @patch("parse_daily_report.pdfplumber")
    def test_zenkai_sagaku_positive(self, mock_pdfplumber):
        """zenkai_sagaku should handle positive values."""
        last_text = "合計 30 30,000 50,000 0 0 5,000 2,000 300 56,500 0"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["zenkai_sagaku"] == 300

    @patch("parse_daily_report.pdfplumber")
    def test_zenkai_sagaku_negative(self, mock_pdfplumber):
        """zenkai_sagaku should handle negative values (e.g. -700)."""
        last_text = "合計 30 30,000 50,000 0 0 5,000 2,000 -700 56,500 0"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["zenkai_sagaku"] == -700

    @patch("parse_daily_report.pdfplumber")
    def test_zenkai_sagaku_zero(self, mock_pdfplumber):
        """zenkai_sagaku should be 0 when the column value is 0."""
        last_text = "合計 30 30,000 50,000 0 0 5,000 2,000 0 56,500 0"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["zenkai_sagaku"] == 0

    @patch("parse_daily_report.pdfplumber")
    def test_fallback_jihi_regex(self, mock_pdfplumber):
        """When the full 合計 row doesn't match, fallback '自費 金額' regex should work."""
        last_text = "合計 30 30,000 50,000\n自費 8,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["jihi_amount"] == 8000
        assert result["zenkai_sagaku"] == 0

    @patch("parse_daily_report.pdfplumber")
    def test_no_overall_total_row(self, mock_pdfplumber):
        """When no 合計 row and no 自費 text, both jihi_amount and zenkai_sagaku stay 0."""
        last_text = "社保 10 50,000 30,000"
        mock_pdf = make_mock_pdf("令和7年1月1日", last_text)
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["jihi_amount"] == 0
        assert result["zenkai_sagaku"] == 0
