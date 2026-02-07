"""
Comprehensive test suite for parse_pdf() in api/parse_daily_report.py.

v2.0: Tests rewritten for extract_table() based extraction.
All tests mock pdfplumber so no real PDF file is needed.
The conftest.py module handles mocking of environment variables and
external modules (notion_client, utils.notion_uploader) before import.
"""
import io
from datetime import datetime
from unittest.mock import MagicMock, patch

from parse_daily_report import parse_pdf, safe_int, parse_row, classify_insurance

# Import helper from conftest via tests package
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import make_table_row


# ============================================================
# Helper functions
# ============================================================

def make_mock_pdf(first_page_text, table_rows_per_page):
    """Create a mock object that simulates pdfplumber.open() as a context manager.

    Parameters
    ----------
    first_page_text : str or None
        Text returned by ``pdf.pages[0].extract_text()``.
    table_rows_per_page : list of (list of rows or None)
        Each element is a list of rows for that page's extract_table(),
        or None if extract_table() returns None for that page.

    Returns
    -------
    MagicMock
        A mock that behaves like the object returned by ``pdfplumber.open()``.
    """
    pages = []
    for i, table_rows in enumerate(table_rows_per_page):
        mock_page = MagicMock()
        # Only first page needs extract_text for date
        if i == 0:
            mock_page.extract_text.return_value = first_page_text
        else:
            mock_page.extract_text.return_value = ""
        mock_page.extract_table.return_value = table_rows
        pages.append(mock_page)

    # If no pages provided, create at least one
    if not pages:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = first_page_text
        mock_page.extract_table.return_value = None
        pages = [mock_page]

    mock_pdf = MagicMock()
    mock_pdf.pages = pages
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    return mock_pdf


# ============================================================
# safe_int() tests
# ============================================================

class TestSafeInt:
    """Tests for the safe_int() helper function."""

    def test_none(self):
        assert safe_int(None) == 0

    def test_empty_string(self):
        assert safe_int('') == 0

    def test_whitespace(self):
        assert safe_int('   ') == 0

    def test_plain_integer(self):
        assert safe_int('123') == 123

    def test_comma_separated(self):
        assert safe_int('1,234') == 1234

    def test_large_comma_separated(self):
        assert safe_int('1,234,567') == 1234567

    def test_negative(self):
        assert safe_int('-700') == -700

    def test_with_newline(self):
        assert safe_int('1,500\n') == 1500

    def test_with_spaces(self):
        assert safe_int(' 500 ') == 500

    def test_non_numeric(self):
        assert safe_int('abc') == 0

    def test_integer_input(self):
        assert safe_int(42) == 42

    def test_zero(self):
        assert safe_int('0') == 0


# ============================================================
# classify_insurance() tests
# ============================================================

class TestClassifyInsurance:
    """Tests for the classify_insurance() helper function."""

    def test_shaho_basic(self):
        assert classify_insurance('社本') == '社保'

    def test_shaho_family(self):
        assert classify_insurance('社家') == '社保'

    def test_shaho_with_modifier(self):
        assert classify_insurance('社家 乳無') == '社保'

    def test_shaho_child(self):
        assert classify_insurance('社家 子ども') == '社保'

    def test_kokuho_family(self):
        assert classify_insurance('国家') == '国保'

    def test_kokuho_main(self):
        assert classify_insurance('国本') == '国保'

    def test_kouki(self):
        assert classify_insurance('後期') == '後期'

    def test_kouki_with_modifier(self):
        assert classify_insurance('後期 難病') == '後期'

    def test_hoken_nashi(self):
        assert classify_insurance('保険なし') == '保険なし'

    def test_empty(self):
        assert classify_insurance('') == 'その他'

    def test_other(self):
        assert classify_insurance('その他') == 'その他'

    def test_disability_with_sha(self):
        """障がい者でも「社」を含むなら社保に分類"""
        assert classify_insurance('社本 障６００') == '社保'


# ============================================================
# parse_row() tests
# ============================================================

