"""データベースID確認スクリプト"""
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

def check_database_id():
    """データベースIDを確認"""

    print("=" * 60)
    print("データベースID確認ツール")
    print("=" * 60)

    notion_token = os.environ.get("NOTION_TOKEN")
    database_id = os.environ.get("NOTION_DATABASE_ID")

    if not notion_token or not database_id:
        print("[エラー] 環境変数が設定されていません")
        return False

    print(f"\n設定値:")
    print(f"  NOTION_TOKEN: {notion_token[:10]}...{notion_token[-10:]}")
    print(f"  NOTION_DATABASE_ID: {database_id}")
    print(f"  データベースID長: {len(database_id)} 文字")

    # データベースIDの形式チェック
    print(f"\nデータベースID形式チェック:")

    # ハイフンを除いた文字数
    id_without_hyphens = database_id.replace("-", "")
    print(f"  ハイフンなし文字数: {len(id_without_hyphens)} (正しい値: 32)")

    # ハイフンの位置
    if "-" in database_id:
        parts = database_id.split("-")
        print(f"  ハイフン区切り: {'-'.join([str(len(p)) for p in parts])} (正しい値: 8-4-4-4-12)")
        expected_format = len(parts) == 5 and [len(p) for p in parts] == [8, 4, 4, 4, 12]
        if expected_format:
            print(f"  [OK] 形式は正しいです")
        else:
            print(f"  [NG] 形式が正しくありません")
            print(f"       正しい形式: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    else:
        print(f"  [NG] ハイフンがありません")
        if len(database_id) == 32:
            formatted = f"{database_id[:8]}-{database_id[8:12]}-{database_id[12:16]}-{database_id[16:20]}-{database_id[20:]}"
            print(f"  推奨形式: {formatted}")

    # Notion APIに直接リクエスト
    print(f"\nNotion APIリクエストテスト:")
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Notion-Version": "2025-09-03",
        "Content-Type": "application/json",
    }

    # データベース取得を試行
    url = f"https://api.notion.com/v1/databases/{database_id}"
    print(f"  URL: {url}")

    try:
        response = requests.get(url, headers=headers)
        print(f"  ステータスコード: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            db_title = data.get('title', [{}])[0].get('plain_text', 'Unknown')
            print(f"  [OK] データベース名: {db_title}")
            print(f"\n[成功] データベースIDは正しいです！")
            return True
        else:
            print(f"  [NG] エラーレスポンス:")
            try:
                error_data = response.json()
                print(f"       {error_data}")
            except:
                print(f"       {response.text}")

            if response.status_code == 404:
                print(f"\n[404エラー] データベースが見つかりません")
                print(f"  原因:")
                print(f"    - データベースIDが間違っている")
                print(f"    - ページIDをデータベースIDとして使用している")
                print(f"    - データベースが削除された")
            elif response.status_code == 401:
                print(f"\n[401エラー] 認証エラー")
                print(f"  原因:")
                print(f"    - NOTION_TOKENが間違っている")
                print(f"    - Integrationが無効化された")
            elif response.status_code == 403:
                print(f"\n[403エラー] アクセス拒否")
                print(f"  原因:")
                print(f"    - Integrationがデータベースに接続されていない")
            elif response.status_code == 400:
                print(f"\n[400エラー] 不正なリクエスト")
                print(f"  原因:")
                print(f"    - データベースIDの形式が間違っている")
                print(f"    - APIバージョンが正しくない")

            return False

    except Exception as e:
        print(f"  [NG] リクエスト失敗: {e}")
        return False

if __name__ == "__main__":
    print("\nヒント: NotionでデータベースのURLを確認してください")
    print("例: https://www.notion.so/workspace/db-name-30168957-60d2-80a4-90e9-c7186c49f2d6?v=...")
    print("                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ この部分")
    print()

    success = check_database_id()

    if not success:
        print("\n" + "=" * 60)
        print("次のステップ:")
        print("1. Notionでデータベースページを開く")
        print("2. ブラウザのアドレスバーからURLをコピー")
        print("3. URLからデータベースIDを抽出")
        print("4. .envファイルのNOTION_DATABASE_IDを更新")
        print("=" * 60)

    exit(0 if success else 1)
