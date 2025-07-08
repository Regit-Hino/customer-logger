# 顧客管理システムPoC 要件定義書（Salesforce風 UI）

## 概要

本PoCでは、LINE WORKS の Bot から受信した外部ユーザー発言を、自動で顧客管理システム（CRM）に記録・表示する仕組みを検証する。UIはSalesforce風を想定し、顧客詳細ページに活動履歴を時系列で表示する。

---

## 1. 想定するユーザーと対象

- **対象顧客：**
  - 主に LINE WORKS 上の「外部ユーザー」を想定（将来的に社員対応も可能）
  - 顧客マスタには手動で「line_user_id（発言元ユーザーID）」を設定しておく

---

## 2. 主要オブジェクトと構成

### 2.1 顧客（Customer）

| 項目名           | 型        | 説明                           |
|------------------|-----------|--------------------------------|
| `id`             | integer   | 主キー                         |
| `first_name`     | text      | 名                             |
| `last_name`      | text      | 姓                             |
| `email`          | text      | メールアドレス                 |
| `phone`          | text      | 電話番号                       |
| `line_user_id`   | text      | LINE WORKSの送信者ID（紐付け）|

---

### 2.2 活動履歴（Activity）

| 項目名           | 型        | 説明                             |
|------------------|-----------|----------------------------------|
| `id`             | integer   | 主キー                           |
| `customer_id`    | integer   | 紐づく顧客ID（外部キー）          |
| `message`        | text      | ユーザーの発言内容                |
| `timestamp`      | datetime  | 発言日時                          |

---

## 3. 主な機能一覧

### 3.1 顧客詳細ページ（UI）

- 顧客の基本情報を表示
- 右カラムに「活動履歴」を時系列で表示（直近が上に表示される）
- LINE WORKSからの発言は、自動的に履歴として追加される

### 3.2 LINE WORKS Bot連携

- Flaskで `/webhook` エンドポイントを公開
- ngrokで外部公開し、LINE WORKS Bot からのメッセージを受信
- `line_user_id` を使って該当顧客を検索し、活動履歴に追加

---

## 4. 技術構成

| 要素        | 使用技術               |
|-------------|------------------------|
| Webフレームワーク | Flask                  |
| DB           | SQLite                 |
| テンプレート | Jinja2（Flask標準）     |
| フロント     | Bootstrap（CDNでOK）   |
| 外部連携     | LINE WORKS Bot + ngrok |

---

## 5. フォルダ構成（例）
customer-logger/
├── app.py
├── requirements.md
├── database.db
├── templates/
│ ├── layout.html
│ ├── customer_list.html
│ └── customer_detail.html


---

## 6. 今後の拡張案（将来的に対応）

- 顧客登録時に自動で line_user_id を取得・紐付け
- LINE発言以外の「担当者による手動記録」も履歴に追加
- ファイル・画像の投稿ログなども管理対象に拡張

---

## 備考

- PoCでは **line_user_id を手動で設定する運用** で問題ない
- セキュリティや認証機能は今回は不要

