# 顧客管理システム（CRM）包括的システム仕様書

## 1. システム概要と目的

### 1.1 システム概要
本システムは、LINE WORKS Bot と連携した顧客管理システム（CRM）のProof of Concept（PoC）実装です。LINE WORKS上での顧客とのコミュニケーションを自動的に活動履歴として記録し、Salesforce風のユーザーインターフェースで一元管理します。

### 1.2 システムの目的
- LINE WORKSを通じた顧客とのコミュニケーション履歴の自動記録
- 顧客情報と活動履歴の一元管理
- リアルタイムでの顧客対応状況の可視化
- 双方向コミュニケーション（メッセージ送信）のサポート

### 1.3 主要機能
1. 会社・顧客情報の管理（CRUD操作）
2. LINE WORKS Botとの自動連携
3. 活動履歴の自動記録と時系列表示
4. 顧客へのメッセージ送信機能
5. 連携ステータスの可視化

## 2. 技術スタック詳細

### 2.1 バックエンド
| 要素 | 技術/バージョン | 説明 |
|------|----------------|------|
| 言語 | Python 3.9+ | メイン開発言語 |
| Webフレームワーク | Flask 2.x | 軽量で柔軟なWebフレームワーク |
| データベース | SQLite 3 | 組み込み型リレーショナルDB |
| ORM | SQLite3（標準ライブラリ） | データベース操作 |
| 認証ライブラリ | PyJWT | JWT生成（LINE WORKS認証用） |
| HTTPクライアント | Requests | 外部API通信 |

### 2.2 フロントエンド
| 要素 | 技術/バージョン | 説明 |
|------|----------------|------|
| CSSフレームワーク | Bootstrap 5.1.3 | レスポンシブデザイン |
| アイコン | Bootstrap Icons 1.7.2 | UIアイコン |
| テンプレートエンジン | Jinja2 | Flask標準テンプレート |
| JavaScript | Vanilla JS | 動的機能（Ajax通信等） |

### 2.3 外部連携
| サービス | 用途 | 認証方式 |
|----------|------|----------|
| LINE WORKS Bot API | メッセージ送受信 | Service Account (JWT) |
| ngrok | ローカル環境の公開 | - |

### 2.4 開発環境
- **ポート設定**: 3000番ポート（Flask）
- **ホスト設定**: 0.0.0.0（全インターフェース受付）
- **デバッグモード**: 開発時は有効

## 3. データベーススキーマ詳細

### 3.1 companiesテーブル
```sql
CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    website TEXT
);
```

### 3.2 customersテーブル
```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    line_user_id TEXT,
    company_id INTEGER,
    FOREIGN KEY (company_id) REFERENCES companies (id)
);
```

### 3.3 activitiesテーブル
```sql
CREATE TABLE activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers (id)
);
```

### 3.4 インデックス設計
- `customers.line_user_id`：頻繁な検索のため推奨
- `activities.customer_id`：外部キー制約
- `activities.timestamp`：時系列ソートのため

## 4. LINE WORKS Bot統合仕様

### 4.1 Bot設定値
```python
LINE_WORKS_CONFIG = {
    'bot_id': '10368813',
    'service_account': '8bvy9.serviceaccount@regit-technology',
    'client_id': 'ln7VvQ1rBt_msW7j29qs',
    'client_secret': 'UWD9pXXWd2',
    'domain_id': '400794821',
    'token_url': 'https://auth.worksmobile.com/oauth2/v2.0/token',
    'message_url': 'https://www.worksapis.com/v1.0/bots/{bot_id}/users/{user_id}/messages',
    'private_key_file': 'private.key'
}
```

### 4.2 認証フロー（Service Account認証）

#### 4.2.1 JWT作成プロセス
1. **秘密鍵の読み込み**
   - ファイル：`private.key`（RSA秘密鍵）
   - 形式：PEM形式

2. **JWTペイロード構成**
   ```json
   {
       "iss": "client_id",
       "sub": "service_account",
       "iat": "現在時刻（Unix時間）",
       "exp": "有効期限（1時間後）"
   }
   ```

3. **JWT署名**
   - アルゴリズム：RS256
   - 秘密鍵で署名

