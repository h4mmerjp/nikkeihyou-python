"""Data Source APIテストスクリプト（API 2025-09-03対応）"""
import os
import sys
import requests
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# Windows環境でのUnicode出力対応
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_data_source():
    """Data Source APIでプロパティを取得"""

    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")

    print("=" * 60)
    print("Data Source API テスト (API 2025-09-03)")
    print("=" * 60)

    if not notion_token or not database_id:
        print("[エラー] 環境変数が設定されていません")
        return False

    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2025-09-03",
        "Content-Type": "application/json",
    }

    # 1. データベースを取得してdata_source_idを確認
    print(f"\n[1] データベース情報を取得")
    print(f"    データベースID: {database_id}")

    db_url = f"https://api.notion.com/v1/databases/{database_id}"
    db_response = requests.get(db_url, headers=headers)

    if db_response.status_code != 200:
        print(f"[エラー] データベース取得失敗: {db_response.status_code}")
        print(db_response.text)
        return False

    db_data = db_response.json()
    data_sources = db_data.get("data_sources", [])

    if not data_sources:
        print("[エラー] data_sourcesが見つかりません")
        return False

    print(f"[OK] データソース数: {len(data_sources)}")

    # 2. 各データソースのプロパティを取得
    for idx, ds in enumerate(data_sources):
        ds_id = ds.get("id")
        ds_name = ds.get("name", "Unknown")

        print(f"\n[2] データソース #{idx + 1}")
        print(f"    名前: {ds_name}")
        print(f"    ID: {ds_id}")

        # Retrieve Data Source API
        ds_url = f"https://api.notion.com/v1/data_sources/{ds_id}"
        ds_response = requests.get(ds_url, headers=headers)

        if ds_response.status_code != 200:
            print(f"    [エラー] データソース取得失敗: {ds_response.status_code}")
            print(f"    {ds_response.text}")
            continue

        ds_data = ds_response.json()

        # プロパティを確認
        properties = ds_data.get("properties", {})
        print(f"    [OK] プロパティ数: {len(properties)}")

        if len(properties) > 0:
            print(f"\n    プロパティ一覧:")
            for prop_name, prop_data in properties.items():
                prop_type = prop_data.get("type", "unknown")
                print(f"      - {prop_name} ({prop_type})")

        # .envに保存するか確認
        if len(properties) > 0:
            print(f"\n[成功] プロパティが見つかりました！")
            print(f"\n.envファイルにDATA_SOURCE_IDを追加しますか？ (y/n): ", end="")
            answer = input().strip().lower()

            if answer == 'y':
                # .envファイルを更新
                env_path = ".env"
                with open(env_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if "NOTION_DATA_SOURCE_ID=" not in content:
                    with open(env_path, "a", encoding="utf-8") as f:
                        f.write(f"\nNOTION_DATA_SOURCE_ID={ds_id}\n")
                    print("[OK] NOTION_DATA_SOURCE_IDを追加しました")
                else:
                    # 既存の行を更新
                    lines = content.split('\n')
                    with open(env_path, "w", encoding="utf-8") as f:
                        for line in lines:
                            if line.startswith("NOTION_DATA_SOURCE_ID="):
                                f.write(f"NOTION_DATA_SOURCE_ID={ds_id}\n")
                            else:
                                f.write(line + '\n' if line else '')
                    print("[OK] NOTION_DATA_SOURCE_IDを更新しました")

            return True

    print("\n[警告] プロパティを持つデータソースが見つかりませんでした")
    return False

if __name__ == "__main__":
    success = test_data_source()

    if success:
        print("\n" + "=" * 60)
        print("[完了] Data Source APIテスト成功！")
        print("=" * 60)
        print("\n次のステップ:")
        print("1. コードをData Source API対応に修正します")
        print("2. 修正後、PDFアップロードをテスト")
    else:
        print("\n失敗しました。")

    exit(0 if success else 1)
