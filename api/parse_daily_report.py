from http.server import BaseHTTPRequestHandler
import pdfplumber
import json
import io
import re
import os
from datetime import datetime
from notion_client import Client

from utils.notion_uploader import upload_file_to_notion

try:
    from multipart import parse_form_data
    HAS_MULTIPART = True
except ImportError:
    # フォールバック: 古いcgiモジュール（Python 3.12以前）
    try:
        import cgi
        HAS_CGI = True
        HAS_MULTIPART = False
    except ImportError:
        HAS_CGI = False
        HAS_MULTIPART = False

notion = Client(auth=os.environ["NOTION_TOKEN"], notion_version="2025-05-20")
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

            if HAS_MULTIPART:
                # python-multipart を使用（Python 3.13+）
                environ = {
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": content_type,
                    "CONTENT_LENGTH": str(content_length),
                }
                fields, files = parse_form_data(environ, io.BytesIO(body))

                if "file" not in files:
                    self._send_json(400, {"success": False, "error": "No file uploaded"})
                    return

                file_item = files["file"]
                pdf_bytes = file_item.raw

            elif HAS_CGI:
                # 古いcgiモジュールを使用（Python 3.12以前）
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

            else:
                self._send_json(500, {
                    "success": False,
                    "error": "No multipart parser available. Install python-multipart: pip install python-multipart"
                })
                return

            # 1. PDF 解析
            parsed_data = parse_pdf(io.BytesIO(pdf_bytes))

            # 2. Notion に保存
            notion_page_id = save_to_notion(pdf_bytes, parsed_data["summary"])

            # 3. レスポンス（個別データと集計データの両方を返す）
            # フロントエンドが期待する "data" キーに summary を格納し、
            # previous_difference フィールドも追加
            # 当日差額 = 個別患者の差額の合計
            today_difference = sum(patient.get("sagaku", 0) for patient in parsed_data["patients"])

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
    """PDF から日付、個別患者データ、集計データを抽出"""
    with pdfplumber.open(pdf_file) as pdf:
        # --- 日付 ---
        first_text = pdf.pages[0].extract_text() or ""
        date_match = re.search(r"令和\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日", first_text)
        if date_match:
            year = int(date_match.group(1)) + 2018
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            date_str = f"{year}-{month:02d}-{day:02d}"
        else:
            date_str = datetime.now().strftime("%Y-%m-%d")

        # --- 個別患者データ抽出 ---
        patients = []
        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                if not table or len(table) < 2:
                    continue

                # ヘッダー行をスキップ（1行目）
                for row in table[1:]:
                    if not row or len(row) < 2:
                        continue

                    # 空行や集計行をスキップ
                    first_col = (row[0] or "").strip()
                    if not first_col or first_col in ["合計", "訪問（再掲）", "社保", "国保", "後期", "保険なし", "10%対象", "8%対象", "物販合計"]:
                        continue

                    # 番号が数字でない場合はスキップ
                    if not first_col.isdigit():
                        continue

                    # 患者データをパース
                    patient = parse_patient_row(row)
                    if patient:
                        patients.append(patient)

        # --- 集計データ（全ページから検索） ---
        # 詳細な合計行は最終ページではなく途中のページにある可能性があるため、
        # 全ページのテキストを結合して検索する
        all_text = ""
        for page in pdf.pages:
            all_text += (page.extract_text() or "") + "\n"

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
            "zenkai_sagaku": 0,
        }

        patterns = {
            "shaho": r"社保\s+(\d+)\s+[\d,]+\s+([\d,]+)",
            "kokuho": r"国保\s+(\d+)\s+[\d,]+\s+([\d,]+)",
            "kouki": r"後期\s+(\d+)\s+[\d,]+\s+([\d,]+)",
            "hoken_nashi": r"保険なし\s+(\d+)\s+[\d,]+\s+([\d,]+)",
        }
        for key, pattern in patterns.items():
            matches = re.findall(pattern, all_text)
            if matches:
                last_match = matches[-1]
                summary[f"{key}_count"] = int(last_match[0])
                summary[f"{key}_amount"] = int(last_match[1].replace(",", ""))

        # 合計
        total_m = re.search(r"合計\s+(\d+)\s+[\d,]+\s+([\d,]+)", all_text)
        if total_m:
            summary["total_count"] = int(total_m.group(1))
            summary["total_amount"] = int(total_m.group(2).replace(",", ""))

        # 自費・前回差額（全体合計行から位置ベースで抽出）
        goukei_full_m = re.search(
            r"合計\s+(\d+)\s+([\d,]+)\s+([\d,]+)\s+(\d+)\s+(\d+)\s+([\d,]+)\s+([\d,]+)\s+(-?[\d,]+)\s+([\d,]+)\s+(-?\d+)",
            all_text,
        )
        if goukei_full_m:
            summary["jihi_amount"] = int(goukei_full_m.group(6).replace(",", ""))
            summary["zenkai_sagaku"] = int(goukei_full_m.group(8).replace(",", ""))
        else:
            jihi_m = re.search(r"自費\s+([\d,]+)", all_text)
            if jihi_m:
                summary["jihi_amount"] = int(jihi_m.group(1).replace(",", ""))

        # 物販
        bushan_m = re.search(r"物販合計\s+([\d,]+)", all_text)
        if bushan_m:
            summary["bushan_amount"] = int(bushan_m.group(1).replace(",", ""))

        # 介護
        kaigo_m = re.search(r"介護.*?([\d,]+)", all_text)
        if kaigo_m:
            summary["kaigo_amount"] = int(kaigo_m.group(1).replace(",", ""))

        return {
            "summary": summary,
            "patients": patients,
        }


