"""total_d.pdf のテーブル抽出テスト

PDFからテーブルを抽出して、構造を確認するためのスクリプト。
開発・デバッグ用。

使用方法:
    python tests/test_table_extraction.py
"""
import pdfplumber
import json
import os

# プロジェクトルートからの相対パス
PDF_PATH = os.path.join(os.path.dirname(__file__), '..', 'total_d.pdf')

def main():
    print("=" * 60)
    print("テーブル抽出テスト")
    print("=" * 60)
    print(f"\nPDFファイル: {os.path.abspath(PDF_PATH)}")

    if not os.path.exists(PDF_PATH):
        print(f"\nエラー: PDFファイルが見つかりません: {PDF_PATH}")
        return

    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"\nページ数: {len(pdf.pages)}")

        for page_num, page in enumerate(pdf.pages, 1):
            print(f"\n--- ページ {page_num} ---")

            tables = page.extract_tables()
            print(f"テーブル数: {len(tables)}")

            for table_num, table in enumerate(tables, 1):
                print(f"\nテーブル {table_num}:")
                print(f"  行数: {len(table)}")
                print(f"  列数: {len(table[0]) if table else 0}")

                # 最初の3行を表示
                print("\n  最初の3行:")
                for i, row in enumerate(table[:3], 1):
                    print(f"    行{i}: {row}")

                # データ行のサンプル（10行目あたり）
                if len(table) > 10:
                    print(f"\n  データ行サンプル（行11）:")
                    print(f"    {table[10]}")

if __name__ == "__main__":
    main()
