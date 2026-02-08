"""新しいNotionデータベースを作成するスクリプト"""
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

def create_new_database():
    """新しいデータベースを作成"""

    notion_token = os.environ.get("NOTION_TOKEN")

    print("=" * 60)
    print("新しいNotionデータベースを作成")
    print("=" * 60)

    if not notion_token:
        print("[エラー] NOTION_TOKEN が設定されていません")
        return False

    # Notion Client初期化
    notion = Client(auth=notion_token, notion_version="2025-09-03")

    # プロパティの定義
    properties = {
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
        print("\n新しいデータベースを作成中...")
        print("プロパティ数: 23個\n")

        # データベースを作成（ワークスペース直下に作成）
        new_db = notion.databases.create(
            parent={"type": "page_id", "page_id": "workspace"},  # ワークスペースのルートに作成
            title=[{
                "type": "text",
                "text": {"content": "日計表管理（API作成）"}
            }],
            properties=properties
        )

        database_id = new_db["id"]
        db_url = new_db.get("url", "")

        print("[成功] データベース作成完了！\n")
        print(f"データベース名: 日計表管理（API作成）")
        print(f"データベースID: {database_id}")
        print(f"URL: {db_url}")

        # プロパティを確認
        created_properties = new_db.get('properties', {})
        print(f"\n作成されたプロパティ数: {len(created_properties)}")

        if len(created_properties) > 0:
            print("\nプロパティ一覧:")
            for prop_name, prop_data in created_properties.items():
                prop_type = prop_data.get('type', 'unknown')
                print(f"  [OK] {prop_name} ({prop_type})")

        # .envファイルを更新
        print("\n.envファイルを更新しますか？ (y/n): ", end="")
        answer = input().strip().lower()

        if answer == 'y':
            env_path = ".env"
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            with open(env_path, "w", encoding="utf-8") as f:
                for line in lines:
                    if line.startswith("NOTION_DATABASE_ID="):
                        f.write(f"NOTION_DATABASE_ID={database_id}\n")
                    else:
                        f.write(line)

            print(f"[OK] .envファイルを更新しました")

        print("\n" + "=" * 60)
        print("[完了] データベース作成が完了しました！")
        print("=" * 60)
        print(f"\n次のステップ:")
        print(f"1. Notionでデータベースを開く: {db_url}")
        print(f"2. python test_notion_connection.py を実行して確認")

        return True

    except Exception as e:
        print(f"\n[エラー] データベース作成失敗: {e}")

        # ワークスペースIDが必要な場合の処理
        if "parent" in str(e).lower() or "workspace" in str(e).lower():
            print("\n[注意] ワークスペースルートへの直接作成ができませんでした")
            print("代わりに、既存のページID配下に作成します。\n")
            print("親ページIDを入力してください:")
            print("（Notionでページを開いて、URLから取得: https://www.notion.so/PAGE_ID）")
            parent_page_id = input("親ページID: ").strip()

            if parent_page_id:
                try:
                    new_db = notion.databases.create(
                        parent={"type": "page_id", "page_id": parent_page_id},
                        title=[{
                            "type": "text",
                            "text": {"content": "日計表管理（API作成）"}
                        }],
                        properties=properties
                    )

                    database_id = new_db["id"]
                    db_url = new_db.get("url", "")

                    print(f"\n[成功] データベース作成完了！")
                    print(f"データベースID: {database_id}")
                    print(f"URL: {db_url}")

                    return True

                except Exception as e2:
                    print(f"[エラー] 作成失敗: {e2}")

        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_new_database()
    exit(0 if success else 1)