#### 4.2.2 アクセストークン取得
1. **リクエスト形式**
   ```
   POST https://auth.worksmobile.com/oauth2/v2.0/token
   Content-Type: application/x-www-form-urlencoded
   
   assertion={JWT}
   grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer
   client_id={client_id}
   client_secret={client_secret}
   scope=bot
   ```

2. **トークンキャッシュ**
   - メモリ内キャッシュ実装
   - 有効期限：55分（安全マージン5分）
   - 自動更新機能

### 4.3 Webhook仕様

#### 4.3.1 エンドポイント
- URL：`/webhook`
- メソッド：POST
- Content-Type：application/json

#### 4.3.2 受信データ形式
```json
{
    "type": "message",
    "source": {
        "userId": "d83d38ad-a597-48e1-1254-044ff0479ea0",
        "domainId": 400794821
    },
    "issuedTime": "2025-07-08T02:45:46.446Z",
    "content": {
        "type": "text",
        "text": "メッセージ内容"
    }
}
```

#### 4.3.3 処理フロー
1. リクエスト受信とログ記録
2. メッセージタイプの確認（type="message"）
3. テキストコンテンツの抽出
4. タイムスタンプのUTCからローカル時間への変換
5. ユーザーIDによる顧客検索（複数顧客対応）
6. 活動履歴への記録
7. 常に200 OKレスポンスを返却

### 4.4 メッセージ送信機能

#### 4.4.1 送信API仕様
```
POST https://www.worksapis.com/v1.0/bots/{bot_id}/users/{user_id}/messages
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "content": {
        "type": "text",
        "text": "送信メッセージ"
    }
}
```

#### 4.4.2 送信フロー
1. アクセストークンの取得/更新
2. メッセージAPIへのPOSTリクエスト
3. レスポンス確認（200/201）
4. 送信履歴の記録（[送信]プレフィックス付き）

## 5. API仕様

### 5.1 顧客管理API

#### 5.1.1 顧客一覧取得
- **エンドポイント**: GET `/customers`
- **レスポンス**: HTML（顧客一覧ページ）
- **機能**: 全顧客の一覧表示、連携ステータス付き

#### 5.1.2 顧客詳細取得
- **エンドポイント**: GET `/customer/<customer_id>`
- **レスポンス**: HTML（顧客詳細ページ）
- **機能**: 顧客情報と活動履歴の表示

#### 5.1.3 顧客新規作成
- **エンドポイント**: POST `/customer/new`
- **パラメータ**: first_name, last_name, email, phone, line_user_id, company_id
- **レスポンス**: リダイレクト（顧客詳細ページ）

#### 5.1.4 顧客編集
- **エンドポイント**: POST `/customer/<customer_id>/edit`
- **パラメータ**: 同上
- **レスポンス**: リダイレクト（顧客詳細ページ）

### 5.2 会社管理API

#### 5.2.1 会社一覧取得
- **エンドポイント**: GET `/companies`
- **レスポンス**: HTML（会社一覧ページ）
- **機能**: 全会社の一覧表示、顧客数付き

#### 5.2.2 会社詳細取得
- **エンドポイント**: GET `/company/<company_id>`
- **レスポンス**: HTML（会社詳細ページ）
- **機能**: 会社情報と所属顧客一覧

#### 5.2.3 会社新規作成
- **エンドポイント**: POST `/company/new`
- **パラメータ**: name, address, phone, website
- **レスポンス**: リダイレクト（会社詳細ページ）

#### 5.2.4 会社編集
- **エンドポイント**: POST `/company/<company_id>/edit`
- **パラメータ**: 同上
- **レスポンス**: リダイレクト（会社詳細ページ）

### 5.3 メッセージ送信API

#### 5.3.1 顧客へのメッセージ送信（Ajax）
- **エンドポイント**: POST `/customer/<customer_id>/send`
- **パラメータ**: message
- **レスポンス**: JSON
  ```json
  {
      "success": true/false,
      "message": "結果メッセージ"
  }
  ```

#### 5.3.2 汎用メッセージ送信API
- **エンドポイント**: POST `/send-message`
- **リクエストボディ**:
  ```json
  {
      "userId": "LINE WORKS ユーザーID",
      "message": "送信メッセージ"
  }
  ```
- **レスポンス**: JSON

### 5.4 活動履歴管理API

#### 5.4.1 活動履歴削除
- **エンドポイント**: POST `/activity/<activity_id>/delete`
- **レスポンス**: リダイレクト（顧客詳細ページ）
- **機能**: 指定された活動履歴の削除

