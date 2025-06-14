#20250603_1
## 修改"#3 "時，後台print的結果
## 修改"#紀錄表"，加上表頭

#20250603_2
## 修改"#紀錄表#，取消日期與名稱中間的"-"

import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
from zoneinfo import ZoneInfo
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
    
    ## 列出紀錄表_功能說明 ##
    if user_message == "#紀錄表_功能說明":
        return ("新增項目➡️\n"
                "　輸入「#1 」or 「#新增項目 」\n"
                "　加上「名稱 日期 數量」\n"
                "　例如:#1 冷藏 汽水 2025/04/27 6 \n"
                "刪除項目➡️\n"
                "　輸入「#2 」or「#刪除項目 」\n"
                "　加上「名稱(編號)」\n"
                "　例如:#2 汽水\n"
                "修改項目➡️\n"
                "　輸入「#3 」or「#修改項目 」\n"
                "　加上「名稱(編號) 欄位 修改後內容」\n"
                "　例如:#3 汽水 數量 5")
    return None

def get_all_keywords(user_id_or_group_id):    # 讀取所有關鍵字，並回傳
    spreadsheet, _  = get_user_spreadsheet(user_id_or_group_id)
    default_sheet = spreadsheet.worksheet("關鍵字")
    keywords = default_sheet.col_values(1)[1:] 
    return ", ".join(keywords)

def get_reading_records(user_id_or_group_id, command_type="list"):  #讀取紀錄表中項目欄
    spreadsheet, sheet_list = get_user_spreadsheet(user_id_or_group_id)
    today = datetime.now(ZoneInfo("Asia/Taipei")).date()
    if "紀錄表" in sheet_list:
        sheet = spreadsheet.worksheet("紀錄表")
        data = sheet.get_all_records()

        category_items = {}  # 用來分類
        expired_items = []
        for row in data:
            category = str(row.get("類別", "")).strip()
            item = str(row.get("名稱", "")).strip()
            deadline = str(row.get("日期", "")).strip()
            quantity = str(row.get("數量", "")).strip()
            if category and item and deadline:
                try:
                    deadline_date = datetime.strptime(deadline, "%Y/%m/%d").date()  # 假設格式為 2025/04/25
                    if deadline_date >= today:
                        if category not in category_items :
                            category_items[category]=[]
                        category_items[category].append((deadline_date, item, quantity))
                    elif deadline_date < today:
                        expired_items.append((deadline_date, item, quantity))
                
                except:
                    pass

        if not category_items and not expired_items: # 避免空回傳
            return "無紀錄"
        
        if command_type == "list":
            result = []
            item_counter = 1  # 編號從 1 開始
            first_category = True
              
            for category in sorted(category_items.keys()):  # 類別排序
                if first_category == True:
                    result.append(f"------ {category} ------")
                    first_category = False
                else:
                    result.append(f"\n------ {category} ------")

                result.append("No. |    日期     |   名稱   | 數量")
                items = sorted(category_items[category],key=lambda x: x[0])
                for deadline, item, quantity in items:
                    deadline = deadline.strftime("%Y/%m/%d")
                    if quantity.startswith("1") or quantity == "":
                        result.append(f"{item_counter}. {deadline} {item}")
                    else:
                        result.append(f"{item_counter}. {deadline} {item} *{quantity}")
                    item_counter += 1

            if expired_items: # 處理已過期資料
                result.append("\n------ 已過期 ------")
                result.append("No. |    日期     |   名稱   | 數量")
                expired_items.sort(key=lambda x: x[0])
                for deadline, item, quantity in expired_items:
                    deadline = deadline.strftime("%Y/%m/%d")
                    if quantity.startswith("1") or quantity == "":
                        result.append(f"{item_counter}. {deadline} {item}")
                    else:
                        result.append(f"{item_counter}. {deadline} {item} *{quantity}")
                    item_counter += 1

            return "\n".join(result)
        
        elif command_type == "delete" or command_type == "modify" :
            # 返回紀錄字典，這樣可以在刪除時使用
            records = []
            for category in sorted(category_items.keys()):
                items = sorted(category_items[category], key=lambda x: x[0])
                for deadline, item, quantity in items:
                    records.append({"name": item, "category": category, "deadline": deadline, "quantity": quantity})
            if expired_items:
                expired_items.sort(key=lambda x: x[0])
                for deadline, item, quantity in expired_items:
                    records.append({"name": item, "category": "已過期", "deadline": deadline, "quantity": quantity})
            return records

    return "無紀錄"

def get_add_records(user_id_or_group_id,user_message): #新增紀錄表項目
    spreadsheet, _ = get_user_spreadsheet(user_id_or_group_id)
    if user_message.startswith("#1 "):
        item = user_message.replace("#1 ", "", 1).strip()
    elif user_message.startswith("#新增項目 "):
        item = user_message.replace("#新增項目 ", "", 1).strip()
    parts = item.split(" ") # 依照空格進行分割(類別 名稱 日期 數量)
    if len(parts) == 3:
        category = parts[0]  # 類別
        name = parts[1]      # 名稱
        name_date = parts[2] # 日期
        quantity = 1 #數量預設1
    
    elif len(parts) == 4:
        category = parts[0]  # 類別
        name = parts[1]      # 名稱
        name_date = parts[2] # 日期
        quantity = parts[3] #數量
        if not quantity.isdigit():
            return "數量請輸入正整數！"
        quantity = int(quantity)
    else:
        return "格式錯誤，請使用「#1 類別 名稱 日期 數量」格式。"
            
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
    record_sheet.append_row([category,name,name_date,quantity])
    return f"已新增 ({category}) {name} {name_date}"
    
