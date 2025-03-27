from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, FlexSendMessage, PostbackEvent
#import json

import google_sheet_20250328  # 匯入google_sheet.py

google_sheet = google_sheet_20250328
app = Flask(__name__)

#  Channel Access Token 和 Channel Secret
LINE_CHANNEL_ACCESS_TOKEN = "d187fh/lwQnmxlSrJCr9oBnPpiY6PXqtjHj7T23RwqN7xOb5zCOYwE3BAFsZYgsZDgn6SuA/hpRcdHBO5/40cfLUHmHX9G5RcwyhR5Tv1IyReAXtE7/EpeDuAgVjvZ5MpD8WasTWG/iE9iedjXcu4AdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "18629adaf5a3b0aaf8572849c66e23da"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE Bot 啟動中！"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "驗證失敗", 400
    return "OK", 200

##關鍵字回覆##
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):  
    user_message = event.message.text
    user_id_or_group_id = event.source.group_id if event.source.type == "group" else event.source.user_id  # 取得個人或群組 ID
    print(f"收到訊息: {user_message} (來自: {user_id_or_group_id})")

    if user_message == "我的ID": #  取得id
        reply_text = f"你的 ID 是：\n{user_id_or_group_id}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return
    
    reply_message = google_sheet.get_response(user_id_or_group_id, user_message)
    
    if user_message == "功能":

        flex_message_json ={"type": "bubble",
                            "body": {"type": "box","layout": "vertical","contents": [
                            {"type": "text","text": "功能","weight": "bold","size": "xl"}
                            ]},
                            "footer": {"type": "box","layout": "vertical","spacing": "sm","contents": [
                            {"type": "button","style": "link","height": "sm","action": {
                            "type": "message","label": "關鍵字清單","text": "#關鍵字清單"}},

                            {"type": "button","style": "link","height": "sm","action": {
                            "type": "message","label": "小幫手選午餐","text": "小幫手選午餐"}},

                            {"type": "button","style": "link","height": "sm","action": {
                            "type": "message","label": "紀錄表","text": "#紀錄表"}}
                            ],"flex": 0},
                            "styles": {
                            "body": {"backgroundColor": "#F8D7DA"},
                            "footer": {"backgroundColor": "#F8D7DA"}
                            }
                        }
        
        flex_message = FlexSendMessage(alt_text="請查看功能選單",contents=flex_message_json)
        line_bot_api.reply_message(event.reply_token, flex_message)
        return

    if user_message == "#關鍵字清單":
        reply_message = google_sheet.get_all_keywords(user_id_or_group_id)
        text_message = TextSendMessage(text=reply_message)
        line_bot_api.reply_message(event.reply_token, text_message)
        return

    if user_message == "#紀錄表":
        reply_message = google_sheet.get_record_data(user_id_or_group_id)
        text_message = TextSendMessage(text=reply_message)
        line_bot_api.reply_message(event.reply_token, text_message)
        return

    if reply_message:
        if reply_message.startswith("http"):
            image_message = ImageSendMessage(
                original_content_url=reply_message, 
                preview_image_url=reply_message
            )
            line_bot_api.reply_message(event.reply_token, image_message)
        else:
            text_message = TextSendMessage(text=str(reply_message))
            line_bot_api.reply_message(event.reply_token, text_message)

@handler.add(PostbackEvent)
def handle_postback(event):
    postback_data = event.postback.data
    user_id_or_group_id = event.source.group_id if event.source.type == "group" else event.source.user_id  # 取得個人或群組 ID
    print(f"收到 Postback: {postback_data} (來自: {user_id_or_group_id})")
    if postback_data.startswith("get_function_details"):
        option = postback_data.split(":", 1)[1].strip()  # 取得項目名稱
        reply_message = google_sheet.get_function_details(user_id_or_group_id, option)

    if reply_message:
        if isinstance(reply_message, str):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
        else:
            line_bot_api.reply_message(event.reply_token, reply_message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)