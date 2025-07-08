# LINE WORKS Bot 連携設定手順

## 前提条件
- LINE WORKS Developer Consoleへのアクセス権限
- Bot が作成済み
- テスト用ユーザーアカウント

## 設定手順

### 1. ngrok でローカルサーバーを公開

```bash
# ngrokをインストール（まだの場合）
# macOS: brew install ngrok

# ローカルサーバーを公開
ngrok http 5000
```

ngrok起動後、以下のようなURLが表示されます：
```
Forwarding  https://xxxx-xx-xx-xx-xx.ngrok.io -> http://localhost:5000
```

### 2. LINE WORKS Developer Console での設定

1. [LINE WORKS Developer Console](https://developers.worksmobile.com/) にログイン
2. 対象のBotを選択
3. 「Bot」設定画面で以下を設定：
   - **Callback URL**: `https://xxxx-xx-xx-xx-xx.ngrok.io/webhook`
   - **利用する機能**: 「トーク」にチェック

### 3. 顧客データに LINE WORKS ユーザーID を設定

1. LINE WORKS でテストユーザーの userId を確認
   - Bot にメッセージを送信してログで確認
   - または Developer Console で確認

2. 顧客管理システムで該当顧客を編集
   - 顧客詳細画面から「編集」ボタンをクリック
   - 「LINE WORKS ユーザーID」欄に userId を入力（例：`U12345678`）

### 4. 動作確認

1. LINE WORKS アプリでテストユーザーとしてログイン
2. Bot とのトークルームでメッセージを送信
3. 顧客管理システムの該当顧客詳細ページで活動履歴を確認

## トラブルシューティング

### ログの確認方法
```bash
# Flaskアプリのログを確認
tail -f app.log
```

### よくある問題

1. **Webhook が届かない**
   - ngrok が起動しているか確認
   - Callback URL が正しく設定されているか確認
   - Bot の「トーク」機能が有効になっているか確認

2. **ユーザーIDが一致しない**
   - LINE WORKS の userId は環境により異なります
   - ログで実際の userId を確認して設定

3. **活動履歴に記録されない**
   - 顧客の line_user_id が正しく設定されているか確認
   - データベースに該当顧客が存在するか確認

## セキュリティ注意事項

- ngrok URLは一時的なものです。本番環境では適切なHTTPS対応サーバーを使用してください
- Bot Secret を使用した署名検証の実装を推奨します（現在は未実装）