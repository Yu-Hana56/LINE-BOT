#20250421

from datetime import datetime
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
    today = datetime.today()
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


# 設定每天 10:00 檢查
def job():
    send_reminder()

# 設定每天 10:00 檢查
schedule.every().day.at("17:15").do(job)

# 持續運行，這裡會保持程序運行直到下一次提醒時間
def run_scheduler():
    while True:
        schedule.run_pending()  # 只檢查待處理的任務
        time.sleep(60)  # 每分鐘檢查一次，確保在預定時間發送提醒

if __name__ == "__main__":
    run_scheduler()