class TestParseRow:
    """Tests for the parse_row() helper function."""

    def test_basic_row(self):
        row = make_table_row(
            1, "No.10001\n山田太郎", "社本", 500, "30%\n1,500",
            receipt_amount=1500, diff=0,
        )
        result = parse_row(row)
        assert result['number'] == 1
        assert result['patient_no'] == '10001'
        assert result['name'] == '山田太郎'
        assert result['insurance_type'] == '社本'
        assert result['points'] == 500
        assert result['ratio'] == '30%'
        assert result['futan_amount'] == 1500
        assert result['receipt_amount'] == 1500
        assert result['diff'] == 0

    def test_row_with_modifiers(self):
        row = make_table_row(
            2, "No.10002\n鈴木花子\n再初診", "国家", 300, "30%\n900",
            receipt_amount=900, diff=0,
        )
        result = parse_row(row)
        assert result['name'] == '鈴木花子'
        assert result['patient_no'] == '10002'

    def test_row_with_jihi(self):
        row = make_table_row(
            3, "No.10003\n佐藤次郎", "社家 乳無", 200, "0%\n0",
            jihi=3000, receipt_amount=3000, diff=0,
        )
        result = parse_row(row)
        assert result['jihi'] == 3000
        assert result['futan_amount'] == 0

    def test_row_with_kaigo(self):
        row = make_table_row(
            4, "No.10004\n渡辺太郎", "後期 難病", 800, "10%\n800",
            kaigo_units=100, kaigo_amount=500, receipt_amount=1300, diff=0,
        )
        result = parse_row(row)
        assert result['kaigo_units'] == 100
        assert result['kaigo_amount'] == 500

    def test_row_with_buppan(self):
        row = make_table_row(
            5, "No.10005\n伊藤真", "保険なし", 0, "100%\n5,000",
            buppan=1560, receipt_amount=6560, diff=0,
        )
        result = parse_row(row)
        assert result['buppan'] == 1560

    def test_row_with_previous_diff(self):
        row = make_table_row(
            6, "No.10006\n三宅太郎", "", 0, "",
            previous_diff=-700, receipt_amount=-700, diff=0,
        )
        result = parse_row(row)
        assert result['previous_diff'] == -700

    def test_row_with_none_cells(self):
        """None cells should be handled gracefully."""
        row = make_table_row(
            7, "No.10007\n田中花子", "社本", 100, "30%\n300",
            receipt_amount=300, diff=0,
        )
        result = parse_row(row)
        assert result['kaigo_units'] == 0
        assert result['kaigo_amount'] == 0
        assert result['jihi'] == 0
        assert result['buppan'] == 0
        assert result['previous_diff'] == 0

    def test_futan_cell_without_newline(self):
        """負担額セルに改行がない場合"""
        row = ["1", "No.100\n名前", "社本", "100", "30%", None, None,
               None, None, None, "300", "0"]
        result = parse_row(row)
        assert result['ratio'] == '30%'
        assert result['futan_amount'] == 0


# ============================================================
# Date extraction tests
# ============================================================

