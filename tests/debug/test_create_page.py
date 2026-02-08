"""Notionページ作成テスト（API 2025-09-03対応）"""
import os
import sys
from notion_client import Client
from dotenv import load_dotenv
from datetime import datetime

# .envファイルを読み込む
load_dotenv()

# Windows環境でのUnicode出力対応
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_create_page():
    """テストページを作成"""

    notion_token = os.environ.get("NOTION_TOKEN")
    data_source_id = os.environ.get("NOTION_DATA_SOURCE_ID")

    print("=" * 60)
    print("Notionページ作成テスト (API 2025-09-03)")
    print("=" * 60)

    if not notion_token or not data_source_id:
        print("[エラー] 環境変数が設定されていません")
        print(f"  NOTION_TOKEN: {'設定済み' if notion_token else '未設定'}")
        print(f"  NOTION_DATA_SOURCE_ID: {'設定済み' if data_source_id else '未設定'}")
        return False

    print(f"\nデータソースID: {data_source_id}")

    # Notion Client初期化
    notion = Client(auth=notion_token, notion_version="2025-09-03")

    # テストデータ
    test_date = datetime.now().strftime("%Y-%m-%d")

    try:
        print(f"\nテストページを作成中...")
        print(f"  日付: {test_date}")

        # ページ作成
        page = notion.pages.create(
            parent={"type": "data_source_id", "data_source_id": data_source_id},
            properties={
                "タイトル": {"title": [{"text": {"content": f"{test_date} テスト"}}]},
                "日付": {"date": {"start": test_date}},
                "社保人数": {"number": 10},
                "社保金額": {"number": 50000},
                "国保人数": {"number": 5},
                "国保金額": {"number": 25000},
                "後期人数": {"number": 3},
                "後期金額": {"number": 15000},
                "自費人数": {"number": 0},
                "自費金額": {"number": 0},
                "保険なし人数": {"number": 0},
                "保険なし金額": {"number": 0},
                "合計人数": {"number": 18},
                "合計金額": {"number": 90000},
                "物販": {"number": 0},
                "介護": {"number": 0},
                "前回差額": {"number": 0},
                "当日差額": {"number": 0},
                "照合状態": {"select": {"name": "未照合"}},
            },
        )

        page_id = page["id"]
        page_url = page.get("url", "")

        print(f"\n[成功] ページ作成完了！")
        print(f"  ページID: {page_id}")
        print(f"  URL: {page_url}")

        # ページにテキストブロックを追加
        print(f"\nブロックを追加中...")

        notion.blocks.children.append(
            block_id=page_id,
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": "テストデータ"}}]
                    },
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": "これはAPI 2025-09-03対応のテストページです。"}}]
                    },
                },
            ],
        )

        print(f"[OK] ブロック追加完了")

        print("\n" + "=" * 60)
        print("[完了] すべてのテストに成功しました！")
        print("=" * 60)
        print(f"\nNotionでページを確認:")
        print(f"  {page_url}")

        return True

    except Exception as e:
        print(f"\n[エラー] ページ作成失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_create_page()

    if success:
        print("\n次のステップ:")
        print("1. NotionでテストページをPDF確認")
        print("2. 実際のPDFアップロード機能をテスト")
    else:
        print("\n失敗しました。エラーメッセージを確認してください。")

    exit(0 if success else 1)
