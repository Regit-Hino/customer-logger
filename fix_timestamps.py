import sqlite3
from datetime import datetime, timezone

# データベースに接続
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# UTC形式のタイムスタンプ（+00:00が含まれるもの）を取得
cursor.execute("""
    SELECT id, timestamp FROM activities 
    WHERE timestamp LIKE '%+00:00%'
""")

records = cursor.fetchall()

print(f"修正対象のレコード数: {len(records)}")

# 各レコードのタイムスタンプを修正
for record_id, timestamp_str in records:
    try:
        # UTCタイムスタンプをパース
        utc_time = datetime.fromisoformat(timestamp_str)
        # ローカルタイムに変換（日本時間 UTC+9）
        local_time = utc_time.replace(tzinfo=timezone.utc).astimezone(tz=None).replace(tzinfo=None)
        
        # データベースを更新
        cursor.execute("""
            UPDATE activities 
            SET timestamp = ? 
            WHERE id = ?
        """, (local_time, record_id))
        
        print(f"ID {record_id}: {timestamp_str} → {local_time}")
        
    except Exception as e:
        print(f"エラー (ID {record_id}): {e}")

# 変更をコミット
conn.commit()
conn.close()

print("タイムスタンプの修正が完了しました。")