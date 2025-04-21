#20250421

from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
import schedule
import time
from linebot import LineBotApi
from linebot.models import TextMessage
import google_sheet_20250421  # 匯入 google_sheet 操作模組

#  測試員
#LINE_CHANNEL_ACCESS_TOKEN = "WDZuclPojc3qvkky3UTFWiZqByyD2CZCg7W4nUcAakLtq2UElgColm5yLNcQJjzg88VhfN06YKNSeU0T8HSne+IVW3ENnlSA3A008suYKlypRRRenKssCTGKH3uGT/ztbukbiu5+DcvZVHZcUPtkeAdB04t89/1O/w1cDnyilFU="

#  小幫手
LINE_CHANNEL_ACCESS_TOKEN = "d187fh/lwQnmxlSrJCr9oBnPpiY6PXqtjHj7T23RwqN7xOb5zCOYwE3BAFsZYgsZDgn6SuA/hpRcdHBO5/40cfLUHmHX9G5RcwyhR5Tv1IyReAXtE7/EpeDuAgVjvZ5MpD8WasTWG/iE9iedjXcu4AdB04t89/1O/w1cDnyilFU="


line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# 取得紀錄表中的「名稱」和「截止日期」
def get_due_dates():
    return google_sheet_20250421.get_all_due_dates()  # 從 google_sheet_20250414 取得資料

# 發送提醒訊息
def send_reminder():
    due_dates = get_due_dates()
    today = datetime.now(ZoneInfo("Asia/Taipei")).date()

    user_messages = {}
    for user_id, name, due_date in due_dates:
        days_left = (due_date - today).days +1
        if days_left in [7, 3, 2, 1]:  # 截止日期是 7、3、2、1 天後
            message = f"{name} 剩 {days_left} 天到期!"
            if user_id not in user_messages:
                user_messages[user_id]=[]
            user_messages[user_id].append(message)

    for user_id, messages in user_messages.items():
        message_text = "\n".join(messages)
        if message_text :
            line_bot_api.push_message(user_id, TextMessage(text=message_text))


# 測試提醒使用(本地電腦)
'''
def run_scheduler():
    next_notify_date = datetime.today().date()
    while True:
        now = datetime.now()
        today = now.date()
        current_time = now.time()  # 使用時間對象比較

        if today == next_notify_date and current_time >= datetime.strptime("18:25", "%H:%M").time():
            send_reminder()
            next_notify_date = today + timedelta(days=1)

        time.sleep(60)# 每分鐘檢查一次，確保在預定時間發送提醒
'''

if __name__ == "__main__":
    #run_scheduler() #測試提醒使用(本地電腦)
    send_reminder()
