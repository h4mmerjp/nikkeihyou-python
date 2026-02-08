import os
import io
import requests

# .envファイルを読み込む（ローカル開発時のみ）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Vercel環境では不要（環境変数は自動的に設定される）
    pass

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
# File Upload API は 2025-05-20 以降のバージョンが必要
NOTION_VERSION = "2025-09-03"


def upload_file_to_notion(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Notion File Upload API でファイルをアップロードし file_upload_id を返す"""

    headers_base = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
    }

    # Step 1: File Upload オブジェクト作成
    create_resp = requests.post(
        "https://api.notion.com/v1/file_uploads",
        headers={**headers_base, "Content-Type": "application/json"},
        json={
            "filename": filename,
            "content_type": content_type,
        },
    )
    if create_resp.status_code != 200:
        raise Exception(
            f"File upload creation failed ({create_resp.status_code}): {create_resp.text}"
        )

    file_upload_id = create_resp.json()["id"]

    # Step 2: ファイル本体を送信
    send_resp = requests.post(
        f"https://api.notion.com/v1/file_uploads/{file_upload_id}/send",
        headers=headers_base,
        files={
            "file": (filename, io.BytesIO(file_bytes), content_type),
        },
    )
    if send_resp.status_code != 200:
        raise Exception(
            f"File send failed ({send_resp.status_code}): {send_resp.text}"
        )

    return file_upload_id
