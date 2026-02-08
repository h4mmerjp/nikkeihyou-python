#!/bin/bash
# Mac/Linux用の簡易テストスクリプト

echo "====================================="
echo "PDF Parser Test"
echo "====================================="
echo ""

# Pythonのバージョンを確認
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "Python が見つかりません。"
    echo "Python 3.x をインストールしてください。"
    exit 1
fi

# python または python3 を使用
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "Python バージョン:"
$PYTHON_CMD --version
echo ""

# 依存関係をチェック
echo "依存関係をチェック中..."
if ! $PYTHON_CMD -c "import pdfplumber" 2>/dev/null; then
    echo "pdfplumber がインストールされていません。"
    echo ""
    echo "依存関係をインストールしますか? (y/n)"
    read -r install
    if [[ $install == "y" || $install == "Y" ]]; then
        echo "インストール中..."
        pip install -r requirements.txt
    else
        echo "テストを中止しました。"
        exit 1
    fi
fi

echo ""
echo "====================================="
echo "テスト実行中..."
echo "====================================="
echo ""

# 引数が渡された場合はそのファイルを使用、なければデフォルト
if [ -z "$1" ]; then
    echo "デフォルトPDF（total_d.pdf）を使用します"
    $PYTHON_CMD scripts/inspect_pdf.py
else
    echo "指定されたPDF（$1）を使用します"
    $PYTHON_CMD scripts/inspect_pdf.py "$1"
fi

echo ""
echo "====================================="
echo "テスト完了"
echo "====================================="
echo ""
echo "使用方法:"
echo "  ./run_test.sh              (total_d.pdfを使用)"
echo "  ./run_test.sh my_file.pdf  (指定したPDFを使用)"
echo ""
