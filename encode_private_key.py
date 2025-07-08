#!/usr/bin/env python3
"""
private.keyファイルをBase64エンコードしてRenderの環境変数として使用できる形式に変換する

使い方:
    python3 encode_private_key.py
    
出力されたBase64文字列をRenderの環境変数LINE_WORKS_PRIVATE_KEY_BASE64に設定してください。
"""

import base64
import os
import sys

def encode_private_key():
    """private.keyファイルをBase64エンコードする"""
    key_path = 'private.key'
    
    # ファイルの存在確認
    if not os.path.exists(key_path):
        print(f"エラー: {key_path} が見つかりません")
        print("カレントディレクトリにprivate.keyファイルを配置してください")
        sys.exit(1)
    
    try:
        # private.keyを読み込む
        with open(key_path, 'r') as f:
            private_key_content = f.read()
        
        # Base64エンコード
        encoded = base64.b64encode(private_key_content.encode('utf-8')).decode('ascii')
        
        print("=== private.key のBase64エンコード結果 ===")
        print("\n以下の文字列をRenderの環境変数 LINE_WORKS_PRIVATE_KEY_BASE64 に設定してください:\n")
        print(encoded)
        print("\n" + "=" * 50)
        
        # 確認のため、最初の50文字と最後の50文字を表示
        if len(encoded) > 100:
            print(f"\n確認: {encoded[:50]}...{encoded[-50:]}")
        
        print(f"\n文字数: {len(encoded)} 文字")
        
        # ファイルにも保存（オプション）
        output_file = 'private_key_base64.txt'
        with open(output_file, 'w') as f:
            f.write(encoded)
        print(f"\nBase64エンコード結果を {output_file} にも保存しました")
        print("※ このファイルは機密情報なので、Gitにコミットしないでください")
        
    except Exception as e:
        print(f"エラー: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    encode_private_key()
