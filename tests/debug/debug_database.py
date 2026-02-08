"""データベース詳細デバッグスクリプト"""
import os
import sys
import json
from notion_client import Client
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# Windows環境でのUnicode出力対応
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def debug_database():
    """データベースの詳細情報を表示"""

    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")

    print("=" * 60)
    print("データベース詳細デバッグ")
    print("=" * 60)

    if not notion_token or not database_id:
        print("[エラー] 環境変数が設定されていません")
        return

    print(f"\n設定値:")
    print(f"  NOTION_DATABASE_ID: {database_id}")

    # Notion Client初期化
    notion = Client(auth=notion_token, notion_version="2025-09-03")

    # データベース情報を取得
    try:
        print("\nデータベース情報を取得中...")
        db = notion.databases.retrieve(database_id=database_id)

        print("\n========== データベース基本情報 ==========")
        print(f"Object: {db.get('object')}")
        print(f"ID: {db.get('id')}")

        # タイトル
        title_obj = db.get('title', [])
        if title_obj:
            title = title_obj[0].get('plain_text', 'Unknown')
            print(f"タイトル: {title}")
        else:
            print(f"タイトル: (なし)")

        # プロパティ情報
        properties = db.get('properties', {})
        print(f"\n========== プロパティ情報 ==========")
        print(f"プロパティ数: {len(properties)}")

        if len(properties) > 0:
            print(f"\nプロパティ一覧:")
            for prop_name, prop_data in properties.items():
                prop_type = prop_data.get('type', 'unknown')
                prop_id = prop_data.get('id', 'N/A')
                print(f"  - {prop_name}")
                print(f"      タイプ: {prop_type}")
                print(f"      ID: {prop_id}")
        else:
            print("\n[警告] プロパティが0個です")

        # 完全なJSONレスポンスを保存
        print(f"\n完全なレスポンスをファイルに保存しています...")
        with open("database_response.json", "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        print(f"  保存先: database_response.json")

        # parent情報
        parent = db.get('parent', {})
        print(f"\n========== Parent情報 ==========")
        print(f"Parent type: {parent.get('type')}")
        if parent.get('type') == 'page_id':
            print(f"Page ID: {parent.get('page_id')}")
            print(f"\n[注意] これはページ内のインラインデータベースです")
            print(f"       フルページデータベースではありません")
        elif parent.get('type') == 'workspace':
            print(f"Workspace: True")
            print(f"[OK] これはワークスペース直下のデータベースです")

        # データベースかページかを確認
        print(f"\n========== オブジェクトタイプ確認 ==========")
        if db.get('object') == 'database':
            print(f"[OK] これは正しくデータベースです")
        else:
            print(f"[警告] これはデータベースではありません: {db.get('object')}")

    except Exception as e:
        print(f"\n[エラー] データベース取得失敗: {e}")
        import traceback
        traceback.print_exc()
        return

    # ページとして取得を試みる
    print(f"\n" + "=" * 60)
    print(f"念のためページとして取得を試みます...")
    print(f"=" * 60)

    try:
        page = notion.pages.retrieve(page_id=database_id)
        print(f"\n[重要] このIDはページとしても取得できました！")
        print(f"Object: {page.get('object')}")

        # ページのプロパティ
        page_properties = page.get('properties', {})
        print(f"ページのプロパティ数: {len(page_properties)}")

        if len(page_properties) > 0:
            print(f"\nページプロパティ一覧:")
            for prop_name, prop_data in page_properties.items():
                prop_type = prop_data.get('type', 'unknown')
                print(f"  - {prop_name} ({prop_type})")

        # 完全なJSONレスポンスを保存
        with open("page_response.json", "w", encoding="utf-8") as f:
            json.dump(page, f, indent=2, ensure_ascii=False)
        print(f"\nページレスポンスを保存: page_response.json")

    except Exception as e:
        print(f"\nページとしての取得は失敗しました（正常です）: {e}")

if __name__ == "__main__":
    debug_database()
