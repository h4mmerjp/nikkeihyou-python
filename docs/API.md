# API仕様書

日計表PDF解析APIのリファレンスドキュメント

## エンドポイント

```
POST /api/parse_daily_report
```

## 概要

日計表PDFから個別患者データと集計データの両方を抽出し、Notionデータベースに保存します。

## リクエスト

### Content-Type

```
multipart/form-data
```

### パラメータ

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| file | File | ✓ | 日計表PDFファイル |

### リクエスト例

#### curl

```bash
curl -X POST http://localhost:3000/api/parse_daily_report \
  -F "file=@total_d.pdf"
```

#### JavaScript (Fetch API)

```javascript
const formData = new FormData();
formData.append('file', pdfFile);

const response = await fetch('/api/parse_daily_report', {
  method: 'POST',
  body: formData
});

const data = await response.json();
```

#### Python (requests)

```python
import requests

with open('total_d.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:3000/api/parse_daily_report',
        files=files
    )
    data = response.json()
```

## レスポンス

### 成功時 (200 OK)

```json
{
  "success": true,
  "summary": {
    "date": "2025-05-31",
    "shaho_count": 42,
    "shaho_amount": 130500,
    "kokuho_count": 4,
    "kokuho_amount": 6050,
    "kouki_count": 5,
    "kouki_amount": 3390,
    "jihi_count": 0,
    "jihi_amount": 3850,
    "hoken_nashi_count": 1,
    "hoken_nashi_amount": 10060,
    "total_count": 55,
    "total_amount": 150000,
    "bushan_amount": 1560,
    "kaigo_amount": 0,
    "zenkai_sagaku": -700
  },
  "patients": [
    {
      "number": 1,
      "patient_id": "No.11378",
      "name": "松本　正和",
      "insurance_type": "社本",
      "points": 2174,
      "burden_amount": 6520,
      "kaigo_units": 0,
      "kaigo_burden": 0,
      "jihi": 0,
      "bushan": 0,
      "zenkai_sagaku": 0,
      "receipt_amount": 6520,
      "sagaku": 0,
      "remarks": ""
    }
  ],
  "notion_page_id": "xxxx-xxxx-xxxx-xxxx"
}
```

### エラー時 (400/500)

```json
{
  "success": false,
  "error": "エラーメッセージ"
}
```

## データ構造

### レスポンスフィールド

| フィールド | 型 | 説明 |
|---|---|---|
| success | boolean | 処理の成功/失敗 |
| summary | object | 集計データ（後述） |
| patients | array | 個別患者データの配列（後述） |
| notion_page_id | string | Notion ページID |
| error | string | エラーメッセージ（エラー時のみ） |

### summary（集計データ）

| フィールド | 型 | 説明 | 例 |
|---|---|---|---|
| date | string | 日付（YYYY-MM-DD形式） | "2025-05-31" |
| shaho_count | number | 社保人数 | 42 |
| shaho_amount | number | 社保金額 | 130500 |
| kokuho_count | number | 国保人数 | 4 |
| kokuho_amount | number | 国保金額 | 6050 |
| kouki_count | number | 後期人数 | 5 |
| kouki_amount | number | 後期金額 | 3390 |
| jihi_count | number | 自費人数（現在は常に0） | 0 |
| jihi_amount | number | 自費金額 | 3850 |
| hoken_nashi_count | number | 保険なし人数 | 1 |
| hoken_nashi_amount | number | 保険なし金額 | 10060 |
| total_count | number | 合計人数 | 55 |
| total_amount | number | 合計金額 | 150000 |
| bushan_amount | number | 物販金額 | 1560 |
| kaigo_amount | number | 介護金額 | 0 |
| zenkai_sagaku | number | 前回差額（マイナス可） | -700 |

### patients（個別患者データ）

配列形式。各要素は以下のフィールドを持つオブジェクト。

| フィールド | 型 | 説明 | 例 |
|---|---|---|---|
| number | number | 患者番号（1から始まる連番） | 1 |
| patient_id | string | 患者ID | "No.11378" |
| name | string | 患者氏名 | "松本　正和" |
| insurance_type | string | 保険種別 | "社本", "再初診 社本" |
| points | number | 点数 | 2174 |
| burden_amount | number | 負担額 | 6520 |
| kaigo_units | number | 介護単位 | 0 |
| kaigo_burden | number | 介護負担額 | 0 |
| jihi | number | 自費 | 0 |
| bushan | number | 物販 | 0 |
| zenkai_sagaku | number | 前回差額 | 0 |
| receipt_amount | number | 領収額 | 6520 |
| sagaku | number | 差額 | 0 |
| remarks | string | 備考 | "" |

