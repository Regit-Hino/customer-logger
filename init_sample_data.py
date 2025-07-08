from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import db

def init_sample_data():
    # データベース初期化
    db.init_db()
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 会社データの挿入
    sample_companies = [
        ('株式会社テックイノベーション', '東京都渋谷区道玄坂1-2-3', '03-1234-5678', 'https://tech-innovation.example.com'),
        ('グローバルソリューションズ株式会社', '大阪府大阪市北区梅田2-4-6', '06-9876-5432', 'https://global-solutions.example.com'),
        ('デジタルクリエイティブ合同会社', '福岡県福岡市博多区博多駅前3-5-7', '092-1111-2222', None),
    ]
    
    cursor.executemany('''
        INSERT INTO companies (name, address, phone, website)
        VALUES (?, ?, ?, ?)
    ''', sample_companies)
    
    conn.commit()
    
    # 会社IDを取得
    company_ids = cursor.execute('SELECT id FROM companies').fetchall()
    
    # 顧客データの挿入（会社と紐付け）
    sample_customers = [
        ('太郎', '山田', 'taro.yamada@example.com', '090-1234-5678', 'd83d38ad-a597-48e1-1254-044ff0479ea0', company_ids[0][0]),
        ('花子', '鈴木', 'hanako.suzuki@example.com', '090-8765-4321', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', company_ids[0][0]),
        ('一郎', '佐藤', 'ichiro.sato@example.com', '090-1111-2222', None, company_ids[1][0]),
        ('美香', '田中', 'mika.tanaka@example.com', '090-3333-4444', 'f9e8d7c6-b5a4-3210-fedc-ba0987654321', company_ids[2][0]),
        ('次郎', '高橋', 'jiro.takahashi@example.com', '090-5555-6666', None, company_ids[1][0]),
    ]
    
    cursor.executemany('''
        INSERT INTO customers (first_name, last_name, email, phone, line_user_id, company_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', sample_customers)
    
    conn.commit()
    
    customer_ids = cursor.execute('SELECT id, line_user_id FROM customers WHERE line_user_id IS NOT NULL').fetchall()
    
    sample_activities = []
    for customer_id, line_user_id in customer_ids:
        if line_user_id == 'd83d38ad-a597-48e1-1254-044ff0479ea0':
            sample_activities.extend([
                (customer_id, '新しいプロジェクトについて相談したいです', datetime.now() - timedelta(days=2, hours=3)),
                (customer_id, '見積もりをお願いできますか？', datetime.now() - timedelta(days=1, hours=5)),
                (customer_id, 'ありがとうございます。検討します。', datetime.now() - timedelta(hours=3)),
            ])
        elif line_user_id == 'a1b2c3d4-e5f6-7890-abcd-ef1234567890':
            sample_activities.extend([
                (customer_id, 'サポートの件で連絡しました', datetime.now() - timedelta(days=3)),
                (customer_id, '問題が解決しました。ありがとうございます！', datetime.now() - timedelta(days=1)),
            ])
        elif line_user_id == 'f9e8d7c6-b5a4-3210-fedc-ba0987654321':
            sample_activities.extend([
                (customer_id, '製品の納期について確認したいです', datetime.now() - timedelta(hours=6)),
            ])
    
    cursor.executemany('''
        INSERT INTO activities (customer_id, message, timestamp)
        VALUES (?, ?, ?)
    ''', sample_activities)
    
    conn.commit()
    conn.close()
    
    print("サンプルデータの挿入が完了しました！")
    print(f"- {len(sample_companies)}件の会社データ")
    print(f"- {len(sample_customers)}件の顧客データ")
    print(f"- {len(sample_activities)}件の活動履歴")

if __name__ == '__main__':
    init_sample_data()