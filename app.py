import os
import certifi

# 設置證書路徑
os.environ['SSL_CERT_FILE'] = certifi.where()

from flask import Flask, request, abort

# 使用 v3 版本的 SDK
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# 在本地測試時使用硬編碼值（僅用於開發，不要在生產環境中這樣做）
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '您的訪問令牌')
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '您的頻道密鑰')

# 設置配置
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    # 获取X-Line-Signature头值
    signature = request.headers['X-Line-Signature']

    # 獲取請求體
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 驗證簽名
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# @handler.add(MessageEvent, message=TextMessageContent)
# def handle_message(event):
#     # 在v3中回复消息
#     with ApiClient(configuration) as api_client:
#         line_bot_api = MessagingApi(api_client)
#         line_bot_api.reply_message_with_http_info(
#             {
#                 'reply_token': event.reply_token,
#                 'messages': [TextMessage(text=f"你說的是: {event.message.text}")]
#             }
#         )

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text
    
    if text.startswith('/help'):
        reply_text = "可用命令:\n/help - 顯示幫助\n/time - 顯示當前時間"
    elif text.startswith('/time'):
        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        reply_text = f"當前時間是: {now}"
    else:
        reply_text = f"你說的是: {text}"
    
    # 在v3中回复消息的方式
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

# 添加一个健康检查路由
@app.route("/", methods=['GET'])
def health_check():
    return 'Bot is running!'

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
