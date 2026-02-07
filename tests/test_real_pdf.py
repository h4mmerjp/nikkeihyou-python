"""
Integration tests for parse_pdf using the real total_d.pdf file.

These tests are skipped when total_d.pdf is not present (e.g. in CI),
so other developers can still run the rest of the test suite.

v2.0: Updated for extract_table() based extraction.
Expected values may differ from v1.0 due to the change in extraction method.
"""
import io
import os

import pytest

PDF_PATH = os.path.join(os.path.dirname(__file__), "..", "total_d.pdf")
PDF_EXISTS = os.path.isfile(PDF_PATH)

skip_unless_pdf = pytest.mark.skipif(
    not PDF_EXISTS,
    reason="total_d.pdf not found; skipping real-PDF integration tests",
)


@pytest.fixture(scope="module")
def parsed_result():
    """Parse the real PDF once and share the result across all tests."""
    from api.parse_daily_report import parse_pdf

    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()
    return parse_pdf(io.BytesIO(pdf_bytes))


EXPECTED_KEYS = {
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


@skip_unless_pdf
class TestRealPdf:
    """Integration tests that verify parse_pdf against known values in total_d.pdf."""

    def test_date_extraction(self, parsed_result):
        assert parsed_result["date"] == "2025-05-31"

    def test_all_fields_present(self, parsed_result):
        assert set(parsed_result.keys()) == EXPECTED_KEYS

    def test_rows_not_empty(self, parsed_result):
        assert len(parsed_result["rows"]) > 0

    def test_total_count(self, parsed_result):
        """total_count should equal the number of parsed rows."""
        assert parsed_result["total_count"] == len(parsed_result["rows"])

    def test_all_numeric_fields_are_int(self, parsed_result):
        for key, value in parsed_result.items():
            if key == "date":
                assert isinstance(value, str)
            elif key == "rows":
                assert isinstance(value, list)
            else:
                assert isinstance(value, int), f"{key} should be int, got {type(value)}"

    def test_row_structure(self, parsed_result):
        """Each row should have the expected keys."""
        expected_row_keys = {
            'number', 'patient_no', 'name', 'insurance_type',
            'points', 'ratio', 'futan_amount',
            'kaigo_units', 'kaigo_amount',
            'jihi', 'buppan', 'previous_diff',
            'receipt_amount', 'diff',
        }
        for row in parsed_result["rows"]:
            assert set(row.keys()) == expected_row_keys