## 使用例

### 基本的な使用

```javascript
// PDFをアップロード
const formData = new FormData();
formData.append('file', pdfFile);

const response = await fetch('/api/parse_daily_report', {
  method: 'POST',
  body: formData
});

const data = await response.json();

if (data.success) {
  console.log('日付:', data.summary.date);
  console.log('合計人数:', data.summary.total_count);
  console.log('合計金額:', data.summary.total_amount);
  console.log('患者数:', data.patients.length);
}
```

### 集計データの表示

```javascript
const { summary } = data;

console.log(`日付: ${summary.date}`);
console.log(`合計: ${summary.total_count}人 / ¥${summary.total_amount.toLocaleString()}`);
console.log(`社保: ${summary.shaho_count}人 / ¥${summary.shaho_amount.toLocaleString()}`);
console.log(`国保: ${summary.kokuho_count}人 / ¥${summary.kokuho_amount.toLocaleString()}`);
console.log(`後期: ${summary.kouki_count}人 / ¥${summary.kouki_amount.toLocaleString()}`);
console.log(`前回差額: ¥${summary.zenkai_sagaku.toLocaleString()}`);
```

### 個別患者データのテーブル表示

```javascript
data.patients.forEach(patient => {
  console.log(
    `${patient.number}. ${patient.name} (${patient.patient_id}) - ` +
    `${patient.insurance_type} - ` +
    `¥${patient.receipt_amount.toLocaleString()}`
  );
});
```

### 前回差額のある患者をフィルタ

```javascript
const patientsWithDiff = data.patients.filter(p => p.zenkai_sagaku !== 0);
console.log('前回差額がある患者:', patientsWithDiff);
```

### React での使用例

```jsx
import { useState } from 'react';

function PDFUploader() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (file) => {
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/parse_daily_report', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        accept=".pdf"
        onChange={(e) => handleUpload(e.target.files[0])}
        disabled={loading}
      />

      {result?.success && (
        <div>
          <h2>集計データ</h2>
          <p>日付: {result.summary.date}</p>
          <p>合計人数: {result.summary.total_count}人</p>
          <p>合計金額: ¥{result.summary.total_amount.toLocaleString()}</p>

          <h2>個別患者データ ({result.patients.length}件)</h2>
          <table>
            <thead>
              <tr>
                <th>番号</th>
                <th>氏名</th>
                <th>保険種別</th>
                <th>領収額</th>
              </tr>
            </thead>
            <tbody>
              {result.patients.map(patient => (
                <tr key={patient.number}>
                  <td>{patient.number}</td>
                  <td>{patient.name}</td>
                  <td>{patient.insurance_type}</td>
                  <td>¥{patient.receipt_amount.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
```

## エラーハンドリング

### エラーレスポンス例

```json
{
  "success": false,
  "error": "No file uploaded"
}
```

```json
{
  "success": false,
  "error": "PDF parsing failed: Invalid PDF format"
}
```

### JavaScriptでのエラーハンドリング

```javascript
try {
  const response = await fetch('/api/parse_daily_report', {
    method: 'POST',
    body: formData
  });

  const data = await response.json();

  if (!data.success) {
    console.error('API Error:', data.error);
    return;
  }

  // 成功時の処理
  console.log('Data:', data);

} catch (error) {
  console.error('Network Error:', error);
}
```

## 制限事項

- **ファイルサイズ**: 最大10MB（Vercelの制限）
- **ファイル形式**: PDFのみ
- **同時リクエスト**: Vercelの無料プランでは制限あり
- **タイムアウト**: 10秒（Vercelの制限）

## Notion連携

APIはNotionデータベースに以下のデータを保存します：

- 集計データ（日付、各保険区分の人数・金額など）
- PDFファイル（添付）
- 照合状態（初期値: "未照合"）

**注意**: 個別患者データは現在Notionには保存されません（APIレスポンスのみ）。

## バージョン履歴

### v2.0 (2025-02-07)
- ✅ テーブル抽出方式に変更（`extract_table()`使用）
- ✅ 個別患者データの抽出機能を追加
- ✅ レスポンス構造を `summary` と `patients` に分離
- ✅ 複数行セルの処理に対応

### v1.0
- 初期版（集計データのみ抽出）

## 関連ドキュメント

- [README.md](README.md) - プロジェクト概要
- [TESTING.md](TESTING.md) - テスト方法
- [INSTALL_GUIDE.md](INSTALL_GUIDE.md) - インストールガイド
- [CHANGELOG.md](CHANGELOG.md) - 詳細な変更履歴