### 5.5 デバッグ・テスト用API

#### 5.5.1 Webhookテスト
- **エンドポイント**: GET `/test-webhook`
- **機能**: ローカル環境でのWebhook処理テスト

#### 5.5.2 顧客確認API
- **エンドポイント**: GET `/check-customer/<user_id>`
- **レスポンス**: JSON（顧客情報と最新活動履歴）

## 6. UI/UX設計仕様

### 6.1 デザインコンセプト
- **基本スタイル**: Salesforce Lightning Design System風
- **カラースキーム**:
  - プライマリカラー: #0070d2（青）
  - 背景色: #f5f7fa（薄いグレー）
  - カード背景: #ffffff（白）
  - テキスト: #333333（濃いグレー）

### 6.2 レイアウト構成

#### 6.2.1 全体構成
```
┌─────────────────────────────────────┐
│         ナビゲーションバー            │
├──────────┬──────────────────────────┤
│          │                          │
│ サイドバー │      メインコンテンツ      │
│          │                          │
└──────────┴──────────────────────────┘
```

#### 6.2.2 ナビゲーションバー
- 高さ: 56px
- 背景色: #0070d2
- ロゴ: 「顧客管理システム」
- 右端: ユーザー情報

#### 6.2.3 サイドバー
- 幅: 16.67%（2/12グリッド）
- メニュー項目:
  - 会社一覧
  - 顧客一覧
- アクティブ状態: 背景色 #e7f1ff、左ボーダー #0070d2

### 6.3 ページ別UI仕様

#### 6.3.1 顧客一覧ページ
- **テーブル形式表示**
  - カラム: 姓名、会社名、メール、電話、LINE WORKS連携状態
  - ソート: 姓名順
  - アクション: 詳細表示リンク

- **連携ステータス表示**
  - 🟢 連携済み（稼働中）: LINE WORKS ID設定済み＋活動履歴あり
  - 🟡 設定済み（未確認）: LINE WORKS ID設定済み＋活動履歴なし
  - ⚫ 未設定: LINE WORKS ID未設定

#### 6.3.2 顧客詳細ページ
- **2カラムレイアウト**
  - 左カラム（4/12）: 顧客基本情報
  - 右カラム（8/12）: 活動履歴

- **活動履歴表示**
  - チャット形式（LINEスタイル）
  - 送信メッセージ: 右寄せ、青背景
  - 受信メッセージ: 左寄せ、白背景
  - タイムスタンプ: 各メッセージ下部
  - 削除ボタン: ホバー時に表示

### 6.4 インタラクション設計

#### 6.4.1 メッセージ送信UI
- **クイック送信**（顧客詳細ページ内）
  - インライン入力フィールド
  - Enterキーで送信
  - Ajax通信でページリロードなし

- **詳細送信画面**
  - 専用ページでの送信
  - 大きなテキストエリア
  - 送信後自動リダイレクト

#### 6.4.2 削除確認
- JavaScriptによる確認ダイアログ
- 「本当に削除しますか？」メッセージ
- OK/キャンセルボタン

## 7. エラーハンドリングと運用ガイドライン

### 7.1 エラーハンドリング方針

#### 7.1.1 Webhook処理
- **原則**: 常に200 OKを返却（LINE WORKS仕様準拠）
- **エラー時**: ログ記録のみ、処理は継続
- **例外キャッチ**: 全体をtry-exceptで囲む

#### 7.1.2 データベース操作
- **トランザクション**: 明示的なcommit
- **エラー時**: ロールバック処理
- **接続管理**: with文での自動クローズ推奨

#### 7.1.3 外部API通信
- **タイムアウト設定**: 30秒（推奨）
- **リトライ**: 認証エラー時のみ1回
- **エラーレスポンス**: ユーザーフレンドリーなメッセージ

### 7.2 ログ設計

#### 7.2.1 ログレベル
- **INFO**: 正常処理の記録
- **WARNING**: 想定内エラー（顧客未発見等）
- **ERROR**: システムエラー、例外

#### 7.2.2 ログ出力先
- **コンソール**: 開発環境での詳細出力
- **app.log**: 本番環境でのファイル出力

