#20250426

import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
from datetime import datetime

# 設定 Google API 權限
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

## 筆電用 ##
#creds = ServiceAccountCredentials.from_json_keyfile_name("hana-linebot-e2cfe8a550b3.json", scope) 

## Render用 ##
service_account_info = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)

client = gspread.authorize(creds)

# 開啟 Google 試算表
MASTERSHEET_ID = "1pSBcIoa3TegHX4cKJMe49ZpePfHGelhjsjgqVm28sko"

master_sheet = client.open_by_key(MASTERSHEET_ID).worksheet("總表")   
#master_sheet = client.open_by_key(MASTERSHEET_ID).worksheet("總表_測試員") 

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
    ## 綁定表單 ##
    if user_message.startswith("#綁定表單 "):
        new_spreadsheet_id = user_message.replace("#綁定表單 ", "").strip()
        return bind_spreadsheet(user_id_or_group_id, new_spreadsheet_id)

    spreadsheet, sheet_list = get_user_spreadsheet(user_id_or_group_id)

    ## 紀錄表_新增 ##
    if user_message.startswith("#新增項目 "):
        item = user_message.replace("#新增項目 ", "").strip()
        parts = item.split(" ", 2)
        if len(parts) == 3:
            category = parts[0]  # 類別
            name = parts[1]      # 名稱
            name_date = parts[2] # 日期
            
            if "/" in name_date: # 確認日期格式
                date_parts = name_date.split("/")
                if len(date_parts) == 2: # MM/DD
                    year = datetime.now().year
                    month = int(date_parts[0])
                    day = int(date_parts[1])
                    name_date = f"{year}/{month:02d}/{day:02d}"
                elif len(date_parts) == 3: # YYYY/MM/DD 格式，直接使用
                    year = int(date_parts[0])
                    month = int(date_parts[1])
                    day = int(date_parts[2])
                    if month < 1 or month > 12 or day < 1 or day > 31:
                        return "日期格式不正確，請使用有效的日期 (MM/DD 或 YYYY/MM/DD 格式)。"
                    name_date = f"{year}/{month:02d}/{day:02d}"

            record_sheet = spreadsheet.worksheet("紀錄表")
            record_sheet.append_row([category,name,name_date])
            return "已新增項目!"
        else:
            return "格式錯誤，請使用「#新增項目 類別 名稱 日期」格式。"
        
    ## 紀錄表_刪除 ##
    if user_message.startswith("#刪除項目 "):
        item = user_message.replace("#刪除項目 ", "").strip()
        record_sheet = spreadsheet.worksheet("紀錄表")
        names = record_sheet.col_values(2)  # 讀第一欄名字
        if item in names :
            row_index = names.index(item) +1# index從0開始，row從1開始
            record_sheet.delete_rows(row_index)
            return f"已刪除項目：{item}"
        else :
            return "找不到項目"

    ## 關鍵字回覆 ##
    default_sheet = spreadsheet.worksheet("關鍵字")
    keywords = default_sheet.col_values(1)  # 讀取第一欄（關鍵字）
    response = default_sheet.col_values(2)  # 讀取第二欄（回覆內容）
    if user_message in keywords:
        index = keywords.index(user_message)
        return response[index]
    
    ## 選餐廳 ##
    RANDOM_SHEET = {"#今天吃什麼":"餐廳"}
    if user_message in RANDOM_SHEET: 
        sheet_name = RANDOM_SHEET[user_message]
        if sheet_name in sheet_list:
            sheet = spreadsheet.worksheet(sheet_name)
            options = sheet.col_values(1)
            if len(options) > 1:
                return random.choice(options[1:])
    
    ## 列出關鍵字 ##
    if user_message == "#關鍵字清單":
        return get_all_keywords(user_id_or_group_id)
    
    ## 列出紀錄表 ##
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
    today = datetime.today().date()
    if "紀錄表" in sheet_list:
        sheet = spreadsheet.worksheet("紀錄表")
        data = sheet.get_all_records()

        category_items = {}  # 用來分類

        for row in data:
            category = str(row.get("類別", "")).strip()
            item = str(row.get("名稱", "")).strip()
            deadline = str(row.get("截止日期", "")).strip()
            if category and item and deadline:
                try:
                    deadline_date = datetime.strptime(deadline, "%Y/%m/%d").date()  # 假設格式為 2025/04/25
                    if deadline_date >= today:
                        if category not in category_items :
                            category_items[category]=[]
                        category_items[category].append((deadline_date, item))
                except:
                    pass

        if not category_items: # 避免空回傳
            return "無紀錄"
        
        result = []
        for category in sorted(category_items.keys()):  # 類別排序
            result.append(f"------ {category} ------")
            items = sorted(category_items[category],key=lambda x: x[0])
            for deadline, item in items:
                result.append(f"{deadline} - {item}")

        return "\n".join(result)
    
    return "無紀錄"

def get_all_due_dates(): ## 給reminder用
    all_records = master_sheet.get_all_records()
    all_due_dates = []
    for row in all_records:
        user_id = row["user_id/group_id"]
        spreadsheet, sheet_list = get_user_spreadsheet(user_id)
        if "紀錄表" in sheet_list:
            sheet = spreadsheet.worksheet("紀錄表")
            data = sheet.get_all_records()
            for item in data:
                name = item.get("名稱")
                deadline = item.get("截止日期")
                if name and deadline:
                    try:
                        due_date = datetime.strptime(deadline, "%Y/%m/%d")
                        all_due_dates.append((user_id, name, due_date))
                    except:
                        continue
    all_due_dates.sort(key=lambda x: x[2])
    return all_due_dates