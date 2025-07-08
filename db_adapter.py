"""
データベースアダプター
SQLiteとPostgreSQLの実装の違いを吸収する
"""
from database import db as database_instance

class DBAdapter:
    def __init__(self):
        self.db = database_instance
        
    def get_connection(self):
        """互換性のため残す"""
        return self.db.get_connection()
    
    def execute(self, query, params=None):
        """SELECT以外のクエリを実行"""
        return self.db.execute_query(query, params)
    
    def fetchall(self, query, params=None):
        """SELECTクエリを実行して全結果を取得"""
        results = self.db.execute_query(query, params)
        # PostgreSQLのRealDictRowをdictに変換
        if self.db.is_postgres and results:
            return [dict(row) for row in results]
        return results
    
    def fetchone(self, query, params=None):
        """SELECTクエリを実行して1件取得"""
        results = self.fetchall(query, params)
        return results[0] if results else None
    
    def insert(self, table, data):
        """データを挿入してIDを返す"""
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['?' for _ in values])
        column_names = ', '.join(columns)
        
        if self.db.is_postgres:
            # PostgreSQLではRETURNING句を使用
            query = f'INSERT INTO {table} ({column_names}) VALUES ({placeholders}) RETURNING id'
            conn = self.db.get_connection()
            cursor = conn.cursor()
            # PostgreSQL用にプレースホルダーを変換
            query = query.replace('?', '%s')
            cursor.execute(query, values)
            result = cursor.fetchone()
            conn.commit()
            last_id = result['id'] if result else None
            conn.close()
            return last_id
        else:
            # SQLiteでは通常のINSERT
            query = f'INSERT INTO {table} ({column_names}) VALUES ({placeholders})'
            return self.db.execute_query(query, values)
    
    def update(self, table, data, where_clause, where_params):
        """データを更新"""
        set_parts = [f"{col} = ?" for col in data.keys()]
        set_clause = ', '.join(set_parts)
        query = f'UPDATE {table} SET {set_clause} WHERE {where_clause}'
        params = list(data.values()) + list(where_params)
        return self.execute(query, params)
    
    def delete(self, table, where_clause, where_params):
        """データを削除"""
        query = f'DELETE FROM {table} WHERE {where_clause}'
        return self.execute(query, where_params)

# シングルトンインスタンス
db_adapter = DBAdapter()