#### 7.2.3 ログフォーマット
```
[時刻] [レベル] [モジュール] メッセージ
例: 2025-07-08 10:30:45 INFO webhook Activity recorded for customer 123
```

### 7.3 運用上の注意事項

#### 7.3.1 ngrok使用時
- **URL変更**: 起動ごとに変更される
- **対応**: LINE WORKS ConsoleでCallback URL更新必須
- **有効期限**: 無料版は8時間制限

#### 7.3.2 トークン管理
- **有効期限**: 1時間（55分でリフレッシュ）
- **キャッシュ**: メモリ内保持
- **再起動時**: 再取得必要

#### 7.3.3 データベース管理
- **バックアップ**: 定期的なdatabase.dbのコピー
- **マイグレーション**: init_db()で自動実行
- **インデックス**: 必要に応じて手動追加

## 8. セキュリティ考慮事項

### 8.1 現在の実装状況
- **SQLインジェクション対策**: パラメータバインディング使用
- **XSS対策**: Jinja2の自動エスケープ
- **CSRF対策**: 未実装（PoC段階）

### 8.2 本番環境での推奨事項

#### 8.2.1 認証・認可
- **管理画面**: ログイン機能の実装
- **API**: Bearer tokenによる認証
- **役割ベース**: 管理者/一般ユーザーの権限分離

#### 8.2.2 通信セキュリティ
- **HTTPS**: 必須（Let's Encrypt推奨）
- **署名検証**: LINE WORKS Bot Secretによる検証
- **IPアドレス制限**: LINE WORKSサーバーのみ許可

#### 8.2.3 データ保護
- **暗号化**: 機密情報の暗号化保存
- **マスキング**: ログ出力時の個人情報マスク
- **アクセスログ**: 全操作の監査ログ

### 8.3 コンプライアンス
- **個人情報保護**: 必要最小限の情報のみ保持
- **データ保持期間**: ポリシーに基づく自動削除
- **輸出規制**: 暗号化技術の使用に注意

## 9. トラブルシューティングガイド

### 9.1 よくある問題と対処法

#### 9.1.1 Webhookが受信できない
**症状**: LINE WORKSからのメッセージが記録されない
**確認項目**:
1. ngrokが起動しているか
2. Callback URLが正しく設定されているか
3. Botの「トーク」機能が有効か
4. ログでリクエストが届いているか

**対処法**:
```bash
# ngrokの再起動
ngrok http 3000

# ログの確認
tail -f app.log | grep webhook
```

#### 9.1.2 メッセージ送信エラー
**症状**: 「送信エラー: 401」等のエラー
**確認項目**:
1. アクセストークンの有効期限
2. private.keyファイルの存在
3. Bot設定値の正確性

**対処法**:
```python
# トークンキャッシュのクリア（app.pyで実行）
token_cache['access_token'] = None
token_cache['expires_at'] = 0
```

#### 9.1.3 顧客が見つからない
**症状**: メッセージ受信しても活動履歴に記録されない
**確認項目**:
1. 顧客のline_user_idが正しく設定されているか
2. UUIDフォーマットが一致しているか

**対処法**:
```bash
# 顧客確認APIの使用
curl http://localhost:3000/check-customer/[USER_ID]
```

### 9.2 デバッグ手順

#### 9.2.1 ログレベルの詳細化
```python
# app.pyに追加
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 9.2.2 リクエスト/レスポンスの確認
```python
# デバッグ用ミドルウェア
@app.before_request
def log_request():
    app.logger.debug(f"Request: {request.method} {request.path}")
    app.logger.debug(f"Headers: {dict(request.headers)}")
    app.logger.debug(f"Body: {request.get_data()}")
```

#### 9.2.3 データベース状態の確認
```bash
# SQLiteコマンドラインツール
sqlite3 database.db

# 顧客一覧
SELECT id, first_name, last_name, line_user_id FROM customers;

