"""
Integration tests for parse_pdf using the real total_d.pdf file.

These tests are skipped when total_d.pdf is not present (e.g. in CI),
so other developers can still run the rest of the test suite.
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


EXPECTED_SUMMARY_KEYS = {
    "date",
    "shaho_count",
    "shaho_amount",
    "kokuho_count",
    "kokuho_amount",
    "kouki_count",
    "kouki_amount",
    "jihi_count",
    "jihi_amount",
    "hoken_nashi_count",
    "hoken_nashi_amount",
    "total_count",
    "total_amount",
    "bushan_amount",
    "kaigo_amount",
    "zenkai_sagaku",
}

EXPECTED_PATIENT_KEYS = {
    "number",
    "patient_id",
    "name",
    "insurance_type",
    "points",
    "burden_amount",
    "kaigo_units",
    "kaigo_burden",
    "jihi",
    "bushan",
    "zenkai_sagaku",
    "receipt_amount",
    "sagaku",
    "remarks",
}


@skip_unless_pdf
class TestRealPdf:
    """Integration tests that verify parse_pdf against known values in total_d.pdf."""

    def test_result_structure(self, parsed_result):
        """Verify the result has both summary and patients keys."""
        assert "summary" in parsed_result
        assert "patients" in parsed_result
        assert isinstance(parsed_result["patients"], list)

    def test_date_extraction(self, parsed_result):
        assert parsed_result["summary"]["date"] == "2025-05-31"

    def test_shaho(self, parsed_result):
        assert parsed_result["summary"]["shaho_count"] == 42
        assert parsed_result["summary"]["shaho_amount"] == 130500

    def test_kokuho(self, parsed_result):
        assert parsed_result["summary"]["kokuho_count"] == 4
        assert parsed_result["summary"]["kokuho_amount"] == 6050

    def test_kouki(self, parsed_result):
        assert parsed_result["summary"]["kouki_count"] == 5
        assert parsed_result["summary"]["kouki_amount"] == 3390

    def test_hoken_nashi(self, parsed_result):
        assert parsed_result["summary"]["hoken_nashi_count"] == 1
        assert parsed_result["summary"]["hoken_nashi_amount"] == 10060

    def test_total(self, parsed_result):
        assert parsed_result["summary"]["total_count"] == 55
        assert parsed_result["summary"]["total_amount"] == 150000

    def test_jihi(self, parsed_result):
        assert parsed_result["summary"]["jihi_count"] == 0
        assert parsed_result["summary"]["jihi_amount"] == 3850

    def test_zenkai_sagaku(self, parsed_result):
        assert parsed_result["summary"]["zenkai_sagaku"] == -700

    def test_bushan(self, parsed_result):
        assert parsed_result["summary"]["bushan_amount"] == 1560

    def test_kaigo(self, parsed_result):
        assert parsed_result["summary"]["kaigo_amount"] == 0

    def test_summary_fields_present(self, parsed_result):
        assert set(parsed_result["summary"].keys()) == EXPECTED_SUMMARY_KEYS

    def test_patients_extracted(self, parsed_result):
        """Verify that patient records were extracted."""
        patients = parsed_result["patients"]
        # PDF has 55 patients total (some rows like "その他" or blank may be skipped)
        assert len(patients) > 0
        assert len(patients) <= 55

    def test_patient_structure(self, parsed_result):
        """Verify that each patient has all expected keys."""
        patients = parsed_result["patients"]
        if patients:
            for patient in patients:
                assert set(patient.keys()) == EXPECTED_PATIENT_KEYS

    def test_patient_data_sample(self, parsed_result):
        """Verify a sample patient's data matches expected values."""
        patients = parsed_result["patients"]
        if patients:
            # First patient should be No.11378 松本　正和
            first_patient = patients[0]
            assert first_patient["number"] == 1
            # Patient ID and name should be extracted
            assert "No.11378" in first_patient["patient_id"] or "11378" in first_patient["patient_id"]
