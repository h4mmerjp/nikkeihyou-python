# デバッグ・テストスクリプト

このディレクトリには、開発中に使用したデバッグおよびテスト用のスクリプトが含まれています。

## ファイル説明

### Notion接続テスト
- `test_notion_connection.py` - Notion APIへの基本的な接続テスト
- `check_database_id.py` - データベースIDの確認
- `debug_database.py` - データベース情報のデバッグ
- `test_data_source.py` - Data Source API のテスト

### Notionデータベース操作
- `create_database_properties.py` - データベースプロパティの作成
- `create_new_database.py` - 新しいデータベースの作成

### Notion保存テスト
- `test_create_page.py` - ページ作成のテスト
- `test_notion_save.py` - Notion保存機能の統合テスト

## 使用方法

これらのスクリプトは開発時のデバッグ用です。本番環境では使用しません。

実行する場合は、プロジェクトルートから:
```bash
python tests/debug/test_notion_connection.py
```

## 注意事項

- これらのスクリプトは `.env` ファイルの環境変数を使用します
- 実行前に NOTION_TOKEN と NOTION_DATABASE_ID が設定されていることを確認してください
