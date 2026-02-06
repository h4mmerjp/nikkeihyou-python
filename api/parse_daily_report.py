from http.server import BaseHTTPRequestHandler
import pdfplumber
import json
import io
import re
import os
import cgi
from datetime import datetime
from notion_client import Client

from utils.notion_uploader import upload_file_to_notion

notion = Client(auth=os.environ["NOTION_TOKEN"])
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        try:
            # --- multipart からファイル取得 ---
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            environ = {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": str(content_length),
            }
            fs = cgi.FieldStorage(
                fp=io.BytesIO(body),
                environ=environ,
                keep_blank_values=True,
            )

            file_item = fs["file"]
            if file_item.file is None:
                self._send_json(400, {"success": False, "error": "No file uploaded"})
                return

            pdf_bytes = file_item.file.read()

            # 1. PDF 解析
            summary = parse_pdf(io.BytesIO(pdf_bytes))

            # 2. Notion に保存
            notion_page_id = save_to_notion(pdf_bytes, summary)

            # 3. レスポンス
            result = {
                "success": True,
                "data": summary,
                "notion_page_id": notion_page_id,
            }
            self._send_json(200, result)

        except Exception as e:
            self._send_json(500, {"success": False, "error": str(e)})

    # --- helpers ---
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


# ====================
# PDF 解析
# ====================
def parse_pdf(pdf_file):
    """PDF から日付と集計データを抽出"""
    with pdfplumber.open(pdf_file) as pdf:
        # --- 日付 ---
        first_text = pdf.pages[0].extract_text() or ""
        # スペース許容の日付パターン
        date_match = re.search(r"令和\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日", first_text)
        if date_match:
            year = int(date_match.group(1)) + 2018
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            date_str = f"{year}-{month:02d}-{day:02d}"
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # --- 集計（最終ページ） ---
        last_text = pdf.pages[-1].extract_text() or ""

        summary = {
            "date": date_str,
            "shaho_count": 0,
            "shaho_amount": 0,
            "kokuho_count": 0,
            "kokuho_amount": 0,
            "kouki_count": 0,
            "kouki_amount": 0,
            "jihi_count": 0,
            "jihi_amount": 0,
            "hoken_nashi_count": 0,
            "hoken_nashi_amount": 0,
            "total_count": 0,
            "total_amount": 0,
            "bushan_amount": 0,
            "kaigo_amount": 0,
        }

        patterns = {
            "shaho": r"社保\s+(\d+)\s+[\d,]+\s+([\d,]+)",
            "kokuho": r"国保\s+(\d+)\s+[\d,]+\s+([\d,]+)",
            "kouki": r"後期\s+(\d+)\s+[\d,]+\s+([\d,]+)",
            "hoken_nashi": r"保険なし\s+(\d+)\s+[\d,]+\s+([\d,]+)",
        }
        for key, pattern in patterns.items():
            m = re.search(pattern, last_text)
            if m:
                summary[f"{key}_count"] = int(m.group(1))
                summary[f"{key}_amount"] = int(m.group(2).replace(",", ""))

        # 合計
        total_m = re.search(r"合計\s+(\d+)\s+[\d,]+\s+([\d,]+)", last_text)
        if total_m:
            summary["total_count"] = int(total_m.group(1))
            summary["total_amount"] = int(total_m.group(2).replace(",", ""))

        # 自費（全体合計行付近に「自費 金額」の形式で存在）
        jihi_m = re.search(r"自費\s+([\d,]+)", last_text)
        if jihi_m:
            summary["jihi_amount"] = int(jihi_m.group(1).replace(",", ""))

        # 物販
        bushan_m = re.search(r"物販合計\s+([\d,]+)", last_text)
        if bushan_m:
            summary["bushan_amount"] = int(bushan_m.group(1).replace(",", ""))

        # 介護
        kaigo_m = re.search(r"介護.*?([\d,]+)", last_text)
        if kaigo_m:
            summary["kaigo_amount"] = int(kaigo_m.group(1).replace(",", "")))

        return summary


# ====================
# Notion 保存
# ====================
def save_to_notion(pdf_bytes, summary):
    """Notion に PDF & 集計データを保存"""

    # 1. PDF アップロード
    pdf_filename = f"日計表_{summary['date']}.pdf"
    file_upload_id = upload_file_to_notion(pdf_bytes, pdf_filename, "application/pdf")

    # 2. ページ作成
    page = notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties={
            "日付": {"date": {"start": summary["date"]}},
            "社保人数": {"number": summary["shaho_count"]},
            "社保金額": {"number": summary["shaho_amount"]},
            "国保人数": {"number": summary["kokuho_count"]},
            "国保金額": {"number": summary["kokuho_amount"]},
            "後期人数": {"number": summary["kouki_count"]},
            "後期金額": {"number": summary["kouki_amount"]},
            "自費人数": {"number": summary["jihi_count"]},
            "自費金額": {"number": summary["jihi_amount"]},
            "保険なし人数": {"number": summary["hoken_nashi_count"]},
            "保険なし金額": {"number": summary["hoken_nashi_amount"]},
            "合計人数": {"number": summary["total_count"]},
            "合計金額": {"number": summary["total_amount"]},
            "物販": {"number": summary["bushan_amount"]},
            "介護": {"number": summary["kaigo_amount"]},
            "照合状態": {"select": {"name": "未照合"}},
        },
    )
    page_id = page["id"]

    # 3. PDF をページ内ブロックとして添付
    notion.blocks.children.append(
        block_id=page_id,
        children=[
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "📄 日計表PDF"}}
                    ]
                },
            },
            {
                "object": "block",
                "type": "file",
                "file": {
                    "type": "file_upload",
                    "file_upload": {"id": file_upload_id},
                    "caption": [
                        {"type": "text", "text": {"content": "元の日計表"}}
                    ],
                },
            },
        ],
    )

    return page_id
