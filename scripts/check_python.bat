@echo off
REM Python環境確認スクリプト

echo =====================================
echo Python環境の確認
echo =====================================
echo.

echo [1] Pythonのバージョン:
python --version
if %errorlevel% neq 0 (
    echo エラー: Python が見つかりません。
    echo.
    echo Pythonをインストールしてください:
    echo https://www.python.org/downloads/
    echo.
    echo インストール時に「Add Python to PATH」にチェックを入れてください。
    pause
    exit /b 1
)

echo.
echo [2] Pythonの場所:
where python

echo.
echo [3] pipの確認（方法1 - pipコマンド）:
pip --version
if %errorlevel% neq 0 (
    echo ⚠ pipコマンドが見つかりません
) else (
    echo ✓ pipコマンドが使えます
)

echo.
echo [4] pipの確認（方法2 - python -m pip）:
python -m pip --version
if %errorlevel% neq 0 (
    echo ⚠ python -m pip が使えません
    echo pipをインストールする必要があります
) else (
    echo ✓ python -m pip が使えます（この方法を推奨）
)

echo.
echo [5] インストール済みパッケージの確認:
python -m pip list | findstr "pdfplumber notion-client requests python-multipart"
if %errorlevel% neq 0 (
    echo ⚠ 必要なパッケージがインストールされていません
    echo.
    echo 以下のコマンドでインストールしてください:
    echo   python -m pip install -r requirements.txt
) else (
    echo ✓ 必要なパッケージがインストールされています
)

echo.
echo =====================================
echo 確認完了
echo =====================================
echo.
echo 推奨: pip の代わりに "python -m pip" を使用してください
echo.
pause
