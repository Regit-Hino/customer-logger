"""
データベース接続管理モジュール
SQLiteとPostgreSQLの両方に対応
"""
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

class DatabaseConnection:
    """データベース接続を管理するクラス"""
    
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        self.is_postgres = bool(self.database_url and self.database_url.startswith('postgres'))
        
        # RenderのPostgreSQLはpostgres://で始まるが、psycopg2はpostgresql://を要求する
        if self.is_postgres and self.database_url.startswith('postgres://'):
            self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
    
    def get_connection(self):
        """データベース接続を取得"""
        if self.is_postgres:
            return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
        else:
            # SQLite（ローカル開発用）
            db_path = os.environ.get('DATABASE_PATH', 'database.db')
            conn = sqlite3.connect(db_path)
            # Row形式をdictに変換する関数
            def dict_factory(cursor, row):
                d = {}
                for idx, col in enumerate(cursor.description):
                    d[col[0]] = row[idx]
                return d
            conn.row_factory = dict_factory
            return conn
    
    def init_db(self):
        """データベースを初期化"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.is_postgres:
            # PostgreSQL用のテーブル作成
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT,
                    phone TEXT,
                    website TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id SERIAL PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    line_user_id TEXT,
                    company_id INTEGER REFERENCES companies(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activities (
                    id SERIAL PRIMARY KEY,
                    customer_id INTEGER NOT NULL REFERENCES customers(id),
                    message TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                )
            ''')
        else:
            # SQLite用のテーブル作成
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    phone TEXT,
                    website TEXT
                )
            ''')
            
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
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query, params=None):
        """クエリを実行して結果を返す"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # PostgreSQL用にクエリを変換
        if self.is_postgres:
            query = query.replace('?', '%s')
            # AUTOINCREMENT を SERIAL に変換（CREATE TABLE用）
            query = query.replace('AUTOINCREMENT', '')
            # DATETIME を TIMESTAMP に変換
            query = query.replace('DATETIME', 'TIMESTAMP')
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
            conn.close()
            return results
        else:
            conn.commit()
            if query.strip().upper().startswith('INSERT'):
                if self.is_postgres:
                    # PostgreSQLはRETURNING句でIDを取得
                    last_id = cursor.fetchone()['id'] if cursor.rowcount > 0 else None
                else:
                    # SQLiteはlastrowidを使用
                    last_id = cursor.lastrowid
                conn.close()
                return last_id
            conn.close()
            return cursor.rowcount
    
    def execute_many(self, query, params_list):
        """複数のクエリを実行"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
        conn.close()

# シングルトンインスタンス
db = DatabaseConnection()