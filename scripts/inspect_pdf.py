"""total_d.pdf の pdfplumber 抽出テキストと parse_pdf 結果を確認するスクリプト"""
import sys
import os
import io

# --- parse_daily_report をインポートするための準備 ---
os.environ.setdefault("NOTION_TOKEN", "test-token")
os.environ.setdefault("NOTION_DATABASE_ID", "test-db-id")

from unittest.mock import MagicMock
sys.modules['cgi'] = MagicMock()
sys.modules['notion_client'] = MagicMock()
sys.modules['utils'] = MagicMock()
sys.modules['utils.notion_uploader'] = MagicMock()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

import pdfplumber
from parse_daily_report import parse_pdf

PDF_PATH = os.path.join(os.path.dirname(__file__), '..', 'total_d.pdf')

def main():
    print("=" * 60)
    print("pdfplumber テキスト抽出結果")
    print("=" * 60)

    with pdfplumber.open(PDF_PATH) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            print(f"\n--- Page {i+1}/{len(pdf.pages)} ---")
            print(text)
            print(f"--- End Page {i+1} (length: {len(text)} chars) ---")

    print("\n" + "=" * 60)
    print("parse_pdf() 結果")
    print("=" * 60)

    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    result = parse_pdf(io.BytesIO(pdf_bytes))

    for key, value in result.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
