import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random

# 設定 Google API 權限
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("hana-linebot-e2cfe8a550b3.json", scope) ##筆電用

## Render用 ##
service_account_info = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)

client = gspread.authorize(creds)

# 開啟 Google 試算表
MASTERSHEET_ID = "1pSBcIoa3TegHX4cKJMe49ZpePfHGelhjsjgqVm28sko"
master_sheet = client.open_by_key(MASTERSHEET_ID).worksheet("總表")   

DEFAULT_SPREADSHEET_ID = "1U3ky_sRStMHG7ojrsG88sPnGxjCji8tbs_ukXNMQzLQ" # 預設試算表名ID

# 取得對應 Google 試算表
def get_user_spreadsheet(user_id_or_group_id):
    records = master_sheet.get_all_records()  # 讀取「總表」所有資料
    for row in records:
        if row["user_id/group_id"] == user_id_or_group_id:
            spreadsheet = client.open_by_key(row["試算表 ID"])  # 直接透過試算表 ID 開啟
            return spreadsheet,[s.title for s in spreadsheet.worksheets()] 
    spreadsheet = client.open_by_key(DEFAULT_SPREADSHEET_ID)   # 回傳預設試算表
    return spreadsheet,[s.title for s in spreadsheet.worksheets()] 

def bind_spreadsheet(user_id_or_group_id, new_spreadsheet_id): #更新或新增試算表 ID。
    records = master_sheet.get_all_records()
    for i, row in enumerate(records, start=2):  # 從第 2 列開始
        if row["user_id/group_id"] == user_id_or_group_id:
            master_sheet.update_cell(i, 2, new_spreadsheet_id)  # 更新試算表 ID
            return "試算表已成功更新！"
    master_sheet.append_row([user_id_or_group_id, new_spreadsheet_id])  # 新增一列
    return "試算表已成功綁定！"

def get_response(user_id_or_group_id,user_message):  #回傳對應的回應內容 
    if user_message.startswith("#綁定表單 "):
        new_spreadsheet_id = user_message.replace("#綁定表單 ", "").strip()
        return bind_spreadsheet(user_id_or_group_id, new_spreadsheet_id)

    spreadsheet, sheet_list = get_user_spreadsheet(user_id_or_group_id)
    default_sheet = spreadsheet.worksheet("關鍵字")
    keywords = default_sheet.col_values(1)  # 讀取第一欄（關鍵字）
    response = default_sheet.col_values(2)  # 讀取第二欄（回覆內容）
    if user_message in keywords:
        index = keywords.index(user_message)
        return response[index]
    
    RANDOM_SHEET = {"#今天吃什麼":"餐廳"}
    if user_message in RANDOM_SHEET: # 選餐廳
        sheet_name = RANDOM_SHEET[user_message]
        if sheet_name in sheet_list:
            sheet = spreadsheet.worksheet(sheet_name)
            options = sheet.col_values(1)
            if len(options) > 1:
                return random.choice(options[1:])
            
    if user_message == "#關鍵字清單":
        return get_all_keywords(user_id_or_group_id)
    
    if user_message == "#紀錄表":
        return get_function_options(user_id_or_group_id)

    return None

def get_all_keywords(user_id_or_group_id):    # 讀取所有關鍵字，並回傳
    spreadsheet, _  = get_user_spreadsheet(user_id_or_group_id)
    default_sheet = spreadsheet.worksheet("關鍵字")
    keywords = default_sheet.col_values(1)[1:] 
    return ", ".join(keywords)


def get_function_options(user_id_or_group_id):  #讀取紀錄表中項目欄
    spreadsheet, sheet_list = get_user_spreadsheet(user_id_or_group_id)
    if "紀錄表" in sheet_list:
        sheet = spreadsheet.worksheet("紀錄表")
        data = sheet.get_all_records()

        items = []
        for row in data:
            item = str(row.get("名稱", "")).strip()
            deadline = str(row.get("截止日期", "")).strip()
            if item and deadline:
                items.append((deadline, item))
        if not items: # 避免空回傳
            return "無紀錄"
        items.sort(key=lambda x: x[0])

        result = [f"{d} - {i}" for d, i in items]
        return "\n".join(result)
    return "無紀錄"