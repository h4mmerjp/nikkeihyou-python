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

# 1. Environment variables used at import time by parse_daily_report (line 13-14)
os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_DATABASE_ID", "test-db-id")

# 2. External modules that are imported at module level
sys.modules.setdefault("notion_client", MagicMock())
sys.modules.setdefault("utils", MagicMock())
sys.modules.setdefault("utils.notion_uploader", MagicMock())

# 3. The 'cgi' module was removed in Python 3.13; mock it if unavailable
try:
    import cgi  # noqa: F401
except ModuleNotFoundError:
    sys.modules["cgi"] = MagicMock()


# ---- Realistic text constants ----

REALISTIC_LAST_PAGE = """\
診療科別集計

区分     人数   点数      金額
社保     25   120,000   360,000
国保     10    45,000   135,000
後期     15    80,000   240,000
保険なし  3     5,000    15,000
合計     53   250,000   750,000   0   0   50,000   12,500   -500   812,000   0

物販合計 12,500

介護保険 請求額 30,000
"""

REALISTIC_FIRST_PAGE = """\
○○医院  日計表
令和7年1月15日

受付番号  患者名  保険種別  点数  金額
001       山田太郎  社保    500   1,500
002       鈴木花子  国保    300     900
"""


# ---- Fixtures ----

@pytest.fixture
def realistic_first_page():
    """Return realistic first-page text with a standard date."""
    return REALISTIC_FIRST_PAGE


@pytest.fixture
def realistic_last_page():
    """Return realistic last-page text with all financial categories."""
    return REALISTIC_LAST_PAGE
