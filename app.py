from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
from datetime import datetime
import json
import requests
import os
import base64

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')  # flash messages用

# データベースパス（環境変数から取得、デフォルトは/tmp）
DATABASE_PATH = os.environ.get('DATABASE_PATH', '/tmp/database.db')

# LINE WORKS設定（環境変数から取得）
LINE_WORKS_CONFIG = {
    'bot_id': os.environ.get('LINE_WORKS_BOT_ID', '10368813'),
    'service_account': os.environ.get('LINE_WORKS_SERVICE_ACCOUNT', '8bvy9.serviceaccount@regit-technology'),
    'client_id': os.environ.get('LINE_WORKS_CLIENT_ID', 'ln7VvQ1rBt_msW7j29qs'),
    'client_secret': os.environ.get('LINE_WORKS_CLIENT_SECRET', 'UWD9pXXWd2'),
    'domain_id': os.environ.get('LINE_WORKS_DOMAIN_ID', '400794821'),
    'token_url': 'https://auth.worksmobile.com/oauth2/v2.0/token',
    'message_url': 'https://www.worksapis.com/v1.0/bots/{bot_id}/users/{user_id}/messages',
    'private_key_file': 'private.key'
}

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 会社テーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            website TEXT
        )
    ''')
    
    # 顧客テーブルの作成（company_idカラムを追加）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            line_user_id TEXT,
            company_id INTEGER,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # 既存のcustomersテーブルにcompany_idカラムが存在しない場合は追加
    cursor.execute("PRAGMA table_info(customers)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'company_id' not in columns:
        cursor.execute('ALTER TABLE customers ADD COLUMN company_id INTEGER REFERENCES companies(id)')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return redirect(url_for('company_list'))

@app.route('/customers')
def customer_list():
    conn = get_db_connection()
    
    # 顧客一覧と活動履歴の有無、会社情報を取得
    customers = conn.execute('''
        SELECT c.*, 
               CASE WHEN COUNT(a.id) > 0 THEN 1 ELSE 0 END as has_activities,
               co.name as company_name
        FROM customers c
        LEFT JOIN activities a ON c.id = a.customer_id
        LEFT JOIN companies co ON c.company_id = co.id
        GROUP BY c.id
        ORDER BY c.last_name, c.first_name
    ''').fetchall()
    
    conn.close()
    return render_template('customer_list.html', customers=customers)

@app.route('/customer/<int:customer_id>')
def customer_detail(customer_id):
    conn = get_db_connection()
    
    # 顧客情報と会社情報を取得
    customer = conn.execute('''
        SELECT c.*, co.name as company_name
        FROM customers c
        LEFT JOIN companies co ON c.company_id = co.id
        WHERE c.id = ?
    ''', (customer_id,)).fetchone()
    
    activities = conn.execute('''
        SELECT * FROM activities 
        WHERE customer_id = ? 
        ORDER BY timestamp ASC
    ''', (customer_id,)).fetchall()
    
    conn.close()
    
    if customer is None:
        return 'Customer not found', 404
    
    return render_template('customer_detail.html', customer=customer, activities=activities)

@app.route('/customer/new', methods=['GET', 'POST'])
def customer_new():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email') or None
        phone = request.form.get('phone') or None
        line_user_id = request.form.get('line_user_id') or None
        company_id = request.form.get('company_id') or None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO customers (first_name, last_name, email, phone, line_user_id, company_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, phone, line_user_id, company_id))
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        
        return redirect(url_for('customer_detail', customer_id=customer_id))
    
    conn = get_db_connection()
    companies = conn.execute('SELECT * FROM companies ORDER BY name').fetchall()
    conn.close()
    
    return render_template('customer_form.html', companies=companies)

@app.route('/customer/<int:customer_id>/edit', methods=['GET', 'POST'])
def customer_edit(customer_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email') or None
        phone = request.form.get('phone') or None
        line_user_id = request.form.get('line_user_id') or None
        company_id = request.form.get('company_id') or None
        
        conn.execute('''
            UPDATE customers 
            SET first_name = ?, last_name = ?, email = ?, phone = ?, line_user_id = ?, company_id = ?
            WHERE id = ?
        ''', (first_name, last_name, email, phone, line_user_id, company_id, customer_id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('customer_detail', customer_id=customer_id))
    
    customer = conn.execute('SELECT * FROM customers WHERE id = ?', (customer_id,)).fetchone()
    companies = conn.execute('SELECT * FROM companies ORDER BY name').fetchall()
    conn.close()
    
    if customer is None:
        return 'Customer not found', 404
    
    return render_template('customer_edit.html', customer=customer, companies=companies)

# 会社関連のルーティング
@app.route('/companies')
def company_list():
    conn = get_db_connection()
    
    # 会社一覧と顧客数を取得
    companies = conn.execute('''
        SELECT c.*, COUNT(cu.id) as customer_count
        FROM companies c
        LEFT JOIN customers cu ON c.id = cu.company_id
        GROUP BY c.id
        ORDER BY c.name
    ''').fetchall()
    
    conn.close()
    return render_template('company_list.html', companies=companies)

@app.route('/company/<int:company_id>')
def company_detail(company_id):
    conn = get_db_connection()
    
    company = conn.execute('SELECT * FROM companies WHERE id = ?', (company_id,)).fetchone()
    
    # この会社に所属する顧客を取得
    customers = conn.execute('''
        SELECT * FROM customers 
        WHERE company_id = ? 
        ORDER BY last_name, first_name
    ''', (company_id,)).fetchall()
    
    conn.close()
    
    if company is None:
        return 'Company not found', 404
    
    return render_template('company_detail.html', company=company, customers=customers)

@app.route('/company/new', methods=['GET', 'POST'])
def company_new():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address') or None
        phone = request.form.get('phone') or None
        website = request.form.get('website') or None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO companies (name, address, phone, website)
            VALUES (?, ?, ?, ?)
        ''', (name, address, phone, website))
        conn.commit()
        company_id = cursor.lastrowid
        conn.close()
        
        return redirect(url_for('company_detail', company_id=company_id))
    
    return render_template('company_form.html')

