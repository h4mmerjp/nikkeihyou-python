# テストガイド

このドキュメントでは、PDF解析システムのテスト方法を詳しく説明します。

## 📋 目次

1. [簡易テスト](#簡易テスト)
2. [PDFファイルの指定](#pdfファイルの指定)
3. [オプション](#オプション)
4. [正式なテスト](#正式なテスト)
5. [ローカルAPIサーバー](#ローカルapiサーバー)
6. [テストの種類](#テストの種類)
7. [トラブルシューティング](#トラブルシューティング)

## 簡易テスト

### 最も簡単な方法

#### Windows

```cmd
# バッチファイルをダブルクリック
scriptsun_test.bat

# または、コマンドプロンプトで
python scripts\inspect_pdf.py
```

#### Mac/Linux

```bash
# シェルスクリプトを実行
scripts/run_test.sh

# または、直接実行
python scripts/inspect_pdf.py
```

### 期待される出力

```
============================================================
PDFファイル: total_d.pdf
フルパス: C:\Users\...\total_d.pdf
============================================================

[集計データ]
  date: 2025-05-31
  shaho_count: 42
  shaho_amount: 130500
  total_count: 55
  total_amount: 150000
  zenkai_sagaku: -700
  ...

[個別患者データ] 件数: 52
  患者 1:
    number: 1
    patient_id: No.11378
    name: 松本　正和
    insurance_type: 社本
    points: 2174
    burden_amount: 6520
    zenkai_sagaku: 0
    receipt_amount: 6520
    ...
```

## PDFファイルの指定

### デフォルトファイル（total_d.pdf）を使用

```bash
# Windows
python scripts\inspect_pdf.py

# Mac/Linux
python scripts/inspect_pdf.py
```

### 別のファイルを指定

```bash
# Windows - 相対パス
python scripts\inspect_pdf.py my_report.pdf

# Windows - 絶対パス
python scripts\inspect_pdf.py C:\Users\user\Documents\日計表_2025-01-15.pdf

# Mac/Linux - 相対パス
python scripts/inspect_pdf.py my_report.pdf

# Mac/Linux - 絶対パス
python scripts/inspect_pdf.py /Users/user/Documents/日計表_2025-01-15.pdf
```

### バッチファイル/シェルスクリプトで指定

```bash
# Windows
scriptsun_test.bat                        # デフォルト
scriptsun_test.bat my_report.pdf          # ファイル指定
scriptsun_test.bat C:\path\to\report.pdf  # 絶対パス

# Mac/Linux
scripts/run_test.sh                       # デフォルト
scripts/run_test.sh my_report.pdf         # ファイル指定
scripts/run_test.sh /path/to/report.pdf   # 絶対パス
```

### パスの指定方法

#### 相対パス

```bash
# カレントディレクトリのファイル
python scripts/inspect_pdf.py report.pdf

# サブディレクトリのファイル
python scripts/inspect_pdf.py data/reports/report_2025.pdf

# 親ディレクトリのファイル
python scripts/inspect_pdf.py ../other_folder/report.pdf
```

#### 絶対パス

```bash
# Windows
python scripts\inspect_pdf.py C:\Users\user\Documents\report.pdf

# Mac/Linux
python scripts/inspect_pdf.py /Users/user/Documents/report.pdf
```

#### スペースを含むパス

```bash
# Windows
python scripts\inspect_pdf.py "C:\Users\user\My Documents\report.pdf"

# Mac/Linux
python scripts/inspect_pdf.py "/Users/user/My Documents/report.pdf"
```

## オプション

### --all : すべての患者データを表示

デフォルトでは最初の5件のみ表示されます。

```bash
python scripts/inspect_pdf.py --all my_report.pdf
```

### --no-text : テキスト抽出結果を非表示

結果のみを表示します（デバッグ情報を省略）。

```bash
python scripts/inspect_pdf.py --no-text my_report.pdf
```

### オプションの組み合わせ

```bash
python scripts/inspect_pdf.py --no-text --all my_report.pdf
```

### --help : ヘルプを表示

```bash
python scripts/inspect_pdf.py --help
```

出力例:
```
usage: inspect_pdf.py [-h] [--no-text] [--all] [pdf_file]

PDFファイルからデータを抽出してテストします

positional arguments:
  pdf_file    テストするPDFファイルのパス（省略時は total_d.pdf）

optional arguments:
  -h, --help  show this help message and exit
  --no-text   テキスト抽出結果を表示しない（結果のみ表示）
  --all       すべての患者データを表示（デフォルトは最初の5件のみ）
```

## 実例

### ケース1: デフォルトファイルで簡易テスト

```bash
python scripts/inspect_pdf.py --no-text
```

結果のみを表示（テキスト抽出結果は非表示）

### ケース2: 別のファイルですべてのデータを確認

```bash
python scripts/inspect_pdf.py --all 日計表_2025-02-01.pdf
```

指定したPDFのすべての患者データを表示

### ケース3: 複数のファイルを一括テスト

```bash
# Windows
for %f in (*.pdf) do python scripts\inspect_pdf.py --no-text %f

# Mac/Linux
for f in *.pdf; do python scripts/inspect_pdf.py --no-text "$f"; done
```

カレントディレクトリのすべてのPDFファイルをテスト

## 正式なテスト

### pytestを使ったテスト

#### インストール

```bash
python -m pip install pytest
```

#### すべてのテストを実行

```bash
pytest tests/ -v
```

#### 特定のテストファイルのみ実行

```bash
# 実際のPDFを使ったテスト
pytest tests/test_real_pdf.py -v

# ユニットテスト（モック使用）
pytest tests/test_parse_pdf.py -v
```

#### テスト結果の詳細表示

```bash
pytest tests/ -v --tb=short
```

#### 特定のテストケースのみ実行

```bash
pytest tests/test_real_pdf.py::TestRealPdf::test_date_extraction -v
```

## ローカルAPIサーバー

### Vercel Devサーバーを起動

```bash
# サーバー起動
vercel dev
```

### curlでテスト

```bash
# デフォルトPDF
curl -X POST http://localhost:3000/api/parse_daily_report \
  -F "file=@total_d.pdf"

# 別のPDF
curl -X POST http://localhost:3000/api/parse_daily_report \
  -F "file=@/path/to/your/report.pdf"
```

### Postmanでテスト

1. Postmanを開く
2. リクエストタイプを `POST` に設定
3. URL: `http://localhost:3000/api/parse_daily_report`
4. Bodyタブで `form-data` を選択
5. Key: `file`, Type: `File`, Value: テストしたいPDFを選択
6. Sendをクリック

### Python requestsでテスト

```python
import requests

with open('my_report.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:3000/api/parse_daily_report',
        files=files
    )
    data = response.json()
    print(f"Success: {data['success']}")
    print(f"Total count: {data['summary']['total_count']}")
    print(f"Patients: {len(data['patients'])}")
```

### JavaScriptでテスト

```javascript
const formData = new FormData();
formData.append('file', pdfFile);

const response = await fetch('http://localhost:3000/api/parse_daily_report', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log('Summary:', data.summary);
console.log('Patients:', data.patients);
```

## テストの種類

### 1. ユニットテスト (`tests/test_parse_pdf.py`)

- モックを使用して各関数をテスト
- PDFファイル不要
- 高速実行
- 個別機能の検証

**注意**: 現在、新しいデータ構造（`summary`と`patients`）に未対応

### 2. 統合テスト (`tests/test_real_pdf.py`)

- 実際の `total_d.pdf` を使用
- エンドツーエンドのテスト
- より信頼性が高い
- 実際のデータでの検証

### 3. 手動テスト (`scripts/inspect_pdf.py`)

- デバッグ用
- 抽出結果を直接確認できる
- 開発中に便利
- カスタマイズ可能

## トラブルシューティング

### ファイルが見つからない

```
エラー: ファイルが見つかりません: /path/to/file.pdf
```

**対処法:**
1. ファイルパスが正しいか確認
2. ファイル名に誤字がないか確認
3. 絶対パスで指定してみる
4. ファイルの存在を確認: `ls` (Mac/Linux) または `dir` (Windows)

### PDF解析エラー

```
エラー: PDF解析に失敗しました
```

**対処法:**
1. PDFファイルが破損していないか確認
2. PDFが日計表の形式に合っているか確認
3. PDFが正しく開けるか確認（Adobe Readerなどで）
4. PDFのバージョンやエンコーディングを確認

### ModuleNotFoundError

```
ModuleNotFoundError: No module named 'pdfplumber'
```

**対処法:**
```bash
# 依存関係をインストール
python -m pip install -r requirements.txt

# または自動インストールスクリプト
scriptsinstall_dependencies.bat  # Windows
scripts/install_dependencies.sh # Mac/Linux
```

詳細は [INSTALL_GUIDE.md](INSTALL_GUIDE.md) を参照

### Python が見つからない

```
'python' は、内部コマンドまたは外部コマンドとして認識されていません
```

**対処法:**
1. Pythonがインストールされているか確認
2. `python3` を試す
3. [INSTALL_GUIDE.md](INSTALL_GUIDE.md) を参照

### テストデータの作成

新しいPDFでテストする場合：

```bash
# ファイルをプロジェクトルートにコピー
cp /path/to/your/pdf/日計表.pdf ./test_data.pdf

# テスト実行
python scripts/inspect_pdf.py test_data.pdf
```

## CI/CD

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: python -m pip install -r requirements.txt pytest
      - name: Run tests
        run: pytest tests/ -v
```

## パフォーマンステスト

### 大量のPDFをテスト

```bash
# Windows
for %f in (data\*.pdf) do @echo Testing %f && python scripts\inspect_pdf.py --no-text "%f"

# Mac/Linux
for f in data/*.pdf; do echo "Testing $f" && python scripts/inspect_pdf.py --no-text "$f"; done
```

### タイミング測定

```bash
# Windows
powershell "Measure-Command { python scripts\inspect_pdf.py }"

# Mac/Linux
time python scripts/inspect_pdf.py
```

## まとめ

### 最も簡単な方法

1. `scriptsun_test.bat` (Windows) または `scripts/run_test.sh` (Mac/Linux) をダブルクリック
2. 結果を確認

### 別のPDFでテストする場合

```bash
# Windows
python scripts\inspect_pdf.py your_file.pdf

# Mac/Linux
python scripts/inspect_pdf.py your_file.pdf
```

### 詳細なテスト

```bash
pytest tests/test_real_pdf.py -v
```

その他の質問は [README.md](README.md) または [INSTALL_GUIDE.md](INSTALL_GUIDE.md) を参照してください。
