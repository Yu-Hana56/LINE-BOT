#20250422_2

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
    return google_sheet_20250421.get_all_due_dates()

# 發送提醒訊息
def send_reminder():
    due_dates = get_due_dates()
    today = datetime.now(ZoneInfo("Asia/Taipei")).date()

    user_messages = {}
    for user_id, name, due_date in due_dates:
        due_date = due_date.date()
        days_left = (due_date - today).days
        if user_id not in user_messages: # 建立各user_id的messages
            user_messages[user_id] = {
                'normal_messages': [],
                'extra_messages': [],
                'seven_message': []
            }

        if days_left in [0, 1, 2, 3]: # 檢查剩0~3天
            if days_left == 0:  # 剩餘0天
                message = f"{name} 於今天到期!"
            elif days_left == 1:  # 剩餘1天
                message = f"{name} 於明天到期!"
            else:  # 剩餘2、3天
                message = f"{name} 於 {days_left} 天後到期!"
            user_messages[user_id]['normal_messages'].append(message)

        elif days_left in  [4, 5, 6]: # 檢查剩4~6天
            message = f"{name} 於 {days_left} 天後到期!"
            user_messages[user_id]['extra_messages'].append(message)

        if days_left == 7: # 檢查剩7天
            message = f"{name} 於 {days_left} 天後到期!"
            user_messages[user_id]['seven_message'].append(message)

    # 處理每個user_id的訊息
    for user_id, messages in user_messages.items():
        notify = []
        if messages['normal_messages'] or messages['seven_message']: # 若0 1 2 3 7有值就全部加總
            notify.extend(messages['normal_messages'])
            notify.extend(messages['extra_messages'])
            notify.extend(messages['seven_message'])

        if notify :
            message_text = "\n".join(messages)
            line_bot_api.push_message(user_id, TextMessage(text=message_text))


# 測試提醒使用(本地電腦)
'''
def run_scheduler():
    next_notify_date = datetime.today().date()
    while True:
        now = datetime.now()
        today = now.date()
        current_time = now.time()  # 使用時間對象比較

        if today == next_notify_date and current_time >= datetime.strptime("15:10", "%H:%M").time():
            send_reminder()
            next_notify_date = today + timedelta(days=1)

        time.sleep(60)# 每分鐘檢查一次，確保在預定時間發送提醒
'''

if __name__ == "__main__":
    #run_scheduler() #測試提醒使用(本地電腦)
    send_reminder()