class TestDateExtraction:
    """Tests for Reiwa date parsing on the first page."""

    @patch("parse_daily_report.pdfplumber")
    def test_standard_date(self, mock_pdfplumber):
        """令和7年1月15日 should convert to 2025-01-15."""
        mock_pdf = make_mock_pdf("令和7年1月15日", [None])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-01-15"

    @patch("parse_daily_report.pdfplumber")
    def test_date_with_spaces(self, mock_pdfplumber):
        """令和 7 年 1 月 15 日 (spaces between tokens) should still parse."""
        mock_pdf = make_mock_pdf("令和 7 年 1 月 15 日", [None])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-01-15"

    @patch("parse_daily_report.pdfplumber")
    def test_date_with_extra_spaces(self, mock_pdfplumber):
        """Multiple spaces between date components should be tolerated."""
        mock_pdf = make_mock_pdf("令和  7  年  1  月  15  日", [None])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-01-15"

    @patch("parse_daily_report.pdfplumber")
    def test_reiwa_1(self, mock_pdfplumber):
        """令和1年 is 2019."""
        mock_pdf = make_mock_pdf("令和1年4月1日", [None])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2019-04-01"

    @patch("parse_daily_report.pdfplumber")
    def test_reiwa_6_december(self, mock_pdfplumber):
        """令和6年12月31日 should convert to 2024-12-31."""
        mock_pdf = make_mock_pdf("令和6年12月31日", [None])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2024-12-31"

    @patch("parse_daily_report.pdfplumber")
    def test_date_embedded_in_text(self, mock_pdfplumber):
        """Date embedded in surrounding text should still be found."""
        first_text = "○○医院  日計表\n令和7年3月20日\n受付一覧"
        mock_pdf = make_mock_pdf(first_text, [None])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-03-20"

    @patch("parse_daily_report.pdfplumber")
    def test_missing_date_falls_back_to_today(self, mock_pdfplumber):
        """When no date pattern is found, use today's date."""
        mock_pdf = make_mock_pdf("このページには日付がありません", [None])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        expected = datetime.now().strftime("%Y-%m-%d")
        assert result["date"] == expected

    @patch("parse_daily_report.pdfplumber")
    def test_empty_first_page_falls_back_to_today(self, mock_pdfplumber):
        """None from extract_text() should not crash; falls back to today."""
        mock_pdf = make_mock_pdf(None, [None])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        expected = datetime.now().strftime("%Y-%m-%d")
        assert result["date"] == expected

    @patch("parse_daily_report.pdfplumber")
    def test_month_and_day_zero_padded(self, mock_pdfplumber):
        """Single-digit month and day should be zero-padded in output."""
        mock_pdf = make_mock_pdf("令和7年2月5日", [None])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-02-05"


# ============================================================
# Insurance classification & aggregation tests
# ============================================================