def get_delete_records(user_id_or_group_id,user_message): #刪除紀錄表項目
    spreadsheet, _ = get_user_spreadsheet(user_id_or_group_id)
    if user_message.startswith("#2 "):
        item = user_message.replace("#2 ", "", 1).strip()
    elif user_message.startswith("#刪除項目 "):
        item = user_message.replace("#刪除項目 ", "", 1).strip()

    delete_list = item.split(" ") #分析刪除紀錄表資料
    deleted_items = [] #放已刪除的項目
    failed_items = []  # 找不到的
    record_sheet = spreadsheet.worksheet("紀錄表")
    records = get_reading_records(user_id_or_group_id,command_type = "delete")
    headers = ["name", "category", "deadline", "quantity"]
    print("編號｜" + "｜".join(headers))
    for i, record in enumerate(records, start=1):
        row = [str(record.get(key, "")) for key in headers]
        print(f"{i}｜" + "｜".join(row))

    names = record_sheet.col_values(2)  # 第二欄是名字
    for item in delete_list:
        if item.isdigit():  # 輸入的是編號
            record_id = int(item)
            if record_id <= len(records): #確保有編號
                delete_id = records[record_id - 1]
                item_name = delete_id['name']
                item_deadline = delete_id['deadline']
            else:
                failed_items.append(f"編號 {record_id} (無效編號)")
                continue  # 出錯就跳下一個

        else:
            if item in names :
                # 篩選出所有相同名稱的項目
                same_name_items = [record for record in records if record['name'] == item]
                # 按照日期從舊到新排序
                same_name_items.sort(key=lambda x: x['deadline'])
                oldest_item = same_name_items[0] # 刪除最舊的項目
                item_name = oldest_item['name']
                item_deadline = oldest_item['deadline']
            else :
                failed_items.append(f"{item} (找不到項目)")
                continue  # 出錯就跳下一個
    
        all_rows = record_sheet.get_all_values()
        found_row = None
        for idx, row in enumerate(all_rows[1:], start=2):  # 跳過標題列
            row_name = row[1]
            row_deadline = row[2]
            if row_name == item_name and row_deadline == item_deadline.strftime("%Y/%m/%d"):
                found_row = idx
                break

        if found_row:
            record_sheet.delete_rows(found_row)
            deleted_items.append(f"{item_name} (日期: {item_deadline.strftime('%Y/%m/%d')})")
        else:
            failed_items.append(f"{item_name} (找不到符合的項目)")

    result = ""
    if deleted_items:
        result += "✅ 已刪除：\n" + "\n".join(deleted_items)
    if failed_items:
        result += "\n\n⚠️ 找不到：\n" + "\n".join(failed_items)

    return result.strip()
    
def get_modify_records(user_id_or_group_id,user_message): #刪除紀錄表項目
    spreadsheet, _ = get_user_spreadsheet(user_id_or_group_id)
    if user_message.startswith("#3 "):
        item = user_message.replace("#3 ", "", 1).strip()
    elif user_message.startswith("#修改項目 "):
        item = user_message.replace("#修改項目 ", "", 1).strip()
    parts  = item.split(" ") #只切割兩次確保資料會是 名稱(編號)、欄位、修改後內容
    if len(parts) < 3 :
        return "格式錯誤，請使用「#3 名稱 欄位 修改後內容」格式。"
    name = parts[0]
    fields = parts[1]
    change = " ".join(parts[2:]).strip()
    change = change.replace(" ","")
    record_sheet = spreadsheet.worksheet("紀錄表")
    records = get_reading_records(user_id_or_group_id,command_type = "modify")
    
    fields_row = record_sheet.row_values(1)  #讀取標題列
    if fields in fields_row:
        col_index = fields_row.index(fields) + 1
    else:
        return f"找不到 {fields} 欄位"
    
    if name.isdigit():  # 輸入的是編號
        record_id = int(name)
        if record_id <= len(records): #確保有編號
            delete_id = records[record_id -1]
            name = delete_id['name']
        else:
            return "無效的編號，請重新輸入有效的編號。"
        
    names = record_sheet.col_values(2)  # 讀第一欄名字
    if name in names :# 找到行數
        row_index = names.index(name) +1# index從0開始，row從1開始
    else :
        return "找不到項目"
    
    record_sheet.update_cell(row_index, col_index, change)
    return f"已將「{name}」的「{fields}」修改為「{change}」。"
    
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
                deadline = item.get("日期")
                if name and deadline:
                    try:
                        due_date = datetime.strptime(deadline, "%Y/%m/%d")
                        all_due_dates.append((user_id, name, due_date))
                    except:
                        continue
    all_due_dates.sort(key=lambda x: x[2])
    return all_due_dates