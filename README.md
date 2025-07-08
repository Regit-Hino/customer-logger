# 顧客管理システム (LINE WORKS Bot連携)

LINE WORKS Botと連携した顧客管理システムのPoC実装です。

## 🚀 クイックスタート

### 1. 必要な環境
- Python 3.9以上
- ngrok（インストール: `brew install ngrok`）
- LINE WORKS Bot（事前に作成済み）

### 2. セットアップ
```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# サンプルデータの投入（オプション）
python3 init_sample_data.py
```

### 3. システム起動（推奨）
```bash
# 一括起動スクリプトを実行
./start.sh
```

このスクリプトは以下を自動実行します：
- Flask アプリケーションの起動
- ngrok でローカルサーバーを公開
- ngrok URL の自動取得と表示
- Webhook接続テスト（オプション）

### 4. 手動起動
```bash
# Flask アプリケーション
python3 app.py

# 別ターミナルで ngrok
ngrok http 3000
```

## 📋 LINE WORKS Bot設定

1. LINE WORKS Developer Console にログイン
2. Bot の Callback URL を設定
   ```
   https://xxxx-xx-xx-xx-xx.ngrok.io/webhook
   ```
3. 「トーク」機能を有効化

## 🔧 主な機能

- **顧客管理**: 作成・編集・一覧表示
- **活動履歴**: LINE WORKSメッセージの自動記録
- **連携ステータス**: 実際の通信状況を表示
- **複数顧客対応**: 同一LINE WORKS IDの複数顧客に対応

## 📁 プロジェクト構成
```
customer-logger/
├── app.py                    # メインアプリケーション
├── database.db              # SQLiteデータベース
├── requirements.txt         # 依存パッケージ
├── start.sh                # 起動スクリプト
├── init_sample_data.py     # サンプルデータ
├── templates/              # HTMLテンプレート
│   ├── layout.html
│   ├── customer_list.html
│   ├── customer_detail.html
│   ├── customer_form.html
│   └── customer_edit.html
├── SYSTEM_SPECIFICATION.md  # 詳細仕様書
├── LINEWORKS_SETUP.md      # LINE WORKS設定ガイド
└── README.md               # このファイル
```

## 🧪 デバッグ・テスト

### Webhookテスト
```bash
curl http://localhost:3000/test-webhook
```

### 特定顧客の確認
```bash
curl http://localhost:3000/check-customer/d83d38ad-a597-48e1-1254-044ff0479ea0
```

## 📝 ログ確認
```bash
# アプリケーションログ
tail -f app_output.log

# コンソール出力にはリアルタイムでWebhook情報が表示されます
```

## 🛑 システム停止

起動スクリプト使用時: `Ctrl+C`

手動起動時:
```bash
# Flask プロセスの停止
pkill -f "python.*app.py"

# ngrok の停止
pkill ngrok
```

## 📚 詳細ドキュメント

- [システム仕様書](SYSTEM_SPECIFICATION.md)
- [LINE WORKS設定ガイド](LINEWORKS_SETUP.md)

## ⚠️ 注意事項

- PoCのため、認証機能は実装されていません
- ngrok URLは起動のたびに変更されます
- 本番環境では適切なHTTPSサーバーを使用してください