class TestInsuranceAggregation:
    """Tests for insurance category aggregation from table rows."""

    @patch("parse_daily_report.pdfplumber")
    def test_shaho_aggregation(self, mock_pdfplumber):
        """社保 patients should be counted and amounts summed."""
        rows = [
            make_table_row(1, "No.1\n山田", "社本", 500, "30%\n1,500",
                           receipt_amount=1500, diff=0),
            make_table_row(2, "No.2\n鈴木", "社家", 300, "30%\n900",
                           receipt_amount=900, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["shaho_count"] == 2
        assert result["shaho_amount"] == 2400  # 1500 + 900
        assert result["shaho_points"] == 800   # 500 + 300

    @patch("parse_daily_report.pdfplumber")
    def test_kokuho_aggregation(self, mock_pdfplumber):
        """国保 patients should be counted correctly."""
        rows = [
            make_table_row(1, "No.1\n田中", "国家", 400, "30%\n1,200",
                           receipt_amount=1200, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["kokuho_count"] == 1
        assert result["kokuho_amount"] == 1200
        assert result["kokuho_points"] == 400

    @patch("parse_daily_report.pdfplumber")
    def test_kouki_aggregation(self, mock_pdfplumber):
        """後期 patients should be counted correctly."""
        rows = [
            make_table_row(1, "No.1\n高橋", "後期", 600, "10%\n600",
                           receipt_amount=600, diff=0),
            make_table_row(2, "No.2\n渡辺", "後期 難病", 800, "10%\n800",
                           receipt_amount=800, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["kouki_count"] == 2
        assert result["kouki_amount"] == 1400  # 600 + 800
        assert result["kouki_points"] == 1400  # 600 + 800

    @patch("parse_daily_report.pdfplumber")
    def test_hoken_nashi_aggregation(self, mock_pdfplumber):
        """保険なし patients should be counted correctly."""
        rows = [
            make_table_row(1, "No.1\n伊藤", "保険なし", 0, "100%\n5,000",
                           receipt_amount=5000, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["hoken_nashi_count"] == 1
        assert result["hoken_nashi_amount"] == 5000

    @patch("parse_daily_report.pdfplumber")
    def test_sonota_excluded_from_insurance(self, mock_pdfplumber):
        """Rows with empty insurance type should be classified as その他 and excluded."""
        rows = [
            make_table_row(1, "No.1\n山田", "社本", 500, "30%\n1,500",
                           receipt_amount=1500, diff=0),
            make_table_row(2, "No.2\n三宅", "", 0, "",
                           previous_diff=-700, receipt_amount=-700, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["shaho_count"] == 1
        assert result["insurance_total_count"] == 1
        assert result["total_count"] == 2  # includes その他 row

    @patch("parse_daily_report.pdfplumber")
    def test_multiple_categories(self, mock_pdfplumber):
        """All four insurance categories present together."""
        rows = [
            make_table_row(1, "No.1\nA", "社本", 500, "30%\n1,500",
                           receipt_amount=1500, diff=0),
            make_table_row(2, "No.2\nB", "国家", 400, "30%\n1,200",
                           receipt_amount=1200, diff=0),
            make_table_row(3, "No.3\nC", "後期", 600, "10%\n600",
                           receipt_amount=600, diff=0),
            make_table_row(4, "No.4\nD", "保険なし", 0, "100%\n5,000",
                           receipt_amount=5000, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["shaho_count"] == 1
        assert result["kokuho_count"] == 1
        assert result["kouki_count"] == 1
        assert result["hoken_nashi_count"] == 1
        assert result["total_count"] == 4
        assert result["insurance_total_count"] == 4


# ============================================================
# Jihi / buppan / kaigo / previous_diff aggregation tests
# ============================================================

class TestSpecialFieldAggregation:
    """Tests for jihi, buppan, kaigo, and previous_diff aggregation."""

    @patch("parse_daily_report.pdfplumber")
    def test_jihi_aggregation(self, mock_pdfplumber):
        """自費 amounts should be summed from individual rows."""
        rows = [
            make_table_row(1, "No.1\nA", "社本", 500, "30%\n1,500",
                           jihi=3000, receipt_amount=4500, diff=0),
            make_table_row(2, "No.2\nB", "社家", 300, "30%\n900",
                           jihi=2000, receipt_amount=2900, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["jihi_amount"] == 5000  # 3000 + 2000

    @patch("parse_daily_report.pdfplumber")
    def test_buppan_aggregation(self, mock_pdfplumber):
        """物販 amounts should be summed from individual rows."""
        rows = [
            make_table_row(1, "No.1\nA", "保険なし", 0, "100%\n5,000",
                           buppan=1560, receipt_amount=6560, diff=0),
            make_table_row(2, "No.2\nB", "保険なし", 0, "100%\n3,000",
                           buppan=500, receipt_amount=3500, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["buppan_amount"] == 2060  # 1560 + 500

    @patch("parse_daily_report.pdfplumber")
    def test_kaigo_aggregation(self, mock_pdfplumber):
        """介護 amounts should be summed from individual rows."""
        rows = [
            make_table_row(1, "No.1\nA", "後期", 600, "10%\n600",
                           kaigo_units=100, kaigo_amount=500,
                           receipt_amount=1100, diff=0),
            make_table_row(2, "No.2\nB", "後期 難病", 800, "10%\n800",
                           kaigo_units=200, kaigo_amount=1000,
                           receipt_amount=1800, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["kaigo_amount"] == 1500  # 500 + 1000

    @patch("parse_daily_report.pdfplumber")
    def test_previous_diff_aggregation(self, mock_pdfplumber):
        """前回差額 should be summed (can be negative)."""
        rows = [
            make_table_row(1, "No.1\nA", "", 0, "",
                           previous_diff=-700, receipt_amount=-700, diff=0),
            make_table_row(2, "No.2\nB", "", 0, "",
                           previous_diff=300, receipt_amount=300, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["previous_diff"] == -400  # -700 + 300

    @patch("parse_daily_report.pdfplumber")
    def test_no_special_fields(self, mock_pdfplumber):
        """When no jihi/buppan/kaigo/previous_diff, all should be 0."""
        rows = [
            make_table_row(1, "No.1\nA", "社本", 500, "30%\n1,500",
                           receipt_amount=1500, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["jihi_amount"] == 0
        assert result["buppan_amount"] == 0
        assert result["kaigo_amount"] == 0
        assert result["previous_diff"] == 0

    @patch("parse_daily_report.pdfplumber")
    def test_total_receipt(self, mock_pdfplumber):
        """total_receipt should sum all receipt_amount values."""
        rows = [
            make_table_row(1, "No.1\nA", "社本", 500, "30%\n1,500",
                           receipt_amount=1500, diff=0),
            make_table_row(2, "No.2\nB", "国家", 400, "30%\n1,200",
                           receipt_amount=1200, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["total_receipt"] == 2700  # 1500 + 1200


# ============================================================
# Empty data / no table tests
# ============================================================

class TestEmptyData:
    """Tests that confirm default zeros when no data matches."""

    @patch("parse_daily_report.pdfplumber")
    def test_no_table(self, mock_pdfplumber):
        """No table on any page: all values should be 0."""
        mock_pdf = make_mock_pdf("令和7年1月1日", [None])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["date"] == "2025-01-01"
        assert result["shaho_count"] == 0
        assert result["shaho_amount"] == 0
        assert result["kokuho_count"] == 0
        assert result["kokuho_amount"] == 0
        assert result["kouki_count"] == 0
        assert result["kouki_amount"] == 0
        assert result["hoken_nashi_count"] == 0
        assert result["hoken_nashi_amount"] == 0
        assert result["total_count"] == 0
        assert result["total_amount"] == 0
        assert result["jihi_amount"] == 0
        assert result["buppan_amount"] == 0
        assert result["kaigo_amount"] == 0
        assert result["previous_diff"] == 0
        assert result["rows"] == []

    @patch("parse_daily_report.pdfplumber")
    def test_table_with_only_header(self, mock_pdfplumber):
        """Table with only header row: all values should be 0."""
        header_only = [
            ["番号", "氏名", "保険種別", "点数", "負担額", "介護単位",
             "介護負担額", "自費", "物販", "前回差額", "領収額", "差額"],
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [header_only])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["total_count"] == 0
        assert result["rows"] == []

    @patch("parse_daily_report.pdfplumber")
    def test_table_with_total_row_only(self, mock_pdfplumber):
        """Table with only a total row (non-digit first column): empty."""
        total_only = [
            ["合計", "", "", "0", "", "0", "0", "0", "0", "0", "0", "0"],
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [total_only])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["total_count"] == 0


# ============================================================
# Multi-page tests
# ============================================================

class TestMultiPage:
    """Tests for PDFs with multiple pages of table data."""

    @patch("parse_daily_report.pdfplumber")
    def test_two_pages(self, mock_pdfplumber):
        """Rows from multiple pages should be combined."""
        page1_rows = [
            make_table_row(1, "No.1\nA", "社本", 500, "30%\n1,500",
                           receipt_amount=1500, diff=0),
        ]
        page2_rows = [
            make_table_row(2, "No.2\nB", "国家", 400, "30%\n1,200",
                           receipt_amount=1200, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [page1_rows, page2_rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["total_count"] == 2
        assert result["shaho_count"] == 1
        assert result["kokuho_count"] == 1

    @patch("parse_daily_report.pdfplumber")
    def test_page_with_no_table(self, mock_pdfplumber):
        """Pages without tables should be skipped gracefully."""
        page1_rows = [
            make_table_row(1, "No.1\nA", "社本", 500, "30%\n1,500",
                           receipt_amount=1500, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [page1_rows, None])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert result["total_count"] == 1


# ============================================================
# Return structure tests
# ============================================================

class TestReturnStructure:
    """Tests that verify the returned dict has all expected keys."""

    @patch("parse_daily_report.pdfplumber")
    def test_all_keys_present(self, mock_pdfplumber):
        """parse_pdf must return all expected keys."""
        mock_pdf = make_mock_pdf("令和7年1月1日", [None])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))

        expected_keys = {
            "date", "rows",
            "shaho_count", "shaho_points", "shaho_amount",
            "kokuho_count", "kokuho_points", "kokuho_amount",
            "kouki_count", "kouki_points", "kouki_amount",
            "hoken_nashi_count", "hoken_nashi_points", "hoken_nashi_amount",
            "total_count", "insurance_total_count",
            "total_amount", "total_receipt",
            "jihi_amount", "buppan_amount",
            "kaigo_amount", "previous_diff",
        }
        assert set(result.keys()) == expected_keys

    @patch("parse_daily_report.pdfplumber")
    def test_numeric_types(self, mock_pdfplumber):
        """All non-date, non-rows values should be int."""
        rows = [
            make_table_row(1, "No.1\nA", "社本", 500, "30%\n1,500",
                           jihi=1000, buppan=500, previous_diff=-300,
                           receipt_amount=3000, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))

        for key, value in result.items():
            if key == "date":
                assert isinstance(value, str)
            elif key == "rows":
                assert isinstance(value, list)
            else:
                assert isinstance(value, int), f"{key} should be int, got {type(value)}"

    @patch("parse_daily_report.pdfplumber")
    def test_rows_structure(self, mock_pdfplumber):
        """Each row in 'rows' should be a dict with expected keys."""
        rows = [
            make_table_row(1, "No.1\nA", "社本", 500, "30%\n1,500",
                           receipt_amount=1500, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年1月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))
        assert len(result["rows"]) == 1

        row = result["rows"][0]
        expected_row_keys = {
            'number', 'patient_no', 'name', 'insurance_type',
            'points', 'ratio', 'futan_amount',
            'kaigo_units', 'kaigo_amount',
            'jihi', 'buppan', 'previous_diff',
            'receipt_amount', 'diff',
        }
        assert set(row.keys()) == expected_row_keys


# ============================================================
# Full realistic scenario tests
# ============================================================

class TestFullRealisticScenario:
    """End-to-end test with realistic table data."""

    @patch("parse_daily_report.pdfplumber")
    def test_full_realistic_pdf(self, mock_pdfplumber, realistic_table_rows,
                                realistic_first_page_text):
        """Parse a realistic PDF with all categories populated."""
        mock_pdf = make_mock_pdf(realistic_first_page_text, [realistic_table_rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))

        # Date
        assert result["date"] == "2025-01-15"

        # 社保: rows 1,2,3 (社本, 社家, 社家 乳無)
        assert result["shaho_count"] == 3
        assert result["shaho_points"] == 1000  # 500+300+200
        assert result["shaho_amount"] == 2400  # 1500+900+0

        # 国保: row 4
        assert result["kokuho_count"] == 1
        assert result["kokuho_points"] == 400
        assert result["kokuho_amount"] == 1200

        # 後期: rows 5,6
        assert result["kouki_count"] == 2
        assert result["kouki_points"] == 1400  # 600+800
        assert result["kouki_amount"] == 1400  # 600+800

        # 保険なし: row 7
        assert result["hoken_nashi_count"] == 1
        assert result["hoken_nashi_amount"] == 5000

        # Total (all 8 rows including その他)
        assert result["total_count"] == 8
        assert result["insurance_total_count"] == 7  # excluding その他

        # Jihi from row 3
        assert result["jihi_amount"] == 3000

        # Buppan from row 7
        assert result["buppan_amount"] == 1560

        # Kaigo from row 6
        assert result["kaigo_amount"] == 500

        # Previous diff from row 8
        assert result["previous_diff"] == -700

    @patch("parse_daily_report.pdfplumber")
    def test_partial_data(self, mock_pdfplumber):
        """Some categories present, others absent: absent ones stay 0."""
        rows = [
            make_table_row(1, "No.1\nA", "社本", 500, "30%\n1,500",
                           receipt_amount=1500, diff=0),
            make_table_row(2, "No.2\nB", "社家", 300, "30%\n900",
                           receipt_amount=900, diff=0),
        ]
        mock_pdf = make_mock_pdf("令和7年5月1日", [rows])
        mock_pdfplumber.open.return_value = mock_pdf

        result = parse_pdf(io.BytesIO(b"fake"))

        assert result["date"] == "2025-05-01"
        assert result["shaho_count"] == 2
        assert result["shaho_amount"] == 2400
        assert result["kokuho_count"] == 0
        assert result["kokuho_amount"] == 0
        assert result["kouki_count"] == 0
        assert result["kouki_amount"] == 0
        assert result["hoken_nashi_count"] == 0
        assert result["hoken_nashi_amount"] == 0
        assert result["jihi_amount"] == 0
        assert result["buppan_amount"] == 0
        assert result["kaigo_amount"] == 0
        assert result["previous_diff"] == 0
