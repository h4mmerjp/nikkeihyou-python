#!/bin/bash
# 依存関係インストール用シェルスクリプト

echo "====================================="
echo "依存関係のインストール"
echo "====================================="
echo ""

# Pythonコマンドを決定
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo "エラー: Python が見つかりません。"
        echo "Python 3.x をインストールしてください。"
        echo "https://www.python.org/downloads/"
        exit 1
    fi
fi

echo "Python バージョン:"
$PYTHON_CMD --version
echo ""

echo "pipをアップグレードしています..."
$PYTHON_CMD -m pip install --upgrade pip

echo ""
echo "依存関係をインストールしています..."
echo ""

if ! pip install -r requirements.txt; then
    echo ""
    echo "エラー: インストールに失敗しました。"
    echo ""
    echo "別の方法を試してください:"
    echo "  $PYTHON_CMD -m pip install --user -r requirements.txt"
    echo ""
    exit 1
fi

echo ""
echo "====================================="
echo "インストール完了！"
echo "====================================="
echo ""
echo "インストールされたパッケージ:"
pip list | grep -E "pdfplumber|notion-client|requests|python-multipart"

echo ""
echo "確認テストを実行しています..."
if $PYTHON_CMD -c "import pdfplumber; import notion_client; import requests; print('すべてのモジュールが正しくインストールされました！')"; then
    echo ""
    echo "これでテストを実行できます:"
    echo "  $PYTHON_CMD scripts/inspect_pdf.py"
    echo "  または"
    echo "  ./run_test.sh"
    echo ""
else
    echo ""
    echo "警告: 一部のモジュールのインポートに失敗しました。"
    exit 1
fi
