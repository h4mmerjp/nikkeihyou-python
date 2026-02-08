"""PDFファイルの pdfplumber 抽出テキストと parse_pdf 結果を確認するスクリプト

使用方法:
    python scripts/inspect_pdf.py [PDF_FILE_PATH]

引数:
    PDF_FILE_PATH: テストするPDFファイルのパス（省略時は total_d.pdf）

例:
    python scripts/inspect_pdf.py
    python scripts/inspect_pdf.py my_report.pdf
    python scripts/inspect_pdf.py C:/Users/user/Documents/report.pdf
"""
import sys
import os
import io
import argparse

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

def main():
    # コマンドライン引数をパース
    parser = argparse.ArgumentParser(
        description='PDFファイルからデータを抽出してテストします',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python scripts/inspect_pdf.py                          # total_d.pdf を使用
  python scripts/inspect_pdf.py my_report.pdf            # my_report.pdf を使用
  python scripts/inspect_pdf.py data/report_2025.pdf    # 相対パスで指定
        """
    )
    parser.add_argument(
        'pdf_file',
        nargs='?',
        default=None,
        help='テストするPDFファイルのパス（省略時は total_d.pdf）'
    )
    parser.add_argument(
        '--no-text',
        action='store_true',
        help='テキスト抽出結果を表示しない（結果のみ表示）'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='すべての患者データを表示（デフォルトは最初の5件のみ）'
    )

    args = parser.parse_args()

    # PDFファイルパスを決定
    if args.pdf_file:
        pdf_path = args.pdf_file
        # 相対パスの場合は絶対パスに変換
        if not os.path.isabs(pdf_path):
            pdf_path = os.path.abspath(pdf_path)
    else:
        # デフォルトは total_d.pdf
        pdf_path = os.path.join(os.path.dirname(__file__), '..', 'total_d.pdf')
        pdf_path = os.path.abspath(pdf_path)

    # ファイルの存在確認
    if not os.path.exists(pdf_path):
        print(f"エラー: ファイルが見つかりません: {pdf_path}")
        print(f"\n使用方法:")
        print(f"  python scripts/inspect_pdf.py [PDF_FILE_PATH]")
        print(f"\n例:")
        print(f"  python scripts/inspect_pdf.py")
        print(f"  python scripts/inspect_pdf.py my_report.pdf")
        sys.exit(1)

    print("=" * 60)
    print(f"PDFファイル: {os.path.basename(pdf_path)}")
    print(f"フルパス: {pdf_path}")
    print("=" * 60)

    if not args.no_text:
        print("\n" + "=" * 60)
        print("pdfplumber テキスト抽出結果")
        print("=" * 60)

        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                print(f"\n--- Page {i+1}/{len(pdf.pages)} ---")
                print(text)
                print(f"--- End Page {i+1} (length: {len(text)} chars) ---")

    print("\n" + "=" * 60)
    print("parse_pdf() 結果")
    print("=" * 60)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    try:
        result = parse_pdf(io.BytesIO(pdf_bytes))
    except Exception as e:
        print(f"\nエラー: PDF解析に失敗しました")
        print(f"エラー内容: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n[集計データ]")
    for key, value in result["summary"].items():
        print(f"  {key}: {value}")

    print(f"\n[個別患者データ] 件数: {len(result['patients'])}")

    # 表示する患者数を決定
    display_count = len(result["patients"]) if args.all else min(5, len(result["patients"]))

    for i, patient in enumerate(result["patients"][:display_count], 1):
        print(f"\n  患者 {i}:")
        for key, value in patient.items():
            print(f"    {key}: {value}")

    if len(result["patients"]) > display_count:
        print(f"\n  ... (残り {len(result['patients']) - display_count} 件)")
        print(f"\n  ※ すべての患者データを表示するには --all オプションを使用してください")

if __name__ == "__main__":
    main()
