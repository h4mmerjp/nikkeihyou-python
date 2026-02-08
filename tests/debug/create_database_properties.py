"""Notionデータベースにプロパティを自動作成するスクリプト"""
import os
import sys
from notion_client import Client
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# Windows環境でのUnicode出力対応
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def create_properties():
    """データベースにプロパティを追加"""

    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")

    print("=" * 60)
    print("Notionデータベースプロパティ自動作成")
    print("=" * 60)

    if not notion_token or not database_id:
        print("[エラー] 環境変数が設定されていません")
        return False

    print(f"\nデータベースID: {database_id}")

    # Notion Client初期化
    notion = Client(auth=notion_token, notion_version="2025-09-03")

    # 作成するプロパティの定義
    properties_to_create = {
        "タイトル": {"title": {}},
        "日付": {"date": {}},
        "社保人数": {"number": {"format": "number"}},
        "社保金額": {"number": {"format": "yen"}},
        "国保人数": {"number": {"format": "number"}},
        "国保金額": {"number": {"format": "yen"}},
        "後期人数": {"number": {"format": "number"}},
        "後期金額": {"number": {"format": "yen"}},
        "自費人数": {"number": {"format": "number"}},
        "自費金額": {"number": {"format": "yen"}},
        "保険なし人数": {"number": {"format": "number"}},
        "保険なし金額": {"number": {"format": "yen"}},
        "合計人数": {"number": {"format": "number"}},
        "合計金額": {"number": {"format": "yen"}},
        "物販": {"number": {"format": "yen"}},
        "介護": {"number": {"format": "yen"}},
        "前回差額": {"number": {"format": "yen"}},
        "当日差額": {"number": {"format": "yen"}},
        "PDF": {"files": {}},
        "照合画面PDF": {"files": {}},
        "照合状態": {
            "select": {
                "options": [
                    {"name": "未照合", "color": "gray"},
                    {"name": "一致", "color": "green"},
                    {"name": "不一致", "color": "red"}
                ]
            }
        },
        "入力金額": {"number": {"format": "yen"}},
        "照合日時": {"date": {}},
    }

    try:
        print(f"\nプロパティを作成中...")
        print(f"合計: {len(properties_to_create)}個\n")

        # データベースを更新
        updated_db = notion.databases.update(
            database_id=database_id,
            properties=properties_to_create
        )

        # 結果を確認
        created_properties = updated_db.get('properties', {})
        print(f"[成功] プロパティ作成完了！")
        print(f"作成されたプロパティ数: {len(created_properties)}\n")

        print("作成されたプロパティ一覧:")
        for prop_name, prop_data in created_properties.items():
            prop_type = prop_data.get('type', 'unknown')
            print(f"  [OK] {prop_name} ({prop_type})")

        print("\n" + "=" * 60)
        print("[完了] すべてのプロパティが作成されました！")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n[エラー] プロパティ作成失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_properties()

    if success:
        print("\n次のステップ:")
        print("1. python test_notion_connection.py を実行してプロパティを確認")
        print("2. PDFをアップロードしてNotionに保存をテスト")
    else:
        print("\nエラーが発生しました。環境変数とIntegration接続を確認してください。")

    exit(0 if success else 1)
