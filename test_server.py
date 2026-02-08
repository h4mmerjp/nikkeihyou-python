#!/usr/bin/env python3
"""
簡易テストサーバー - 修正後のAPIレスポンス構造をテスト
"""
import os
import sys
import json
import io
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# プロジェクトのルートディレクトリとapiディレクトリをパスに追加
project_root = os.path.dirname(__file__)
api_dir = os.path.join(project_root, 'api')
sys.path.insert(0, project_root)
sys.path.insert(0, api_dir)

# .envファイルを読み込み
env_file = os.path.join(project_root, '.env')
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
else:
    # 環境変数がない場合はダミー値を設定（テスト用）
    os.environ.setdefault('NOTION_TOKEN', 'test-token')
    os.environ.setdefault('NOTION_DATABASE_ID', 'test-database-id')

# API関数をインポート
from parse_daily_report import parse_pdf

# マルチパートデータのパース用
try:
    import email
    from email.parser import BytesParser
    HAS_EMAIL_PARSER = True
except ImportError:
    HAS_EMAIL_PARSER = False


class TestServerHandler(SimpleHTTPRequestHandler):
    """テスト用のHTTPリクエストハンドラ"""

    def __init__(self, *args, **kwargs):
        # publicディレクトリをドキュメントルートに設定
        super().__init__(*args, directory="public", **kwargs)

    def do_OPTIONS(self):
        """CORS対応のOPTIONSリクエスト"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """POSTリクエストハンドラ"""
        if self.path == '/api/parse_daily_report':
            self.handle_parse_pdf()
        elif self.path == '/api/update_verification':
            self.handle_update_verification()
        else:
            self.send_error(404, "Not Found")

    def handle_parse_pdf(self):
        """PDF解析APIエンドポイント"""
        try:
            # Content-Typeとコンテンツ長を取得
            content_type = self.headers.get('Content-Type', '')
            content_length = int(self.headers.get('Content-Length', 0))

            # リクエストボディを読み込み
            body = self.rfile.read(content_length)

            # マルチパートデータを解析
            # Content-Typeからboundaryを取得
            if 'boundary=' not in content_type:
                self.send_json_response(400, {
                    'success': False,
                    'error': 'No boundary in Content-Type'
                })
                return

            # emailパーサーを使用してマルチパートデータをパース
            boundary = content_type.split('boundary=')[1].strip()

            # マルチパートメッセージとしてパース
            message_headers = f"Content-Type: {content_type}\r\n\r\n".encode()
            message = BytesParser().parsebytes(message_headers + body)

            # ファイルパートを探す
            pdf_bytes = None
            filename = 'unknown.pdf'

            for part in message.walk():
                content_disposition = str(part.get('Content-Disposition', ''))
                if 'filename=' in content_disposition:
                    # ファイル名を取得
                    filename_match = content_disposition.split('filename=')[1].strip('"\'')
                    if filename_match:
                        filename = filename_match
                    # ファイルデータを取得
                    pdf_bytes = part.get_payload(decode=True)
                    break

            if pdf_bytes is None:
                self.send_json_response(400, {
                    'success': False,
                    'error': 'No file uploaded'
                })
                return

            # PDF解析と Notion保存
            # ファイル名を安全にエンコード（cp932でエラーにならないように）
            safe_filename = filename.encode('ascii', 'ignore').decode('ascii') or 'unknown.pdf'
            print(f"[PDF] Received: {safe_filename} ({len(pdf_bytes)} bytes)")
            parsed_data = parse_pdf(io.BytesIO(pdf_bytes))

            # 当日差額を計算
            today_difference = sum(patient.get("sagaku", 0) for patient in parsed_data["patients"])

            # Notion に保存
            try:
                from parse_daily_report import save_to_notion
                print(f"[Notion] Saving to Notion...")
                notion_page_id = save_to_notion(
                    pdf_bytes,
                    parsed_data["summary"],
                    parsed_data["patients"],
                    today_difference
                )
                print(f"[Notion] Saved successfully. Page ID: {notion_page_id}")
            except Exception as e:
                print(f"[Notion] Save failed: {e}")
                notion_page_id = f"error-{str(e)[:50]}"

            # 修正後のレスポンス構造を返す
            result = {
                "success": True,
                "data": {
                    **parsed_data["summary"],
                    "previous_difference": parsed_data["summary"].get("zenkai_sagaku", 0),
                    "today_difference": today_difference,
                },
                "patients": parsed_data["patients"],
                "notion_page_id": notion_page_id,
            }

            # レスポンス構造をログ出力（確認用）
            print("\n[OK] Fixed Response Structure:")
            print(f"  - success: {result['success']}")
            print(f"  - data key: EXISTS")
            print(f"  - data.date: {result['data'].get('date')}")
            print(f"  - data.zenkai_sagaku: {result['data'].get('zenkai_sagaku')}")
            print(f"  - data.previous_difference: {result['data'].get('previous_difference')} [FIXED]")
            print(f"  - data.today_difference: {result['data'].get('today_difference')} [FIXED]")
            print(f"  - patients: {len(result['patients'])} records")
            print(f"  - notion_page_id: {result['notion_page_id']}")
            print()

            self.send_json_response(200, result)

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response(500, {
                'success': False,
                'error': str(e)
            })

    def handle_update_verification(self):
        """照合結果更新APIエンドポイント"""
        try:
            # JSONデータを読み込み
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))

            notion_page_id = data.get("notion_page_id")
            is_matched = data.get("is_matched")
            cash_input = data.get("cash_input")
            frontend_pdf_b64 = data.get("frontend_pdf_base64")
            date = data.get("date", "")

            print(f"[Verification] Page ID: {notion_page_id}")
            print(f"[Verification] Matched: {is_matched}")
            print(f"[Verification] Cash Input: {cash_input}")
            print(f"[Verification] Date: {date}")

            # フロントエンド画面PDFをデコード
            import base64
            frontend_pdf_bytes = base64.b64decode(frontend_pdf_b64)
            print(f"[Verification] Frontend PDF size: {len(frontend_pdf_bytes)} bytes")

            # Notionを更新
            try:
                from datetime import datetime
                from notion_client import Client
                from utils.notion_uploader import upload_file_to_notion

                notion_token = os.environ.get("NOTION_TOKEN")
                notion = Client(auth=notion_token, notion_version="2025-09-03")

                # PDFファイル名を作成
                if date:
                    frontend_filename = f"照合画面_{date}.pdf"
                else:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    frontend_filename = f"照合画面_{ts}.pdf"

                # PDFサイズをチェック（5MB = 5242880 bytes）
                max_size = 5242880
                frontend_file_id = None

                if len(frontend_pdf_bytes) > max_size:
                    print(f"[Verification] Frontend PDF too large ({len(frontend_pdf_bytes)} bytes > {max_size} bytes). Skipping upload.")
                else:
                    # PDFをアップロード
                    print(f"[Verification] Uploading frontend PDF: {frontend_filename}")
                    frontend_file_id = upload_file_to_notion(
                        frontend_pdf_bytes,
                        frontend_filename,
                        "application/pdf",
                    )
                    print(f"[Verification] Frontend PDF uploaded. File ID: {frontend_file_id}")

                # ページプロパティを更新
                print(f"[Verification] Updating Notion page properties...")

                properties_to_update = {
                    "照合状態": {
                        "select": {"name": "一致" if is_matched else "不一致"}
                    },
                    "入力金額": {"number": cash_input},
                    "照合日時": {"date": {"start": datetime.now().isoformat()}},
                }

                # PDFがアップロードされた場合のみプロパティに追加
                if frontend_file_id:
                    properties_to_update["照合画面PDF"] = {
                        "files": [
                            {
                                "type": "file_upload",
                                "file_upload": {"id": frontend_file_id},
                                "name": frontend_filename,
                            }
                        ]
                    }

                notion.pages.update(
                    page_id=notion_page_id,
                    properties=properties_to_update,
                )
                print(f"[Verification] Properties updated successfully")

                # 照合画面PDFをページ内ブロックに追加（PDFがアップロードされた場合のみ）
                if frontend_file_id:
                    print(f"[Verification] Adding frontend PDF block...")
                    notion.blocks.children.append(
                        block_id=notion_page_id,
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
                    print(f"[Verification] Block added successfully")
                else:
                    print(f"[Verification] Skipping PDF block (file too large)")

                    # 代わりにメモブロックを追加
                    notion.blocks.children.append(
                        block_id=notion_page_id,
                        children=[
                            {
                                "object": "block",
                                "type": "callout",
                                "callout": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {
                                                "content": f"照合結果: {'一致' if is_matched else '不一致'} (照合画面PDFはサイズ制限によりアップロードできませんでした)"
                                            }
                                        }
                                    ],
                                    "icon": {"emoji": "✅" if is_matched else "❌"}
                                },
                            },
                        ],
                    )
                    print(f"[Verification] Added note block instead of PDF")

                self.send_json_response(200, {"success": True})
                print(f"[Verification] Update completed successfully\n")

            except Exception as e:
                print(f"[Verification] Notion update failed: {e}")
                import traceback
                traceback.print_exc()
                self.send_json_response(500, {"success": False, "error": str(e)})

        except Exception as e:
            print(f"[Verification] Request processing failed: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response(500, {"success": False, "error": str(e)})

    def send_json_response(self, status, data):
        """JSONレスポンスを送信"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))

    def log_message(self, format, *args):
        """ログメッセージをカスタマイズ"""
        if self.path.startswith('/api/'):
            print(f"[API] {self.command} {self.path} - {args[1]}")
        else:
            print(f"[File] {self.command} {self.path}")


def main():
    """テストサーバーを起動"""
    port = 8000

    print("=" * 60)
    print(">> Test Server Starting...")
    print("=" * 60)
    print(f"URL: http://localhost:{port}")
    print(f"Document Root: public/")
    print(f"API: /api/parse_daily_report")
    print()
    print("Fixed:")
    print("  1. Added 'data' key in response")
    print("  2. Added data.previous_difference field")
    print("  3. Notion save is skipped (test mode)")
    print()
    print("Test Steps:")
    print(f"  1. Open http://localhost:{port} in browser")
    print("  2. Upload PDF file")
    print("  3. Check if data is displayed correctly")
    print("  4. Check if 'previous_difference' is shown")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    try:
        server = HTTPServer(('localhost', port), TestServerHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[INFO] Server stopped")
        sys.exit(0)


if __name__ == '__main__':
    main()
