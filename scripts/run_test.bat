@echo off
REM Windows用の簡易テストスクリプト

echo =====================================
echo PDF Parser Test
echo =====================================
echo.

REM Pythonのバージョンを確認
python --version
if %errorlevel% neq 0 (
    echo Python が見つかりません。
    echo Python 3.x をインストールしてください。
    pause
    exit /b 1
)

echo.
echo 依存関係をチェック中...
python -c "import pdfplumber" 2>nul
if %errorlevel% neq 0 (
    echo pdfplumber がインストールされていません。
    echo.
    echo 依存関係をインストールしますか? (Y/N)
    set /p install=
    if /i "%install%"=="Y" (
        echo インストール中...
        pip install -r requirements.txt
    ) else (
        echo テストを中止しました。
        pause
        exit /b 1
    )
)

echo.
echo =====================================
echo テスト実行中...
echo =====================================
echo.

REM 引数が渡された場合はそのファイルを使用、なければデフォルト
if "%1"=="" (
    echo デフォルトPDF（total_d.pdf）を使用します
    python scripts\inspect_pdf.py
) else (
    echo 指定されたPDF（%1）を使用します
    python scripts\inspect_pdf.py %1
)

echo.
echo =====================================
echo テスト完了
echo =====================================
echo.
echo 使用方法:
echo   run_test.bat              ^(total_d.pdfを使用^)
echo   run_test.bat my_file.pdf  ^(指定したPDFを使用^)
echo.
pause