@app.route('/company/<int:company_id>/edit', methods=['GET', 'POST'])
def company_edit(company_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address') or None
        phone = request.form.get('phone') or None
        website = request.form.get('website') or None
        
        conn.execute('''
            UPDATE companies 
            SET name = ?, address = ?, phone = ?, website = ?
            WHERE id = ?
        ''', (name, address, phone, website, company_id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('company_detail', company_id=company_id))
    
    company = conn.execute('SELECT * FROM companies WHERE id = ?', (company_id,)).fetchone()
    conn.close()
    
    if company is None:
        return 'Company not found', 404
    
    return render_template('company_edit.html', company=company)

# トークンキャッシュ（メモリ内）
token_cache = {
    'access_token': None,
    'expires_at': 0
}

def create_jwt_assertion():
    """Service Account認証用のJWTアサーションを作成"""
    import jwt
    import time
    
    # 環境変数からBase64エンコードされた秘密鍵を取得
    private_key_base64 = os.environ.get('LINE_WORKS_PRIVATE_KEY_BASE64')
    
    if private_key_base64:
        # Base64デコード
        try:
            private_key = base64.b64decode(private_key_base64).decode('utf-8')
            app.logger.info("Private key loaded from environment variable")
        except Exception as e:
            app.logger.error(f"Error decoding private key from Base64: {str(e)}")
            return None
    else:
        # フォールバック：ファイルから読み込む（ローカル開発用）
        key_path = os.path.join(os.path.dirname(__file__), LINE_WORKS_CONFIG['private_key_file'])
        try:
            with open(key_path, 'r') as f:
                private_key = f.read()
            app.logger.info(f"Private key loaded from: {key_path}")
        except FileNotFoundError:
            app.logger.error(f"Private key file not found: {key_path}")
            return None
        except Exception as e:
            app.logger.error(f"Error reading private key: {str(e)}")
            return None
    
    # JWTペイロード
    current_time = int(time.time())
    
    payload = {
        'iss': LINE_WORKS_CONFIG['client_id'],
        'sub': LINE_WORKS_CONFIG['service_account'],  # フルのサービスアカウントIDを使用
        'iat': current_time,
        'exp': current_time + 3600  # 1時間後
    }
    
    app.logger.info(f"JWT payload: {json.dumps(payload, indent=2)}")
    
    # RS256でJWT署名
    try:
        assertion = jwt.encode(payload, private_key, algorithm='RS256')
        return assertion
    except Exception as e:
        app.logger.error(f"JWT encoding error: {str(e)}")
        return None

def get_access_token():
    """Service Account認証でアクセストークンを取得"""
    import time
    
    # キャッシュが有効な場合はそれを返す
    if token_cache['access_token'] and token_cache['expires_at'] > time.time():
        return token_cache['access_token']
    
    # JWTアサーションを作成
    assertion = create_jwt_assertion()
    if not assertion:
        return None
    
    try:
        # トークンリクエスト
        data = {
            'assertion': assertion,
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'client_id': LINE_WORKS_CONFIG['client_id'],
            'client_secret': LINE_WORKS_CONFIG['client_secret'],
            'scope': 'bot'
        }
        
        app.logger.info(f"Requesting token with assertion length: {len(assertion)}")
        
        response = requests.post(
            LINE_WORKS_CONFIG['token_url'],
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        app.logger.info(f"Token response status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            app.logger.info(f"Token response data: {json.dumps(token_data, indent=2)}")
            
            token_cache['access_token'] = token_data.get('access_token')
            # 有効期限を設定（通常1時間なので、安全のため55分後に設定）
            token_cache['expires_at'] = time.time() + (55 * 60)
            
            app.logger.info(f"Access token obtained successfully: {token_cache['access_token'][:20] if token_cache['access_token'] else 'None'}...")
            return token_cache['access_token']
        else:
            app.logger.error(f"Token error: {response.status_code} - {response.text}")
            app.logger.error(f"Request data: {data}")
            return None
            
    except Exception as e:
        app.logger.error(f"Token request exception: {str(e)}")
        return None

# LINE WORKSユーザープロファイル取得
def get_line_works_user_profile(user_id):
    """LINE WORKSのユーザープロファイルを取得"""
    # Service Account認証でトークンを取得
    token = get_access_token()
    if not token:
        app.logger.error("Token is None in get_line_works_user_profile")
        return None
    
    try:
        # ユーザープロファイル取得APIのURL
        url = f"https://www.worksapis.com/v1.0/users/{user_id}"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        app.logger.info(f"Getting user profile from: {url}")
        
        response = requests.get(url, headers=headers)
        
        app.logger.info(f"User profile response status: {response.status_code}")
        app.logger.info(f"User profile response: {response.text}")
        
        if response.status_code == 200:
            profile_data = response.json()
            app.logger.info(f"User profile obtained: {json.dumps(profile_data, ensure_ascii=False)}")
            return profile_data
        else:
            app.logger.error(f"Failed to get user profile: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        app.logger.error(f"Exception getting user profile: {str(e)}")
        return None

# LINE WORKSメッセージ送信
def send_line_works_message(user_id, message):
    """LINE WORKSにメッセージを送信"""
    # Service Account認証でトークンを取得
    token = get_access_token()
    if not token:
        app.logger.error("Token is None in send_line_works_message")
        return False, "アクセストークンの取得に失敗しました"
    
    app.logger.info(f"Got token: {token[:20]}...") # トークンの最初の20文字をログ出力
    
    try:
        url = LINE_WORKS_CONFIG['message_url'].format(
            bot_id=LINE_WORKS_CONFIG['bot_id'],
            user_id=user_id
        )
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'content': {
                'type': 'text',
                'text': message
            }
        }
        
        app.logger.info(f"Sending message to: {url}")
        app.logger.info(f"Message data: {json.dumps(data, ensure_ascii=False)}")
        
        response = requests.post(url, json=data, headers=headers)
        
        app.logger.info(f"Response status: {response.status_code}")
        app.logger.info(f"Response headers: {response.headers}")
        app.logger.info(f"Response body: {response.text}")
        
        if response.status_code in [200, 201]:  # 201も成功とする
            app.logger.info(f"Message sent successfully to user {user_id}")
            return True, "メッセージを送信しました"
        else:
            error_msg = f"送信エラー: {response.status_code} - {response.text}"
            app.logger.error(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"送信例外: {str(e)}"
        app.logger.error(error_msg)
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        return False, error_msg

@app.route('/customer/<int:customer_id>/send', methods=['POST'])
def customer_send_message(customer_id):
    """顧客詳細ページからのメッセージ送信（Ajax対応）"""
    conn = get_db_connection()
    customer = conn.execute('SELECT * FROM customers WHERE id = ?', (customer_id,)).fetchone()
    
    if not customer:
        conn.close()
        return jsonify({'success': False, 'message': '顧客が見つかりません'}), 404
    
    message = request.form.get('message', '').strip()
    
    if not message:
        conn.close()
        return jsonify({'success': False, 'message': 'メッセージを入力してください'}), 400
    
    if not customer['line_user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'この顧客はLINE WORKSと連携されていません'}), 400
    
    # メッセージ送信
    success, result_msg = send_line_works_message(customer['line_user_id'], message)
    
    if success:
        # 送信成功時、活動履歴に記録
        conn.execute('''
            INSERT INTO activities (customer_id, message, timestamp)
            VALUES (?, ?, ?)
        ''', (customer_id, f"[送信] {message}", datetime.now()))
        conn.commit()
        
        app.logger.info(f"Message sent to customer {customer_id} (user_id: {customer['line_user_id']}): {message}")
    
    conn.close()
    return jsonify({'success': success, 'message': result_msg})

@app.route('/send-message/<int:customer_id>', methods=['GET', 'POST'])
def send_message(customer_id):
    conn = get_db_connection()
    customer = conn.execute('''
        SELECT c.*, co.name as company_name
        FROM customers c
        LEFT JOIN companies co ON c.company_id = co.id
        WHERE c.id = ?
    ''', (customer_id,)).fetchone()
    
    if not customer:
        conn.close()
        return 'Customer not found', 404
    
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        
        if not message:
            flash('メッセージを入力してください', 'error')
        elif not customer['line_user_id']:
            flash('この顧客はLINE WORKSと連携されていません', 'error')
        else:
            # メッセージ送信
            success, result_msg = send_line_works_message(customer['line_user_id'], message)
            
            if success:
                # 送信成功時、活動履歴に記録
                conn.execute('''
                    INSERT INTO activities (customer_id, message, timestamp)
                    VALUES (?, ?, ?)
                ''', (customer_id, f"[送信] {message}", datetime.now()))
                conn.commit()
                
                flash(result_msg, 'success')
                app.logger.info(f"Message sent to customer {customer_id}: {message}")
                
                conn.close()
                return redirect(url_for('customer_detail', customer_id=customer_id))
            else:
                flash(result_msg, 'error')
    
    conn.close()
    return render_template('send_message.html', customer=customer)

# APIエンドポイント：任意のuserIdにメッセージ送信
@app.route('/send-message', methods=['POST'])
def send_message_api():
    """LINE WORKSの任意のユーザーにメッセージを送信するAPI"""
    try:
        # JSONボディからパラメータを取得
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'JSONデータが必要です'}), 400
        
        user_id = data.get('userId')
        message = data.get('message')
        
        # バリデーション
        if not user_id:
            return jsonify({'success': False, 'message': 'userIdが必要です'}), 400
        
        if not message:
            return jsonify({'success': False, 'message': 'messageが必要です'}), 400
        
        # メッセージ送信
        success, result_msg = send_line_works_message(user_id, message)
        
        if success:
            app.logger.info(f"API: Message sent to {user_id}: {message}")
            return jsonify({
                'success': True,
                'message': result_msg,
                'userId': user_id,
                'sentMessage': message
            })
        else:
            return jsonify({
                'success': False,
                'message': result_msg,
                'userId': user_id
            }), 500
            
    except Exception as e:
        app.logger.error(f"API error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # デバッグ用：リクエストの詳細情報を記録
        print(f"\n{'='*50}")
        print(f"🔵 WEBHOOK REQUEST RECEIVED at {datetime.now()}")
        print(f"{'='*50}")
        
        # リクエストヘッダー
        headers = dict(request.headers)
        print(f"\n📋 Headers:")
        for key, value in headers.items():
            print(f"  {key}: {value}")
        
        # リクエストボディ
        data = request.get_json()
        print(f"\n📦 Request Body:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        # ログファイルにも記録
        app.logger.info(f"Webhook headers: {headers}")
        app.logger.info(f"Webhook body: {json.dumps(data, ensure_ascii=False)}")
        
        # メッセージタイプの確認
        if data.get('type') == 'message':
            # LINE WORKSのメッセージ形式
            source = data.get('source', {})
            user_id = source.get('userId')  # 送信者のユーザーID（UUID形式）
            
            # コンテンツの取得
            content = data.get('content', {})
            content_type = content.get('type')
            
            # テキストメッセージの処理
            if content_type == 'text':
                message_text = content.get('text', '')
                
                # タイムスタンプの取得（issuedTimeを使用）
                issued_time = data.get('issuedTime')
                if issued_time:
                    # ISO形式の日時をパース（UTCからローカルタイムに変換）
                    from datetime import timezone
                    utc_time = datetime.fromisoformat(issued_time.replace('Z', '+00:00'))
                    # UTCからローカルタイムに変換
                    timestamp = utc_time.replace(tzinfo=timezone.utc).astimezone(tz=None).replace(tzinfo=None)
                else:
                    timestamp = datetime.now()
                
                if user_id and message_text:
                    conn = get_db_connection()
                    
                    # ユーザーIDで顧客を検索（複数の顧客に対応）
                    customers = conn.execute(
                        'SELECT id FROM customers WHERE line_user_id = ?', 
                        (user_id,)
                    ).fetchall()
                    
                    if customers:
                        # すべての該当顧客に活動履歴を記録
                        for customer in customers:
                            conn.execute('''
                                INSERT INTO activities (customer_id, message, timestamp)
                                VALUES (?, ?, ?)
                            ''', (customer['id'], message_text, timestamp))
                        
                        conn.commit()
                        
                        print(f"\n✅ SUCCESS: Activity recorded for {len(customers)} customer(s)")
                        for customer in customers:
                            print(f"  Customer ID: {customer['id']}")
                        print(f"  Message: {message_text}")
                        print(f"  Timestamp: {timestamp}")
                        
                        customer_ids = [str(c['id']) for c in customers]
                        app.logger.info(f"Activity recorded for customers {', '.join(customer_ids)}: {message_text}")
                    else:
                        # 顧客が見つからない場合、新規顧客として自動登録
                        print(f"\n🆕 NEW USER DETECTED")
                        print(f"  LINE WORKS user ID: {user_id}")
                        print(f"  Attempting to fetch user profile...")
                        
                        app.logger.info(f"No customer found for LINE WORKS user ID: {user_id}. Attempting to auto-register.")
                        
                        # ユーザープロファイルを取得
                        profile = get_line_works_user_profile(user_id)
                        
                        if profile:
                            # プロファイル情報から顧客データを作成
                            # 名前の処理（first_name/last_nameの分割が困難な場合はfirst_nameに全体を入れる）
                            user_name = profile.get('name', {})
                            if isinstance(user_name, dict):
                                # 構造化された名前の場合
                                first_name = user_name.get('firstName', '')
                                last_name = user_name.get('lastName', '')
                                if not first_name and not last_name:
                                    # フォールバック：displayNameを使用
                                    display_name = profile.get('displayName', 'Unknown')
                                    first_name = display_name
                                    last_name = ''
                            else:
                                # 文字列の名前の場合（またはdisplayNameを使用）
                                display_name = profile.get('displayName', profile.get('name', 'Unknown'))
                                # スペースで分割を試みる
                                name_parts = display_name.split(' ', 1)
                                if len(name_parts) == 2:
                                    last_name, first_name = name_parts  # 日本式の姓名順を仮定
                                else:
                                    first_name = display_name
                                    last_name = ''
                            
                            # メールアドレスと電話番号
                            email = profile.get('email')
                            phone = profile.get('phoneNumber')
                            
                            # 新規顧客として登録
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT INTO customers (first_name, last_name, email, phone, line_user_id, company_id)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (first_name, last_name, email, phone, user_id, None))
                            
                            new_customer_id = cursor.lastrowid
                            
                            # 活動履歴に最初のメッセージを記録
                            conn.execute('''
                                INSERT INTO activities (customer_id, message, timestamp)
                                VALUES (?, ?, ?)
                            ''', (new_customer_id, message_text, timestamp))
                            
                            conn.commit()
                            
                            print(f"\n✅ NEW CUSTOMER REGISTERED")
                            print(f"  Customer ID: {new_customer_id}")
                            print(f"  Name: {last_name} {first_name}")
                            print(f"  Email: {email or 'N/A'}")
                            print(f"  Phone: {phone or 'N/A'}")
                            print(f"  Message recorded: {message_text}")
                            
                            app.logger.info(f"New customer auto-registered: ID={new_customer_id}, Name={last_name} {first_name}, LINE WORKS ID={user_id}")
                        else:
                            # プロファイル取得失敗時は仮の情報で登録
                            print(f"\n⚠️  User profile fetch failed. Registering with minimal info...")
                            
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT INTO customers (first_name, last_name, email, phone, line_user_id, company_id)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (f"LINE WORKS User ({user_id[:8]}...)", '', None, None, user_id, None))
                            
                            new_customer_id = cursor.lastrowid
                            
                            # 活動履歴に最初のメッセージを記録
                            conn.execute('''
                                INSERT INTO activities (customer_id, message, timestamp)
                                VALUES (?, ?, ?)
                            ''', (new_customer_id, message_text, timestamp))
                            
                            conn.commit()
                            
                            print(f"\n✅ CUSTOMER REGISTERED (with minimal info)")
                            print(f"  Customer ID: {new_customer_id}")
                            print(f"  LINE WORKS ID: {user_id}")
                            print(f"  Message recorded: {message_text}")
                            
                            app.logger.warning(f"Customer registered with minimal info due to profile fetch failure: ID={new_customer_id}, LINE WORKS ID={user_id}")
                    
                    conn.close()
            else:
                app.logger.info(f"Received non-text content type: {content_type}")
        
        # レスポンスの詳細
        print(f"\n🔵 WEBHOOK RESPONSE")
        print(f"  Status: 200 OK")
        print(f"  Body: (empty)")
        print(f"{'='*50}\n")
        
        # LINE WORKSはレスポンスとして200 OKを期待
        return '', 200
    
    except Exception as e:
        print(f"\n❌ ERROR in webhook processing:")
        print(f"  {str(e)}")
        print(f"{'='*50}\n")
        
        app.logger.error(f"Webhook error: {str(e)}")
        # エラーでも200を返す（LINE WORKSの仕様に従う）
        return '', 200

@app.route('/test-webhook', methods=['GET'])
def test_webhook():
    """Webhook処理をテストするためのエンドポイント"""
    import requests
    
    # テスト用のWebhookデータ
    test_data = {
        "type": "message",
        "source": {
            "userId": "d83d38ad-a597-48e1-1254-044ff0479ea0",
            "domainId": 400794821
        },
        "issuedTime": "2025-07-07T11:53:14.443Z",
        "content": {
            "type": "text",
            "text": "テストメッセージ from test endpoint"
        }
    }
    
    # 自分自身のWebhookエンドポイントにPOST
    response = requests.post('http://localhost:3000/webhook', json=test_data)
    
    return jsonify({
        "status": "test completed",
        "webhook_response": response.status_code,
        "test_data": test_data
    })

@app.route('/check-customer/<user_id>')
def check_customer(user_id):
    """指定されたLINE WORKS user_idを持つ顧客を確認"""
    conn = get_db_connection()
    customer = conn.execute(
        'SELECT * FROM customers WHERE line_user_id = ?', 
        (user_id,)
    ).fetchone()
    
    if customer:
        activities = conn.execute(
            'SELECT * FROM activities WHERE customer_id = ? ORDER BY timestamp DESC LIMIT 5',
            (customer['id'],)
        ).fetchall()
        
        result = {
            "customer": dict(customer),
            "recent_activities": [dict(a) for a in activities]
        }
    else:
        result = {"error": f"No customer found with line_user_id: {user_id}"}
    
    conn.close()
    return jsonify(result)

@app.route('/activity/<int:activity_id>/delete', methods=['POST'])
def delete_activity(activity_id):
    """活動履歴を削除"""
    conn = get_db_connection()
    
    # 削除前に顧客IDを取得
    activity = conn.execute(
        'SELECT customer_id FROM activities WHERE id = ?',
        (activity_id,)
    ).fetchone()
    
    if activity:
        # 活動履歴を削除
        conn.execute('DELETE FROM activities WHERE id = ?', (activity_id,))
        conn.commit()
        customer_id = activity['customer_id']
    else:
        customer_id = None
    
    conn.close()
    
    # 削除後は顧客詳細ページにリダイレクト
    if customer_id:
        return redirect(url_for('customer_detail', customer_id=customer_id))
    else:
        return 'Activity not found', 404

@app.route('/test-auto-register', methods=['GET'])
def test_auto_register():
    """未登録ユーザーの自動登録をテストするエンドポイント"""
    import requests
    import uuid
    
    # テスト用の新規ユーザーID（実際には存在しないID）
    test_user_id = str(uuid.uuid4())
    
    # テスト用のWebhookデータ
    test_data = {
        "type": "message",
        "source": {
            "userId": test_user_id,
            "domainId": 400794821
        },
        "issuedTime": datetime.now().isoformat() + "Z",
        "content": {
            "type": "text",
            "text": "新規ユーザー自動登録のテストメッセージ"
        }
    }
    
    # 自分自身のWebhookエンドポイントにPOST
    response = requests.post('http://localhost:3000/webhook', json=test_data)
    
    # 登録されたか確認
    conn = get_db_connection()
    customer = conn.execute(
        'SELECT * FROM customers WHERE line_user_id = ?', 
        (test_user_id,)
    ).fetchone()
    
    if customer:
        activities = conn.execute(
            'SELECT * FROM activities WHERE customer_id = ? ORDER BY timestamp DESC',
            (customer['id'],)
        ).fetchall()
        
        result = {
            "status": "success",
            "message": "新規ユーザーが自動登録されました",
            "customer": dict(customer),
            "activities": [dict(a) for a in activities],
            "webhook_response": response.status_code
        }
    else:
        result = {
            "status": "failed",
            "message": "ユーザーの自動登録に失敗しました",
            "test_user_id": test_user_id,
            "webhook_response": response.status_code
        }
    
    conn.close()
    return jsonify(result)

# アプリケーション起動時の初期化
init_db()

# Gunicorn用にappをエクスポート（WSGIアプリケーションとして）
# ローカル開発時のみFlask組み込みサーバーを使用
if __name__ == '__main__':
    app.run(debug=True, port=3000, host='0.0.0.0')
