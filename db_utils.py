"""
データベースユーティリティ
SQLiteとPostgreSQLの違いを吸収する
"""
import os
from database import db

def get_placeholder():
    """データベースに応じたプレースホルダーを返す"""
    return '%s' if db.is_postgres else '?'

def adapt_query(query):
    """クエリをデータベースに応じて調整"""
    if db.is_postgres:
        # SQLiteの ? を PostgreSQLの %s に変換
        return query.replace('?', '%s')
    return query

def insert_returning_id(table, columns, values):
    """INSERTしてIDを返す（データベース間の違いを吸収）"""
    placeholders = ', '.join([get_placeholder()] * len(values))
    column_names = ', '.join(columns)
    
    if db.is_postgres:
        query = f'INSERT INTO {table} ({column_names}) VALUES ({placeholders}) RETURNING id'
        return db.execute_query(query, values)
    else:
        query = f'INSERT INTO {table} ({column_names}) VALUES ({placeholders})'
        return db.execute_query(query, values)