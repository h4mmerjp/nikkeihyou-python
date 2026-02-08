"""Notion接続テストスクリプト"""
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

def test_notion_connection():
    """Notion APIの接続テスト"""

    print("=" * 60)
    print("Notion接続テスト")
    print("=" * 60)

    # 1. 環境変数の確認
    print("\n[1] 環境変数の確認")
    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")

    if not notion_token:
        print("[NG] NOTION_TOKEN が設定されていません")
        print("     設定方法:")
        print("     Windows: set NOTION_TOKEN=your_token")
        print("     Mac/Linux: export NOTION_TOKEN=your_token")
        return False
    else:
        print(f"[OK] NOTION_TOKEN: {notion_token[:10]}...{notion_token[-10:]}")

    if not database_id:
        print("[NG] NOTION_DATABASE_ID が設定されていません")
        print("     設定方法:")
        print("     Windows: set NOTION_DATABASE_ID=your_database_id")
        print("     Mac/Linux: export NOTION_DATABASE_ID=your_database_id")
        return False
    else:
        print(f"[OK] NOTION_DATABASE_ID: {database_id}")

        # データベースIDのフォーマット確認
        if len(database_id) == 32 and "-" not in database_id:
            formatted_id = f"{database_id[:8]}-{database_id[8:12]}-{database_id[12:16]}-{database_id[16:20]}-{database_id[20:]}"
            print(f"     [警告] ハイフンなしのID検出。正しい形式: {formatted_id}")
            print(f"     環境変数を修正してください:")
            print(f"     set NOTION_DATABASE_ID={formatted_id}")

    # 2. Notion API接続テスト
    print("\n[2] Notion API接続テスト")
    try:
        notion = Client(auth=notion_token, notion_version="2025-09-03")
        print("[OK] Notion Clientの初期化成功")
    except Exception as e:
        print(f"[NG] Notion Clientの初期化失敗: {e}")
        return False

    # 3. データベース取得テスト
    print("\n[3] データベース取得テスト")
    try:
        print(f"     リクエスト送信中...")
        db = notion.databases.retrieve(database_id=database_id)
        db_title = db.get('title', [{}])[0].get('plain_text', 'Unknown')
        print(f"[OK] データベース取得成功: {db_title}")

        # プロパティの確認
        print("\n[4] データベースプロパティの確認")
        properties = db.get("properties", {})
        print(f"     プロパティ数: {len(properties)}")

        required_properties = [
            "タイトル", "日付", "社保人数", "社保金額", "国保人数", "国保金額",
            "後期人数", "後期金額", "自費人数", "自費金額", "保険なし人数", "保険なし金額",
            "合計人数", "合計金額", "物販", "介護", "前回差額", "当日差額",
            "PDF", "照合画面PDF", "照合状態", "入力金額", "照合日時"
        ]

        missing_properties = []
        for prop_name in required_properties:
            if prop_name in properties:
                prop_type = properties[prop_name]["type"]
                print(f"     [OK] {prop_name} ({prop_type})")
            else:
                print(f"     [NG] {prop_name} (未設定)")
                missing_properties.append(prop_name)

        if missing_properties:
            print(f"\n[警告] 不足しているプロパティ: {', '.join(missing_properties)}")
            print("       これらのプロパティをNotionデータベースに追加してください。")
            return False

        print("\n" + "=" * 60)
        print("[成功] すべてのテストに合格しました！")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"[NG] データベース取得失敗: {e}")

        # 詳細なエラー情報を表示
        import traceback
        print("\n詳細なエラー情報:")
        traceback.print_exc()

        print("\n考えられる原因:")
        print("1. NOTION_DATABASE_ID が間違っている")
        print("2. Notion Integrationがデータベースに接続されていない")
        print("3. データベースIDのフォーマットが正しくない（ハイフンが必要）")
        print("4. ページIDをデータベースIDとして使用している可能性")

        # データベースIDの再確認を促す
        print("\n✓ データベースIDの確認方法:")
        print("  1. Notionでデータベースページを開く")
        print("  2. URLをコピー:")
        print("     https://www.notion.so/workspace/データベース名-[ここがデータベースID]?v=...")
        print("  3. ?の前の32文字（ハイフン付き）がデータベースID")
        print(f"\n  現在の設定: {database_id}")

        return False

if __name__ == "__main__":
    success = test_notion_connection()
    exit(0 if success else 1)
