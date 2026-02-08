# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2025-02-07

### Added
- 個別患者データの抽出機能
  - 番号、患者ID、氏名、保険種別、点数、負担額
  - 介護単位、介護負担額、自費、物販
  - 前回差額、領収額、差額、備考
- テーブル抽出方式（`pdfplumber.extract_table()`）を採用
- 複数行セルの処理機能
- コマンドライン引数でPDFファイル指定可能（`scripts/inspect_pdf.py`）
- テストスクリプトのオプション（`--all`, `--no-text`）
- 自動インストールスクリプト（`install_dependencies.bat`/`.sh`）
- 環境確認スクリプト（`check_python.bat`）
- 包括的なドキュメント
  - `README.md` - プロジェクト概要
  - `INSTALL_GUIDE.md` - インストールガイド
  - `TESTING.md` - テスト方法
  - `API.md` - API仕様
  - `CHANGELOG.md` - このファイル

### Changed
- APIレスポンス構造を変更
  - `summary` と `patients` に分離
  - 後方互換性なし（破壊的変更）
- PDF解析方式を `extract_text()` から `extract_table()` に変更
- `tests/test_real_pdf.py` を新しいデータ構造に対応

### Fixed
- 空欄を含むPDFでの列位置ずれの問題
- 複数行テキストを含むセルの処理

### Technical Details

#### PDF解析方式の変更

**変更前:**
- `extract_text()` でテキスト抽出
- 正規表現で集計データのみを抽出

**変更後:**
- `extract_table()` でテーブルデータを抽出
- 各行から個別患者データをパース
- 集計データも引き続き抽出

#### データ構造の変更

**変更前:**
```json
{
  "date": "2025-05-31",
  "shaho_count": 42,
  "shaho_amount": 130500,
  ...
}
```

**変更後:**
```json
{
  "summary": {
    "date": "2025-05-31",
    "shaho_count": 42,
    "shaho_amount": 130500,
    ...
  },
  "patients": [
    {
      "number": 1,
      "patient_id": "No.11378",
      "name": "松本　正和",
      ...
    }
  ]
}
```

#### APIレスポンスの変更

**変更前:**
```json
{
  "success": true,
  "data": { ... },
  "notion_page_id": "xxxx"
}
```

**変更後:**
```json
{
  "success": true,
  "summary": { ... },
  "patients": [ ... ],
  "notion_page_id": "xxxx"
}
```

## [1.0.0] - 2025-01-XX

### Added
- 初期リリース
- 日計表PDFから集計データを抽出
- Notion APIとの連携
- Vercel Serverless Functionsでのデプロイ
- 基本的なテスト（`tests/test_parse_pdf.py`, `tests/test_real_pdf.py`）

### Features
- 日付抽出（令和から西暦に変換）
- 保険区分別の集計
  - 社保（人数・金額）
  - 国保（人数・金額）
  - 後期（人数・金額）
  - 保険なし（人数・金額）
- 合計人数・金額
- 自費金額
- 物販金額
- 介護金額
- 前回差額
- Notionデータベースへの保存
- PDFファイルの添付

## Migration Guide (v1.0 → v2.0)

### Breaking Changes

v2.0では、APIレスポンスの構造が変更されました。既存のコードを更新する必要があります。

#### 変更前（v1.0）

```javascript
const data = await response.json();
console.log(data.date);           // "2025-05-31"
console.log(data.total_count);    // 55
console.log(data.total_amount);   // 150000
```

#### 変更後（v2.0）

```javascript
const data = await response.json();
console.log(data.summary.date);          // "2025-05-31"
console.log(data.summary.total_count);   // 55
console.log(data.summary.total_amount);  // 150000

// 新機能: 個別患者データ
console.log(data.patients.length);       // 52
console.log(data.patients[0].name);      // "松本　正和"
```

### 移行手順

1. **APIレスポンスの構造を更新**
   ```javascript
   // 変更前
   const { date, total_count } = data;

   // 変更後
   const { summary, patients } = data;
   const { date, total_count } = summary;
   ```

2. **個別患者データの活用**
   ```javascript
   // 新機能: 患者一覧の表示
   patients.forEach(patient => {
     console.log(`${patient.name}: ¥${patient.receipt_amount}`);
   });
   ```

3. **テストコードの更新**
   - `tests/test_parse_pdf.py` のモックを更新（未対応）
   - `tests/test_real_pdf.py` は既に対応済み

## [Unreleased]

### TODO
- `tests/test_parse_pdf.py` を新しい構造に対応
- 個別患者データのNotion保存機能
- エラーハンドリングの改善
- パフォーマンスの最適化
- CI/CDパイプラインの構築

---

## Notes

### Versioning
このプロジェクトは [Semantic Versioning](https://semver.org/) を使用しています。

- MAJOR: 破壊的変更
- MINOR: 後方互換性のある機能追加
- PATCH: 後方互換性のあるバグ修正

### Links
- [README](README.md)
- [API Documentation](API.md)
- [Testing Guide](TESTING.md)
- [Installation Guide](INSTALL_GUIDE.md)
