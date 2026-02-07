"""
Shared fixtures and module-level mocking for parse_pdf tests.

Module-level setup: mock environment variables and external modules
BEFORE importing parse_daily_report, because that module accesses
os.environ["NOTION_TOKEN"] and imports notion_client at module load time.
"""
import sys
import os
from unittest.mock import MagicMock

import pytest

# ---- Module-level mocks (must happen before any import of parse_daily_report) ----

# 1. Environment variables used at import time by parse_daily_report (line 14-15)
os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_DATABASE_ID", "test-db-id")

# 2. External modules that are imported at module level
sys.modules.setdefault("notion_client", MagicMock())
sys.modules.setdefault("utils", MagicMock())
sys.modules.setdefault("utils.notion_uploader", MagicMock())

# 3. Mock pdfplumber — tests always patch it; avoids broken native deps in CI
sys.modules.setdefault("pdfplumber", MagicMock())

# 4. The 'cgi' module was removed in Python 3.13; mock it if unavailable
try:
    import cgi  # noqa: F401
except ModuleNotFoundError:
    sys.modules["cgi"] = MagicMock()


# ---- Helper: build a table row for extract_table() ----

def make_table_row(
    number,
    name_cell,
    insurance_type,
    points,
    futan_cell,
    kaigo_units=None,
    kaigo_amount=None,
    jihi=None,
    buppan=None,
    previous_diff=None,
    receipt_amount=None,
    diff=None,
    extra=None,
):
    """Build a 12-column table row list as returned by pdfplumber extract_table().

    Parameters match the column layout:
    [0] number, [1] name_cell, [2] insurance_type, [3] points,
    [4] futan_cell, [5] kaigo_units, [6] kaigo_amount, [7] jihi,
    [8] buppan, [9] previous_diff, [10] receipt_amount, [11] diff
    """
    return [
        str(number),
        name_cell,
        insurance_type,
        str(points) if points is not None else None,
        futan_cell,
        str(kaigo_units) if kaigo_units is not None else None,
        str(kaigo_amount) if kaigo_amount is not None else None,
        str(jihi) if jihi is not None else None,
        str(buppan) if buppan is not None else None,
        str(previous_diff) if previous_diff is not None else None,
        str(receipt_amount) if receipt_amount is not None else None,
        str(diff) if diff is not None else None,
    ]


# ---- Realistic table data ----

REALISTIC_TABLE_ROWS = [
    # header row (skipped by parse_pdf because row[0] is not a digit)
    ["番号", "氏名", "保険種別", "点数", "負担額", "介護単位", "介護負担額",
     "自費", "物販", "前回差額", "領収額", "差額"],
    # 社保 patients
    make_table_row(1, "No.10001\n山田太郎", "社本", 500, "30%\n1,500",
                   receipt_amount=1500, diff=0),
    make_table_row(2, "No.10002\n鈴木花子", "社家", 300, "30%\n900",
                   receipt_amount=900, diff=0),
    make_table_row(3, "No.10003\n佐藤次郎", "社家 乳無", 200, "0%\n0",
                   jihi=3000, receipt_amount=3000, diff=0),
    # 国保 patients
    make_table_row(4, "No.10004\n田中一郎", "国家", 400, "30%\n1,200",
                   receipt_amount=1200, diff=0),
    # 後期 patients
    make_table_row(5, "No.10005\n高橋花子", "後期", 600, "10%\n600",
                   receipt_amount=600, diff=0),
    make_table_row(6, "No.10006\n渡辺太郎", "後期 難病", 800, "10%\n800",
                   kaigo_units=100, kaigo_amount=500, receipt_amount=1300, diff=0),
    # 保険なし
    make_table_row(7, "No.10007\n伊藤真", "保険なし", 0, "100%\n5,000",
                   buppan=1560, receipt_amount=6560, diff=0),
    # 前回差額のみ（保険種別空欄 → その他に分類）
    make_table_row(8, "No.10008\n三宅太郎", "", 0, "",
                   previous_diff=-700, receipt_amount=-700, diff=0),
    # total row (skipped because row[0] is not a digit)
    ["合計", "", "", "2,800", "", "100", "500", "3,000", "1,560", "-700", "14,360", "0"],
]


@pytest.fixture
def realistic_table_rows():
    """Return realistic table rows for testing."""
    return REALISTIC_TABLE_ROWS


@pytest.fixture
def realistic_first_page_text():
    """Return realistic first-page text with a standard date."""
    return "○○医院  日計表\n令和7年1月15日\n受付番号  患者名  保険種別  点数  金額"