# 最新の活動履歴
SELECT * FROM activities ORDER BY timestamp DESC LIMIT 10;
```

## 10. 将来の拡張計画

### 10.1 機能拡張（フェーズ1: 3ヶ月以内）

#### 10.1.1 メッセージタイプの拡張
- **画像メッセージ**: サムネイル表示、S3保存
- **ファイル添付**: ドキュメント管理機能
- **位置情報**: 地図表示統合

#### 10.1.2 自動化機能
- **自動返信**: キーワードベースの自動応答
- **通知機能**: 重要顧客からのメッセージ通知
- **エスカレーション**: 未対応メッセージのアラート

#### 10.1.3 分析・レポート機能
- **ダッシュボード**: 活動統計の可視化
- **レポート生成**: PDF/Excel形式での出力
- **KPI追跡**: 応答時間、メッセージ数等

### 10.2 アーキテクチャ改善（フェーズ2: 6ヶ月以内）

#### 10.2.1 スケーラビリティ
- **データベース**: PostgreSQL/MySQLへの移行
- **キャッシュ**: Redis導入
- **非同期処理**: Celeryによるタスクキュー

#### 10.2.2 マイクロサービス化
- **API分離**: RESTful API独立サービス
- **メッセージング**: RabbitMQ/Kafka導入
- **コンテナ化**: Docker/Kubernetes対応

#### 10.2.3 高可用性
- **ロードバランサー**: 複数インスタンス対応
- **データベースレプリケーション**: 読み取り負荷分散
- **障害復旧**: 自動フェイルオーバー

### 10.3 ビジネス機能拡張（フェーズ3: 1年以内）

#### 10.3.1 CRM機能の充実
- **商談管理**: 案件進捗トラッキング
- **タスク管理**: ToDo/リマインダー機能
- **カレンダー統合**: スケジュール管理

#### 10.3.2 AI/ML統合
- **感情分析**: メッセージのセンチメント分析
- **自動分類**: 問い合わせ内容の自動カテゴライズ
- **予測分析**: 顧客行動予測

#### 10.3.3 外部システム連携
- **Salesforce連携**: データ同期
- **メール統合**: Outlook/Gmail連携
- **他メッセンジャー対応**: Slack/Teams統合

## 11. 付録

### 11.1 環境構築手順

#### 11.1.1 Python環境
```bash
# 仮想環境の作成
python3 -m venv env
source env/bin/activate  # Mac/Linux
# or
env\Scripts\activate     # Windows

# 依存関係のインストール
pip install flask requests pyjwt cryptography
```

#### 11.1.2 プロジェクト構造
```
customer-logger/
├── app.py                 # メインアプリケーション
├── database.db           # SQLiteデータベース
├── private.key           # LINE WORKS認証用秘密鍵
├── requirements.txt      # Python依存関係
├── templates/            # HTMLテンプレート
│   ├── layout.html      # 基本レイアウト
│   ├── company_list.html
│   ├── company_detail.html
│   ├── company_form.html
│   ├── company_edit.html
│   ├── customer_list.html
│   ├── customer_detail.html
│   ├── customer_form.html
│   ├── customer_edit.html
│   └── send_message.html
├── SYSTEM_SPECIFICATION.md  # 本仕様書
├── LINEWORKS_SETUP.md      # LINE WORKS設定手順
└── README.md               # プロジェクト概要
```

### 11.2 設定ファイルサンプル

#### 11.2.1 requirements.txt
```
Flask==2.3.2
requests==2.31.0
PyJWT==2.8.0
cryptography==41.0.3
```

#### 11.2.2 環境変数（.env）※本番環境推奨
```
FLASK_SECRET_KEY=your-secret-key-here
LINE_WORKS_BOT_ID=10368813
LINE_WORKS_CLIENT_ID=ln7VvQ1rBt_msW7j29qs
LINE_WORKS_CLIENT_SECRET=UWD9pXXWd2
LINE_WORKS_DOMAIN_ID=400794821
LINE_WORKS_SERVICE_ACCOUNT=8bvy9.serviceaccount@regit-technology
```

### 11.3 コマンドリファレンス

#### 11.3.1 開発用コマンド
```bash
# アプリケーション起動
python app.py

# ngrok起動
ngrok http 3000

# ログ監視
tail -f app.log | grep -E "(ERROR|WARNING)"

# データベース初期化
python -c "from app import init_db; init_db()"
```

#### 11.3.2 運用コマンド
```bash
# データベースバックアップ
cp database.db backup/database_$(date +%Y%m%d_%H%M%S).db

# プロセス確認
ps aux | grep "python app.py"

# ポート使用確認
lsof -i :3000
```

---

**文書情報**
- バージョン: 1.0
- 最終更新日: 2025年7月8日
- 作成者: システム開発チーム
- レビュー状況: 初版作成完了