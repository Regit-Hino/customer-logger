# Render デプロイガイド

このガイドでは、customer-loggerアプリケーションをRenderにデプロイする手順を説明します。

## 前提条件

- GitHubアカウント
- Renderアカウント（https://render.com）
- private.keyファイル（LINE WORKS認証用）

## デプロイ手順

### 1. private.keyのBase64エンコード

まず、LINE WORKS認証用の秘密鍵をBase64形式に変換します：

```bash
python3 encode_private_key.py
```

出力されたBase64文字列をコピーしておきます。

### 2. GitHubリポジトリの準備

```bash
# Gitリポジトリの初期化（まだの場合）
git init

# ファイルをステージング
git add .

# コミット
git commit -m "Initial commit for Render deployment"

# GitHubにプッシュ
git remote add origin https://github.com/YOUR_USERNAME/customer-logger.git
git branch -M main
git push -u origin main
```

### 3. Renderでのデプロイ

1. [Render Dashboard](https://dashboard.render.com/)にログイン

2. 「New +」→「Web Service」をクリック

3. GitHubリポジトリを接続：
   - 「Connect a repository」でGitHubアカウントを連携
   - `customer-logger`リポジトリを選択

4. 設定内容：
   - **Name**: customer-logger
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

5. 環境変数の設定（「Advanced」→「Add Environment Variable」）：
   - `LINE_WORKS_PRIVATE_KEY_BASE64`: （手順1でコピーしたBase64文字列）
   - その他の環境変数は`render.yaml`で自動設定されます

6. 「Create Web Service」をクリック

### 4. デプロイ完了後の設定

1. デプロイが完了すると、`https://customer-logger.onrender.com`のようなURLが割り当てられます

2. LINE WORKS Developer ConsoleでBotのCallback URLを更新：
   ```
   https://customer-logger.onrender.com/webhook
   ```

## 注意事項

### SQLiteの制限

Renderの無料プランではファイルシステムが永続化されないため：
- アプリケーションが再起動するとデータベースがリセットされます
- 本番環境では、PostgreSQLなどの永続的なデータベースへの移行を推奨します

### スリープモード

無料プランでは15分間アクセスがないとアプリケーションがスリープします：
- 初回アクセス時に起動に時間がかかる場合があります
- 定期的なヘルスチェックを設定することで回避可能

### ログの確認

Renderダッシュボードの「Logs」タブから：
- アプリケーションログ
- ビルドログ
- デプロイログ
を確認できます。

## トラブルシューティング

### デプロイが失敗する場合

1. `requirements.txt`にすべての依存関係が含まれているか確認
2. 環境変数が正しく設定されているか確認
3. ビルドログでエラーメッセージを確認

### Webhookが受信できない場合

1. LINE WORKS側のCallback URLが正しいか確認
2. Renderのログでエラーがないか確認
3. ngrokでローカルテストして動作確認

### 秘密鍵エラーの場合

1. `LINE_WORKS_PRIVATE_KEY_BASE64`環境変数が正しく設定されているか確認
2. Base64エンコードが正しく行われているか確認
3. ログで`Private key loaded from environment variable`が表示されているか確認

## 本番環境への移行

本番環境では以下の対応を推奨：

1. **データベース**: PostgreSQLへの移行
2. **認証**: ユーザー認証の実装
3. **セキュリティ**: HTTPS強制、CSRF対策
4. **監視**: エラー監視、パフォーマンス監視
5. **バックアップ**: 定期的なデータバックアップ