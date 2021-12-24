import pymysql

# 資料庫參數設定
db_settings = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "1qazXSW@3edc",
    "db": "sys",
    "charset": "utf8"
}

def Query_command(command, params = None):
    try:
        # 建立Connection物件
        conn = pymysql.connect(**db_settings)
        # 建立Cursor物件
        with conn.cursor() as cursor:

            # 執行query指令
            if params == None:
                cursor.execute(command)
            else:
                cursor.execute(command, (params))
            # 取得所有資料
            result = cursor.fetchall()
            cursor.close()
        return result
    except Exception as ex:
        print(ex)

def Insert_stock_daily_info(command, data):
    try:
        # 建立Connection物件
        conn = pymysql.connect(**db_settings)
        # 建立Cursor物件
        with conn.cursor() as cursor:

            cursor.execute(command, (
            data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10],
            data[11], data[12], data[13], data[14], data[15], data[16]))
            conn.commit()
            cursor.close()
        return 0
    except Exception as ex:
        print(str(data[0]) + ' fail')
        return data[0]

def Update_stock_daily_info(command, data):
    try:
        # 建立Connection物件
        conn = pymysql.connect(**db_settings)
        # 建立Cursor物件
        with conn.cursor() as cursor:

            cursor.execute(command, (
            data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10],
            data[11], data[12], data[13], data[14], data[15], data[16]))
            conn.commit()
            cursor.close()
        return 0
    except Exception as ex:
        print(str(data[0]) + ' fail')
        return data[0]