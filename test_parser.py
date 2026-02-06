"""
PDF解析の単体テスト
使い方: python test_parser.py <PDFファイルパス>

Notion不要。pdfplumberのみ必要。
  pip install pdfplumber
"""
import sys
import json
import io
import re
import pdfplumber
from datetime import datetime


def parse_pdf(pdf_file):
    """PDF から日付と集計データを抽出"""
    with pdfplumber.open(pdf_file) as pdf:
        # --- 全ページのテキストを表示（デバッグ用） ---
        print(f"=== PDF情報: {len(pdf.pages)}ページ ===\n")

        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            print(f"--- ページ {i+1} ---")
            print(text)
            print()

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
            print("[WARNING] 日付パターンが見つかりませんでした。今日の日付を使用します。")

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
                print(f"[MATCH] {key}: 人数={m.group(1)}, 金額={m.group(2)}")
            else:
                print(f"[MISS]  {key}: パターンにマッチしませんでした")

        # 合計
        total_m = re.search(r"合計\s+(\d+)\s+[\d,]+\s+([\d,]+)", last_text)
        if total_m:
            summary["total_count"] = int(total_m.group(1))
            summary["total_amount"] = int(total_m.group(2).replace(",", ""))
            print(f"[MATCH] 合計: 人数={total_m.group(1)}, 金額={total_m.group(2)}")
        else:
            print("[MISS]  合計: パターンにマッチしませんでした")

        # 自費
        jihi_m = re.search(r"自費\s+([\d,]+)", last_text)
        if jihi_m:
            summary["jihi_amount"] = int(jihi_m.group(1).replace(",", ""))
            print(f"[MATCH] 自費: 金額={jihi_m.group(1)}")
        else:
            print("[MISS]  自費: パターンにマッチしませんでした")

        # 物販
        bushan_m = re.search(r"物販合計\s+([\d,]+)", last_text)
        if bushan_m:
            summary["bushan_amount"] = int(bushan_m.group(1).replace(",", ""))
            print(f"[MATCH] 物販: 金額={bushan_m.group(1)}")
        else:
            print("[MISS]  物販: パターンにマッチしませんでした")

        # 介護
        kaigo_m = re.search(r"介護.*?([\d,]+)", last_text)
        if kaigo_m:
            summary["kaigo_amount"] = int(kaigo_m.group(1).replace(",", ""))
            print(f"[MATCH] 介護: 金額={kaigo_m.group(1)}")
        else:
            print("[MISS]  介護: パターンにマッチしませんでした")

        return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python test_parser.py <PDFファイルパス>")
        print("例:     python test_parser.py ~/Downloads/日計表_20250531.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    print(f"PDF解析開始: {pdf_path}\n")

    result = parse_pdf(pdf_path)

    print("\n=== 抽出結果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
