# nikkeihyou-python

日計表PDFから個別患者データと集計データを抽出し、Notionに保存するシステム

## ✨ 機能

- **個別患者データの抽出**: 番号、患者ID、氏名、保険種別、点数、負担額、前回差額など
- **集計データの抽出**: 社保、国保、後期、保険なし、合計、物販、介護、前回差額
- **Notion連携**: データベースへの自動保存とPDF添付
- **テーブル抽出**: 空欄があっても正確に抽出可能
- **API提供**: Vercel Serverless Functions

## 🚀 クイックスタート

### 1. 環境確認

```cmd
# Python環境を確認
scripts\check_python.bat
```

### 2. 依存関係のインストール

```cmd
# 自動インストール（推奨）
scripts\install_dependencies.bat
```

または手動で：
```cmd
python -m pip install -r requirements.txt
```

### 3. テスト実行

```cmd
# デフォルトPDF（total_d.pdf）でテスト
scripts\run_test.bat

# 別のPDFファイルでテスト
scripts\run_test.bat my_report.pdf
```

または：
```cmd
python scripts\inspect_pdf.py
python scripts\inspect_pdf.py my_report.pdf
```

## 📦 インストール

詳細は **[INSTALL_GUIDE.md](docs/INSTALL_GUIDE.md)** を参照してください。

### 基本的なインストール

```bash
# 依存関係をインストール
python -m pip install -r requirements.txt

# 環境変数を設定（.envファイルを作成）
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id
```

### よくある問題

- **「pip が見つかりません」**: `python -m pip` を使用
- **「Python が見つかりません」**: Pythonをインストール（「Add to PATH」にチェック）
- **モジュールエラー**: `install_dependencies.bat` を実行

詳細なトラブルシューティングは [INSTALL_GUIDE.md](docs/INSTALL_GUIDE.md) へ

## 🧪 テスト

### 簡易テスト

```bash
# Windows
python scripts\inspect_pdf.py [PDF_FILE]

# Mac/Linux
python scripts/inspect_pdf.py [PDF_FILE]
```

### オプション

```bash
# すべての患者データを表示
python scripts\inspect_pdf.py --all my_report.pdf

# テキスト抽出を非表示
python scripts\inspect_pdf.py --no-text my_report.pdf

# ヘルプ表示
python scripts\inspect_pdf.py --help
```

### 正式なテスト

```bash
# pytestをインストール
pip install pytest

# テスト実行
pytest tests/test_real_pdf.py -v
```

詳細は **[TESTING.md](docs/TESTING.md)** を参照してください。

## 🌐 ローカルAPIサーバー

```bash
# サーバー起動
vercel dev

# テスト
curl -X POST http://localhost:3000/api/parse_daily_report \
  -F "file=@total_d.pdf"
```

## 📊 APIレスポンス

```json
{
  "success": true,
  "summary": {
    "date": "2025-05-31",
    "total_count": 55,
    "total_amount": 150000,
    "zenkai_sagaku": -700,
    ...
  },
  "patients": [
    {
      "number": 1,
      "patient_id": "No.11378",
      "name": "松本　正和",
      "points": 2174,
      "burden_amount": 6520,
      "zenkai_sagaku": 0,
      ...
    }
  ],
  "notion_page_id": "xxxx-xxxx-xxxx-xxxx"
}
```

詳細は **[API.md](docs/API.md)** を参照してください。

## 🚢 デプロイ

```bash
# Vercelにデプロイ
vercel --prod

# 環境変数を設定
vercel env add NOTION_TOKEN
vercel env add NOTION_DATABASE_ID
```

## 📁 プロジェクト構造

```
nikkeihyou-python/
├── api/
│   ├── parse_daily_report.py       # メインAPIハンドラ
│   ├── update_verification.py      # 照合結果更新API
│   └── utils/
│       └── notion_uploader.py      # Notion API連携
├── public/
│   └── index.html                  # フロントエンド
├── scripts/
│   ├── inspect_pdf.py              # テスト・デバッグ用
│   ├── run_test.bat                # テスト実行（Windows）
│   ├── run_test.sh                 # テスト実行（Mac/Linux）
│   ├── install_dependencies.bat    # 依存関係インストール（Windows）
│   ├── install_dependencies.sh     # 依存関係インストール（Mac/Linux）
│   └── check_python.bat            # 環境確認（Windows）
├── tests/
│   ├── test_parse_pdf.py           # ユニットテスト
│   ├── test_real_pdf.py            # 統合テスト
│   ├── test_table_extraction.py    # テーブル抽出テスト
│   └── debug/                      # デバッグ用スクリプト
│       ├── test_notion_connection.py
│       ├── test_notion_save.py
│       └── ... (その他デバッグスクリプト)
├── docs/
│   ├── INSTALL_GUIDE.md            # インストールガイド
│   ├── TESTING.md                  # テスト詳細
│   ├── API.md                      # API仕様
│   ├── CHANGELOG.md                # 変更履歴
│   └── analysis_report.md          # 解析レポート
├── test_server.py                  # ローカル開発サーバー
├── requirements.txt                # Python依存関係
└── README.md                       # このファイル
```

## 🔧 使い方

### コマンドライン

```bash
# デフォルトPDFでテスト
python scripts\inspect_pdf.py

# 指定したPDFでテスト
python scripts\inspect_pdf.py path/to/report.pdf

# すべての患者データを表示
python scripts\inspect_pdf.py --all report.pdf
```

### バッチファイル/シェルスクリプト

```bash
# Windows
scripts\run_test.bat [PDF_FILE]

# Mac/Linux
scripts/run_test.sh [PDF_FILE]
```

### API経由

```javascript
const formData = new FormData();
formData.append('file', pdfFile);

const response = await fetch('/api/parse_daily_report', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log(data.summary);     // 集計データ
console.log(data.patients);    // 個別患者データ
```

## 📖 ドキュメント

- **[INSTALL_GUIDE.md](docs/INSTALL_GUIDE.md)** - インストールとトラブルシューティング
- **[TESTING.md](docs/TESTING.md)** - テスト方法の詳細ガイド
- **[API.md](docs/API.md)** - APIレスポンス仕様
- **[CHANGELOG.md](docs/CHANGELOG.md)** - 変更履歴

## 🆕 最新の変更（v2.0）

- ✅ テーブル抽出方式に変更（`extract_table()`使用）
- ✅ 個別患者データの抽出機能を追加
- ✅ 前回差額など詳細データの出力に対応
- ✅ 複数行セルの処理に対応
- ✅ コマンドライン引数でPDFファイル指定可能
- ✅ 自動インストールスクリプト追加

詳細は [CHANGELOG.md](docs/CHANGELOG.md) を参照してください。

## ⚡ ヘルプ

### 依存関係のインストールエラー

```bash
# check_python.bat で環境を確認
scripts\check_python.bat

# install_dependencies.bat で自動インストール
scripts\install_dependencies.bat
```

### テストの実行方法

```bash
# 最も簡単な方法
run_test.bat
```

詳細は [TESTING.md](docs/TESTING.md) を参照

### pipが使えない

`pip` の代わりに `python -m pip` を使用してください。
詳細は [INSTALL_GUIDE.md](docs/INSTALL_GUIDE.md) を参照

## 📝 ライセンス

Private

## 👤 作者

h4mmerjp
