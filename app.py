#20250603_1

from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, FlexSendMessage, PostbackEvent

import threading
import google_sheet  # 匯入google_sheet.py
import reminder

app = Flask(__name__)

#  測試員
#LINE_CHANNEL_ACCESS_TOKEN = "WDZuclPojc3qvkky3UTFWiZqByyD2CZCg7W4nUcAakLtq2UElgColm5yLNcQJjzg88VhfN06YKNSeU0T8HSne+IVW3ENnlSA3A008suYKlypRRRenKssCTGKH3uGT/ztbukbiu5+DcvZVHZcUPtkeAdB04t89/1O/w1cDnyilFU="
#LINE_CHANNEL_SECRET = "7b432f773cac5194ece7799b4be9cb28"


#  小幫手
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

## 針對各指令進行回覆 ##
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):  
    user_message = event.message.text
    user_id_or_group_id = event.source.group_id if event.source.type == "group" else event.source.user_id  # 取得個人或群組 ID
    print(f"收到訊息: {user_message} (來自: {user_id_or_group_id})")

    if user_message == "我的ID": # 取得ID
        reply_text = f"你的 ID 是：\n{user_id_or_group_id}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return
    
    if user_message == "#功能": # 列出"功能"列

        flex_message_json ={"type": "bubble", "size": "micro",
                            "body": {"type": "box", "layout": "vertical", "contents": [
                            {"type": "text", "text": "功能", "size": "xl", "weight": "bold"},
                            {"type": "box", "layout": "vertical", "contents": [
                            {"type": "text", "text": "關鍵字清單", "size": "sm", "action": {
                                "type": "message", "label": "關鍵字清單", "text": "#關鍵字清單" },
                                "align": "center", "color": "#42659A" } ] },
                            {"type": "box", "layout": "vertical", "spacing": "none", "contents": [
                            {"type": "text", "text": "今天吃什麼", "size": "sm", "align": "center", "action": {
                                "type": "message", "label": "今天吃什麼", "text": "#今天吃什麼" },
                                "color": "#42659A" } ] },
                            {"type": "box", "layout": "vertical", "contents": [
                            {"type": "text", "text": "紀錄表", "size": "sm", "align": "center", "action": {
                                "type": "message", "label": "紀錄表", "text": "#紀錄表" },
                                "color": "#42659A" } ] },
                            {"type": "box", "layout": "vertical", "contents": [
                            {"type": "text", "text": "紀錄表_功能說明", "size": "sm", "align": "center", "action": {
                                "type": "message", "label": "紀錄表_功能說明", "text": "#紀錄表_功能說明" },
                                "color": "#42659A" } ] }
                                ],
                                "spacing": "md",
                                "backgroundColor": "#F8D7DA"
                                }
                            }
                            
        flex_message = FlexSendMessage(alt_text="請查看功能選單",contents=flex_message_json)
        line_bot_api.reply_message(event.reply_token, flex_message)
        return

    if user_message == "#關鍵字清單": # 列出所有關鍵字
        reply_message = google_sheet.get_all_keywords(user_id_or_group_id)
        text_message = TextSendMessage(text=reply_message)
        line_bot_api.reply_message(event.reply_token, text_message)
        return

    if user_message == "#紀錄表": # 列出紀錄表
        reply_message = google_sheet.get_reading_records(user_id_or_group_id)
        text_message = TextSendMessage(text=reply_message)
        line_bot_api.reply_message(event.reply_token, text_message)
        return
    
    ## 紀錄表_新增 ##
    if user_message.startswith("#1 ") or user_message.startswith('#新增項目 '):
        print("執行紀錄表_新增")
        reply_message = google_sheet.get_add_records(user_id_or_group_id,user_message)
        text_message = TextSendMessage(text=reply_message)
        line_bot_api.reply_message(event.reply_token, text_message)
        return 
        
    ## 紀錄表_刪除 ##
    if user_message.startswith("#2 ") or user_message.startswith('#刪除項目 '):
        print("執行紀錄表_刪除")
        reply_message = google_sheet.get_delete_records(user_id_or_group_id,user_message)
        text_message = TextSendMessage(text=reply_message)
        line_bot_api.reply_message(event.reply_token, text_message)
        return 

    ## 紀錄表_修改 ##
    if user_message.startswith("#3 ") or user_message.startswith('#修改項目 '):
        print("執行紀錄表_修改")
        reply_message = google_sheet.get_modify_records(user_id_or_group_id,user_message)
        text_message = TextSendMessage(text=reply_message)
        line_bot_api.reply_message(event.reply_token, text_message)
        return  
    

    ## 回覆對應關鍵字 ##
    reply_message = google_sheet.get_response(user_id_or_group_id, user_message)
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

def start_reminder_scheduler():
    thread = threading.Thread(target=reminder.run_scheduler, daemon=True)
    thread.start()

#start_reminder_scheduler()

if __name__ == "__main__":
    start_reminder_scheduler()
    app.run(host="0.0.0.0", port=8000)