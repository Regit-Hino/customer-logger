#!/bin/bash

echo "=========================================="
echo "🚀 顧客管理システム起動スクリプト"
echo "=========================================="

# 1. Flaskアプリケーションの起動
echo ""
echo "📦 Flask アプリケーションを起動しています..."
python3 app.py &
FLASK_PID=$!
echo "✅ Flask起動完了 (PID: $FLASK_PID)"

# 2. Flaskの起動を待機
echo ""
echo "⏳ サーバーの起動を待っています..."
sleep 3

# 3. サーバーの起動確認
echo ""
echo "🔍 サーバーの動作確認中..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ サーバーは正常に動作しています"
else
    echo "❌ サーバーの起動に失敗しました"
    exit 1
fi

# 4. ngrokの起動
echo ""
echo "🌐 ngrokを起動しています..."
ngrok http 3000 > /dev/null 2>&1 &
NGROK_PID=$!
echo "✅ ngrok起動完了 (PID: $NGROK_PID)"

# 5. ngrokの起動を待機
sleep 3

# 6. ngrok URLの取得
echo ""
echo "🔗 ngrok URLを取得中..."
NGROK_URL=$(curl -s localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)

if [ -z "$NGROK_URL" ]; then
    echo "❌ ngrok URLの取得に失敗しました"
    echo "手動で確認してください: http://localhost:4040"
else
    echo "✅ ngrok URL: $NGROK_URL"
    echo ""
    echo "📋 LINE WORKS Bot設定:"
    echo "   Callback URL: $NGROK_URL/webhook"
fi

# 7. Webhook テスト
echo ""
echo "🧪 Webhook接続テストを実行しますか？ (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "📡 Webhookテストを実行中..."
    TEST_RESULT=$(curl -s -X POST http://localhost:3000/webhook \
        -H "Content-Type: application/json" \
        -d '{
            "type": "message",
            "source": {
                "userId": "test-user-id",
                "domainId": 400794821
            },
            "issuedTime": "'$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")'",
            "content": {
                "type": "text",
                "text": "システム起動テストメッセージ"
            }
        }')
    
    if [ $? -eq 0 ]; then
        echo "✅ Webhookテスト成功"
    else
        echo "❌ Webhookテスト失敗"
    fi
fi

# 8. 起動完了
echo ""
echo "=========================================="
echo "✨ システム起動完了！"
echo ""
echo "📌 アクセスURL:"
echo "   ローカル: http://localhost:3000"
echo "   外部公開: $NGROK_URL"
echo ""
echo "📝 管理画面:"
echo "   顧客一覧: http://localhost:3000/customers"
echo "   ngrok状態: http://localhost:4040"
echo ""
echo "🛑 終了方法: Ctrl+C"
echo "=========================================="

# プロセスの監視
trap "echo ''; echo '🛑 システムを終了しています...'; kill $FLASK_PID $NGROK_PID 2>/dev/null; exit" INT TERM

# 無限ループで待機
while true; do
    sleep 1
done