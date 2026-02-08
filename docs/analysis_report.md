# 日計表システム データフロー分析レポート

## 🔴 致命的なバグ

### 1. APIレスポンスとフロントエンドのキー不一致

**バックエンド** (`parse_daily_report.py` L53-58) が返すJSON:
```json
{
  "success": true,
  "summary": { ... },
  "patients": [ ... ],
  "notion_page_id": "xxx"
}
```

**フロントエンド** (`index.html` uploadPDF関数内) が期待するJSON:
```javascript
if (result.success && result.data) {       // ← "data" を参照
    populateFormWithExtractedData(result.data);  // ← result.data を渡す
    window.notionPageId = result.notion_page_id;
```

**問題**: バックエンドは `summary` と `patients` を返すが、フロントは `result.data` を参照している。`result.data` は `undefined` なので `if` 条件が false になり、**データが一切表示されない**。

**修正方法** (どちらか一つ):

**案A: バックエンド修正** (推奨)
```python
# parse_daily_report.py L53-58
result = {
    "success": True,
    "data": parsed_data["summary"],  # "summary" → "data" に変更
    "patients": parsed_data["patients"],
    "notion_page_id": notion_page_id,
}
```

**案B: フロントエンド修正**
```javascript
if (result.success && result.summary) {
    populateFormWithExtractedData(result.summary);
```

---

### 2. 前回差額 (zenkai_sagaku) がフロントに渡されない

バックエンドは `summary.zenkai_sagaku = -700` を出力するが、フロントエンドの `populateFormWithExtractedData(data)` は `data.previous_difference` を参照している。

**フロントの該当コード:**
```javascript
if (data.previous_difference) {
    // 前回差額を入力
}
```

**バックエンドが返すキー名**: `zenkai_sagaku`

**修正方法**: バックエンド側で `data` に `previous_difference` フィールドを追加:
```python
summary["previous_difference"] = summary["zenkai_sagaku"]
```
※マイナスの場合は `-700` のように符号付き整数で返す。フロントはすでに符号処理のロジックを持っている。

---

## 🟡 中程度の問題

### 3. `total_amount` が合計行の**全体合計**の負担額を取得

2つの「合計」行が存在:
- `合計 55 53,309 150,000 ...` (全患者合計 - 負担額=150,000)
- `合計 51 52,303 139,940` (保険内患者合計 - 負担額=139,940)

`re.search()` は最初のマッチを返すので `total_count=55, total_amount=150,000` が取得される。これは全体合計なので意味的には正しいが、**フロントエンドでの照合用途によっては確認が必要**。

現在のフロントエンドは `total_count` / `total_amount` を直接表示しないので実害なし。

### 4. `jihi_count` が常に 0

バックエンドには `jihi_count` を設定するロジックがない。PDFの集計部分にも自費の人数行は独立して存在しないため、個別患者データから自費患者数をカウントするか、初期値0のまま許容するか判断が必要。

フロントの `jihiCount` フィールドには 0 が入力されるが、もし自費患者数を正確に入力したい場合は patients 配列から保険なしをカウントする必要がある。

### 5. `today_difference` (当日差額) のフィールドが未定義

フロントエンドは `data.today_difference` も処理するが、バックエンドの summary にはこのフィールドが存在しない。当日差額はPDFの日計表には含まれない（印刷時点では不明）ので、これは手入力の想定で問題ない。ただし `data.today_difference !== undefined` のチェックで `undefined` になるため、条件分岐でスキップされ、実害なし。

---

## 🟢 Notion保存機能の分析

### save_to_notion の問題点

#### 6. File Upload API のバージョン依存
```python
NOTION_VERSION = "2025-05-20"
```
Notion File Upload API は `2025-05-20` バージョンが必要だが、`notion_client` ライブラリのデフォルトバージョンとの不整合が起きる可能性がある。`notion_uploader.py` は直接 `requests` を使っているので、ヘッダーに `Notion-Version: 2025-05-20` を正しく設定しており、この部分は問題ない。

ただし、`notion = Client(auth=...)` のインスタンスは `notion-client` ライブラリのデフォルトバージョンを使う。ページ作成(`pages.create`) やブロック追加(`blocks.children.append`)時にFile Uploadブロックを使う場合、ライブラリバージョンが古いとエラーになる可能性がある。

**推奨**: `Client(auth=..., notion_version="2025-05-20")` で明示指定。

#### 7. Notion保存のプロパティマッピング（問題なし）

| summary キー | Notion プロパティ | 値 (このPDF) | 検証 |
|---|---|---|---|
| date | 日付 | 2025-05-31 | ✅ |
| shaho_count | 社保人数 | 42 | ✅ |
| shaho_amount | 社保金額 | 130,500 | ✅ |
| kokuho_count | 国保人数 | 4 | ✅ |
| kokuho_amount | 国保金額 | 6,050 | ✅ |
| kouki_count | 後期人数 | 5 | ✅ |
| kouki_amount | 後期金額 | 3,390 | ✅ |
| jihi_count | 自費人数 | 0 | ⚠️ 常に0 |
| jihi_amount | 自費金額 | 3,850 | ✅ |
| hoken_nashi_count | 保険なし人数 | 1 | ✅ |
| hoken_nashi_amount | 保険なし金額 | 10,060 | ✅ |
| total_count | 合計人数 | 55 | ✅ |
| total_amount | 合計金額 | 150,000 | ✅ |
| bushan_amount | 物販 | 1,560 | ✅ |
| kaigo_amount | 介護 | 0 | ✅ |
| zenkai_sagaku | 前回差額 | -700 | ✅ |

### update_verification.py (照合結果保存)

照合結果保存のフローに問題なし:
- フロントからのPDF Base64受信 → デコード → Notion Upload → ページ更新 → ブロック追加
- `照合状態` プロパティを「一致」/「不一致」で更新
- 照合画面PDFをブロックとして追加

---

## 修正コードの提案

### parse_daily_report.py の修正箇所

```python
# L53-58: レスポンス構造を修正
result = {
    "success": True,
    "data": {
        **parsed_data["summary"],
        "previous_difference": parsed_data["summary"].get("zenkai_sagaku", 0),
    },
    "patients": parsed_data["patients"],
    "notion_page_id": notion_page_id,
}
```

この1箇所の修正で Issue #1 と #2 が同時に解決される。
