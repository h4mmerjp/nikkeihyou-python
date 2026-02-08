@echo off
REM 依存関係インストール用バッチファイル

echo =====================================
echo 依存関係のインストール
echo =====================================
echo.

REM Pythonのバージョンを確認
python --version
if %errorlevel% neq 0 (
    echo エラー: Python が見つかりません。
    echo Python 3.x をインストールしてください。
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo pipをアップグレードしています...
python -m pip install --upgrade pip

echo.
echo 依存関係をインストールしています...
echo.

pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo エラー: インストールに失敗しました。
    echo.
    echo 別の方法を試してください:
    echo   python -m pip install --user -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo =====================================
echo インストール完了！
echo =====================================
echo.
echo インストールされたパッケージ:
pip list | findstr "pdfplumber notion-client requests python-multipart"

echo.
echo 確認テストを実行しています...
python -c "import pdfplumber; import notion_client; import requests; print('すべてのモジュールが正しくインストールされました！')"

if %errorlevel% neq 0 (
    echo.
    echo 警告: 一部のモジュールのインポートに失敗しました。
    pause
    exit /b 1
)

echo.
echo これでテストを実行できます:
echo   python scripts\inspect_pdf.py
echo   または
echo   run_test.bat
echo.
pause
