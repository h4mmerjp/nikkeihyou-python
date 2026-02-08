# インストールガイド

## ❌ 「pip が見つかりません」エラーの解決方法

### 解決策1: `python -m pip` を使う（最も簡単）

`pip` の代わりに `python -m pip` を使います：

```cmd
cd C:\Users\shiot\GitHub\nikkeihyou-python
python -m pip install -r requirements.txt
```

### 解決策2: 自動インストールスクリプトを使う

1. プロジェクトフォルダを開く
2. `scriptsinstall_dependencies.bat` をダブルクリック

このスクリプトは自動的に `python -m pip` を使います。

### 解決策3: Python環境を確認する

1. `scriptseck_python.bat` をダブルクリック
2. 表示される情報を確認

## 🔍 Pythonがインストールされていない場合

### Pythonのインストール

1. **Pythonをダウンロード**
   - https://www.python.org/downloads/
   - Python 3.8以上を推奨

2. **インストール時の重要な設定**
   - ✅ **「Add Python to PATH」にチェックを入れる**（重要！）
   - ✅ 「Install for all users」を選択（推奨）

3. **インストール確認**
   ```cmd
   python --version
   ```

   表示例：
   ```
   Python 3.11.0
   ```

### pipが使えない場合の対処法

#### 方法A: get-pip.py を使う

```cmd
# get-pip.pyをダウンロード
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

# pipをインストール
python get-pip.py
```

#### 方法B: Pythonを再インストール

1. Pythonをアンインストール
2. 再度インストール（「Add Python to PATH」にチェック）

#### 方法C: python -m ensurepip

```cmd
python -m ensurepip --upgrade
```

## 📦 依存関係のインストール手順

### ステップ1: プロジェクトフォルダに移動

```cmd
cd C:\Users\shiot\GitHub\nikkeihyou-python
```

### ステップ2: 依存関係をインストール

以下のいずれかを実行：

**オプションA: 一括インストール**
```cmd
python -m pip install -r requirements.txt
```

**オプションB: 個別インストール**
```cmd
python -m pip install pdfplumber==0.11.0
python -m pip install notion-client==2.2.1
python -m pip install requests==2.31.0
python -m pip install python-multipart==0.0.9
```

**オプションC: バッチファイル**
```cmd
scriptsinstall_dependencies.bat
```
（ダブルクリックでもOK）

### ステップ3: インストール確認

```cmd
python -c "import pdfplumber; print('pdfplumber: OK')"
python -c "import notion_client; print('notion-client: OK')"
python -c "import requests; print('requests: OK')"
```

すべて「OK」と表示されれば成功です。

## 🚀 テスト実行

```cmd
python scripts\inspect_pdf.py
```

## ⚠️ よくあるエラーと解決法

### エラー1: "Python は内部コマンドまたは外部コマンドとして認識されていません"

**原因**: PythonがPATHに追加されていない

**解決法**:
1. Pythonを再インストール（「Add Python to PATH」にチェック）
2. または、環境変数を手動で設定

### エラー2: "python -m pip: No module named pip"

**原因**: pipがインストールされていない

**解決法**:
```cmd
python -m ensurepip --upgrade
```

### エラー3: "Could not find a version that satisfies the requirement"

**原因**: インターネット接続の問題またはパッケージ名の誤り

**解決法**:
1. インターネット接続を確認
2. パッケージ名のスペルを確認
3. pipをアップグレード:
   ```cmd
   python -m pip install --upgrade pip
   ```

### エラー4: "Permission denied" または "Access denied"

**原因**: 管理者権限が必要

**解決法**:
```cmd
# ユーザー領域にインストール
python -m pip install --user -r requirements.txt
```

または

1. コマンドプロンプトを「管理者として実行」
2. 再度インストールを試す

### エラー5: Microsoft Store版Pythonの問題

**原因**: Microsoft Store版PythonにはPATHの問題がある場合がある

**解決法**:
1. python.orgからPythonをダウンロード
2. Microsoft Store版をアンインストール
3. python.org版をインストール

## 🔧 環境変数の確認と設定（上級者向け）

### 環境変数を確認

```cmd
echo %PATH%
```

Pythonのパス（例: `C:\Python311\` や `C:\Users\user\AppData\Local\Programs\Python\Python311\`）が含まれているか確認

### 環境変数を追加（手動）

1. 「システムのプロパティ」を開く
2. 「環境変数」をクリック
3. 「Path」を編集
4. 以下を追加:
   - `C:\Python311\`
   - `C:\Python311\Scripts\`
   （実際のPythonのインストールパスに合わせる）

## 📞 サポート

それでも解決しない場合は、以下の情報を収集してください：

1. **scriptseck_python.bat の出力結果**
2. **Pythonのバージョン**: `python --version`
3. **pipのバージョン**: `python -m pip --version`
4. **エラーメッセージの全文**

## 🎯 まとめ

### 最も簡単な方法（推奨）

1. `scriptseck_python.bat` をダブルクリックして環境を確認
2. `scriptsinstall_dependencies.bat` をダブルクリックして依存関係をインストール
3. `scriptsun_test.bat` をダブルクリックしてテスト実行

すべてバッチファイルをダブルクリックするだけで完了します！
