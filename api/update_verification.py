from http.server import BaseHTTPRequestHandler
from notion_client import Client
import json
import os
import base64
from datetime import datetime

# .envファイルを読み込む（ローカル開発時のみ）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Vercel環境では不要（環境変数は自動的に設定される）
    pass

from utils.notion_uploader import upload_file_to_notion

notion = Client(auth=os.environ["NOTION_TOKEN"])


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length))

            page_id = body["notion_page_id"]
            is_matched = body["is_matched"]
            cash_input = body["cash_input"]
            frontend_pdf_b64 = body["frontend_pdf_base64"]
            date = body.get("date", "")  # 日付を取得（YYYY-MM-DD形式）

            # フロント画面 PDF をデコード
            frontend_pdf_bytes = base64.b64decode(frontend_pdf_b64)

            # PDF アップロード（日付ベースのファイル名）
            if date:
                frontend_filename = f"照合画面_{date}.pdf"
            else:
                # 日付がない場合はタイムスタンプを使用（フォールバック）
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                frontend_filename = f"照合画面_{ts}.pdf"

            frontend_file_id = upload_file_to_notion(
                frontend_pdf_bytes,
                frontend_filename,
                "application/pdf",
            )

            # ページプロパティ更新
            notion.pages.update(
                page_id=page_id,
                properties={
                    "照合状態": {
                        "select": {"name": "一致" if is_matched else "不一致"}
                    },
                    "入力金額": {"number": cash_input},
                    "照合日時": {"date": {"start": datetime.now().isoformat()}},
                    "照合画面PDF": {
                        "files": [
                            {
                                "type": "file_upload",
                                "file_upload": {"id": frontend_file_id},
                                "name": frontend_filename,
                            }
                        ]
                    },
                },
            )

            # 照合画面 PDF をページ内ブロックに追加
            notion.blocks.children.append(
                block_id=page_id,
                children=[
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": "✅ 照合画面PDF"},
                                }
                            ]
                        },
                    },
                    {
                        "object": "block",
                        "type": "file",
                        "file": {
                            "type": "file_upload",
                            "file_upload": {"id": frontend_file_id},
                            "caption": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"照合結果: {'一致' if is_matched else '不一致'}"
                                    },
                                }
                            ],
                        },
                    },
                ],
            )

            self._send_json(200, {"success": True})

        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status, data):
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
