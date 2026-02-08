"""Notion保存機能をテストするスクリプト"""
import os
import sys
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# パスを追加
project_root = os.path.dirname(__file__)
api_dir = os.path.join(project_root, 'api')
sys.path.insert(0, project_root)
sys.path.insert(0, api_dir)

print("=" * 60)
print("Notion保存テスト")
print("=" * 60)

# 環境変数を確認
notion_token = os.environ.get("NOTION_TOKEN")
database_id = os.environ.get("NOTION_DATABASE_ID")
data_source_id = os.environ.get("NOTION_DATA_SOURCE_ID")

print(f"\n環境変数:")
print(f"  NOTION_TOKEN: {'設定済み' if notion_token else '未設定'}")
print(f"  NOTION_DATABASE_ID: {database_id}")
print(f"  NOTION_DATA_SOURCE_ID: {data_source_id}")

if not all([notion_token, database_id, data_source_id]):
    print("\n[エラー] 環境変数が不足しています")
    sys.exit(1)

# テストデータ
test_summary = {
    "date": "2025-06-13",
    "shaho_count": 22,
    "shaho_amount": 68140,
    "kokuho_count": 19,
    "kokuho_amount": 45450,
    "kouki_count": 16,
    "kouki_amount": 27510,
    "jihi_count": 0,
    "jihi_amount": 48950,
    "hoken_nashi_count": 1,
    "hoken_nashi_amount": 10140,
    "total_count": 61,
    "total_amount": 151240,
    "bushan_amount": 2300,
    "kaigo_amount": 0,
    "zenkai_sagaku": -7040,
}

test_patients = [
    {
        "number": 1,
        "patient_id": "No.12345",
        "name": "テスト　太郎",
        "insurance_type": "社本",
        "points": 1000,
        "burden_amount": 3000,
        "kaigo_units": 0,
        "kaigo_burden": 0,
        "jihi": 0,
        "bushan": 0,
        "zenkai_sagaku": 0,
        "receipt_amount": 3000,
        "sagaku": 0,
        "remarks": "",
    }
]

test_today_difference = 7100

# ダミーPDF（空のバイト列）
test_pdf_bytes = b"%PDF-1.4\n%EOF\n"

print(f"\nテストデータ:")
print(f"  日付: {test_summary['date']}")
print(f"  合計人数: {test_summary['total_count']}")
print(f"  合計金額: {test_summary['total_amount']}")
print(f"  患者データ: {len(test_patients)}件")
print(f"  当日差額: {test_today_difference}")

try:
    print(f"\nsave_to_notion関数をインポート中...")
    from parse_daily_report import save_to_notion

    print(f"Notionに保存中...")
    page_id = save_to_notion(
        test_pdf_bytes,
        test_summary,
        test_patients,
        test_today_difference
    )

    print(f"\n" + "=" * 60)
    print(f"[成功] Notionに保存されました！")
    print(f"=" * 60)
    print(f"ページID: {page_id}")
    print(f"URL: https://www.notion.so/{page_id.replace('-', '')}")

except Exception as e:
    print(f"\n" + "=" * 60)
    print(f"[エラー] 保存失敗")
    print(f"=" * 60)
    print(f"エラーメッセージ: {e}")

    import traceback
    print(f"\n詳細なエラー情報:")
    traceback.print_exc()

    sys.exit(1)