def parse_patient_row(row):
    """テーブル行から患者データをパース"""
    try:
        def safe_int(value):
            """文字列を安全に整数に変換"""
            if value is None or value == "":
                return 0
            value = str(value).strip().replace(",", "").replace(" ", "").replace("\n", "")
            # マイナス記号を処理
            if value.startswith("-"):
                return -int(value[1:]) if value[1:].isdigit() else 0
            return int(value) if value.isdigit() else 0

        def safe_str(value):
            """文字列を安全に取得（改行を処理）"""
            if not value:
                return ""
            # 改行で分割して、空でない行を結合
            lines = [line.strip() for line in str(value).split("\n") if line.strip()]
            return " ".join(lines)

        def extract_multi_line_cell(value):
            """複数行のセルから各行を抽出"""
            if not value:
                return []
            return [line.strip() for line in str(value).split("\n") if line.strip()]

        # 1列目: 番号・患者ID・氏名が複数行で含まれる可能性がある
        first_col_lines = extract_multi_line_cell(row[0]) if len(row) > 0 else []

        # 番号を抽出（最初の数字のみの行）
        number = 0
        patient_id = ""
        name = ""

        for line in first_col_lines:
            if line.isdigit() and number == 0:
                number = int(line)
            elif line.startswith("No."):
                patient_id = line
            elif line and not line.isdigit() and not line.startswith("No."):
                name = line

        # 2列目: 氏名（1列目に氏名がない場合）
        if not name and len(row) > 1:
            second_col_lines = extract_multi_line_cell(row[1])
            for line in second_col_lines:
                if line.startswith("No.") and not patient_id:
                    patient_id = line
                elif line and not line.startswith("No."):
                    name = line if not name else name

        # 保険種別: 「再初診」などの複数行を処理
        insurance_type = safe_str(row[2]) if len(row) > 2 else ""

        # 点数（数値のみを抽出）
        points = safe_int(row[3]) if len(row) > 3 else 0

        # 負担額（「30%」などと「金額」が同じセルにある可能性）
        burden_col = extract_multi_line_cell(row[4]) if len(row) > 4 else []
        burden_amount = 0
        for line in burden_col:
            if line and line.replace(",", "").replace(" ", "").isdigit():
                burden_amount = safe_int(line)
                break

        # 介護単位
        kaigo_units = safe_int(row[5]) if len(row) > 5 else 0

        # 介護負担額
        kaigo_burden = safe_int(row[6]) if len(row) > 6 else 0

        # 自費
        jihi = safe_int(row[7]) if len(row) > 7 else 0

        # 物販
        bushan = safe_int(row[8]) if len(row) > 8 else 0

        # 前回差額
        zenkai_sagaku = safe_int(row[9]) if len(row) > 9 else 0

        # 領収額
        receipt_amount = safe_int(row[10]) if len(row) > 10 else 0

        # 差額
        sagaku = safe_int(row[11]) if len(row) > 11 else 0

        # 備考
        remarks = safe_str(row[12]) if len(row) > 12 else ""

        return {
            "number": number,
            "patient_id": patient_id,
            "name": name,
            "insurance_type": insurance_type,
            "points": points,
            "burden_amount": burden_amount,
            "kaigo_units": kaigo_units,
            "kaigo_burden": kaigo_burden,
            "jihi": jihi,
            "bushan": bushan,
            "zenkai_sagaku": zenkai_sagaku,
            "receipt_amount": receipt_amount,
            "sagaku": sagaku,
            "remarks": remarks,
        }
    except Exception as e:
        print(f"Warning: Failed to parse patient row: {e}")
        return None


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
            "前回差額": {"number": summary["zenkai_sagaku"]},
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
