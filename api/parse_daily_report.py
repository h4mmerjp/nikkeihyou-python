from http.server import BaseHTTPRequestHandler
import pdfplumber
import json
import io
import re
import os
import cgi
from datetime import datetime
from collections import defaultdict
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
# ヘルパー関数
# ====================
def safe_int(val):
    """空・None・カンマ付き文字列を安全にintへ"""
    if val is None or str(val).strip() == '':
        return 0
    # 改行・カンマ・スペース除去してint変換
    cleaned = str(val).replace(',', '').replace('\n', '').strip()
    try:
        return int(cleaned)
    except ValueError:
        return 0


def parse_row(row):
    """テーブルの1行をパースして辞書を返す"""
    # 氏名セル: "No.11378\n松本　正和" or "No.11378\n松本　正和\n再初診"
    name_cell = row[1] or ''
    no_match = re.search(r'No\.(\d+)', name_cell)
    patient_no = no_match.group(1) if no_match else ''
    name_lines = [l.strip() for l in name_cell.split('\n')
                  if not l.strip().startswith('No.') and l.strip()]
    # "再初診" "新患" などの修飾語を除外して氏名だけ取る
    modifiers = {'再初診', '新患'}
    name = ' '.join(l for l in name_lines if l not in modifiers).strip()

    # 負担額セル: "30%\n6,520" → %と金額を分離
    futan_cell = row[4] or ''
    futan_parts = futan_cell.split('\n')
    futan_ratio = futan_parts[0].strip() if len(futan_parts) >= 1 else ''
    futan_amount = safe_int(futan_parts[1]) if len(futan_parts) >= 2 else 0

    return {
        'number': int(row[0]),
        'patient_no': patient_no,
        'name': name,
        'insurance_type': (row[2] or '').strip(),
        'points': safe_int(row[3]),
        'ratio': futan_ratio,
        'futan_amount': futan_amount,
        'kaigo_units': safe_int(row[5]),
        'kaigo_amount': safe_int(row[6]),
        'jihi': safe_int(row[7]),
        'buppan': safe_int(row[8]),
        'previous_diff': safe_int(row[9]),
        'receipt_amount': safe_int(row[10]),
        'diff': safe_int(row[11]),
    }


def classify_insurance(ins_type):
    """保険種別を4分類に正規化"""
    if '社' in ins_type:
        return '社保'
    elif '国' in ins_type:
        return '国保'
    elif '後期' in ins_type:
        return '後期'
    elif '保険なし' in ins_type:
        return '保険なし'
    return 'その他'


# ====================
# PDF 解析（extract_table ベース）
# ====================
def parse_pdf(pdf_file):
    """PDF から日付・個別行データ・集計データを抽出

    extract_table() を使用し、空セルも None として保持するため
    前回差額・自費・物販・介護など空欄が多い列も正確にマッピングできる。
    """
    with pdfplumber.open(pdf_file) as pdf:
        # --- 日付（1ページ目のテキストから） ---
        first_text = pdf.pages[0].extract_text() or ""
        date_match = re.search(r"令和\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日", first_text)
        if date_match:
            year = int(date_match.group(1)) + 2018
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            date_str = f"{year}-{month:02d}-{day:02d}"
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # --- 全ページからテーブル行を抽出 ---
        all_rows = []
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table:
                # 番号列が数字の行のみ（ヘッダー・合計行を除外）
                if row[0] and row[0].strip().isdigit():
                    parsed = parse_row(row)
                    if parsed:
                        all_rows.append(parsed)

        # --- 個別行データから集計を算出 ---
        cat_summary = defaultdict(lambda: {"count": 0, "points": 0, "amount": 0})

        total_receipt = 0
        total_jihi = 0
        total_buppan = 0
        total_kaigo = 0
        total_previous_diff = 0

        for r in all_rows:
            cat = classify_insurance(r['insurance_type'])
            if cat != 'その他':
                cat_summary[cat]["count"] += 1
                cat_summary[cat]["points"] += r['points']
                cat_summary[cat]["amount"] += r['futan_amount']
            total_receipt += r['receipt_amount']
            total_jihi += r['jihi']
            total_buppan += r['buppan']
            total_kaigo += r['kaigo_amount']
            total_previous_diff += r['previous_diff']

        # 保険合計
        insurance_total_count = sum(v["count"] for v in cat_summary.values())
        insurance_total_amount = sum(v["amount"] for v in cat_summary.values())

        summary = {
            "date": date_str,
            "rows": all_rows,
            "shaho_count": cat_summary["社保"]["count"],
            "shaho_points": cat_summary["社保"]["points"],
            "shaho_amount": cat_summary["社保"]["amount"],
            "kokuho_count": cat_summary["国保"]["count"],
            "kokuho_points": cat_summary["国保"]["points"],
            "kokuho_amount": cat_summary["国保"]["amount"],
            "kouki_count": cat_summary["後期"]["count"],
            "kouki_points": cat_summary["後期"]["points"],
            "kouki_amount": cat_summary["後期"]["amount"],
            "hoken_nashi_count": cat_summary["保険なし"]["count"],
            "hoken_nashi_points": cat_summary["保険なし"]["points"],
            "hoken_nashi_amount": cat_summary["保険なし"]["amount"],
            "total_count": len(all_rows),
            "insurance_total_count": insurance_total_count,
            "total_amount": insurance_total_amount,
            "total_receipt": total_receipt,
            "jihi_amount": total_jihi,
            "buppan_amount": total_buppan,
            "kaigo_amount": total_kaigo,
            "previous_diff": total_previous_diff,
        }

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
            "保険なし人数": {"number": summary["hoken_nashi_count"]},
            "保険なし金額": {"number": summary["hoken_nashi_amount"]},
            "合計人数": {"number": summary["total_count"]},
            "合計金額": {"number": summary["total_amount"]},
            "物販": {"number": summary["buppan_amount"]},
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
