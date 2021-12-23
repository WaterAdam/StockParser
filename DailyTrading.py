import Goodinfo
import csv
from datetime import date
from datetime import datetime
import SQL
import time

goodinfoURL = "https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID="
# goodinfoURL = "https://google.com.tw?STOCK_ID="

# 確認stock_daily_info已存在最新data
check_data_exist = "SELECT sid, date FROM stock_daily_info where sid = %s order by lid desc limit 1"
# 新增資料SQL語法
insert = "INSERT INTO stock_daily_info(sid, Open, Close, Volume, ChangePrice, ChangePercent, High, Low, AvgPrice, PreviousPrice, ForeignInvVol, InvVol, ForeignTradePercent, InvTradePercent, AvgVol5, AvgVol20, date) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

def process(sids):
    csvName = date.today().strftime("%Y%m%d") + '_loss.csv'
    csvList = []

    for rows in sids:
        for col in rows:
            print("parser id ", col)
            # goodinfo url mapping
            url = goodinfoURL + str(col)
            # get data
            data = Goodinfo.parser_url(url, col)
            if data is None:
                csvList.append([col])
                print(col, ' page data is null')
                break
            # check latest data in DB
            latest = SQL.Query_command(check_data_exist, col)

            # trans string to datetime
            date_url = datetime.strptime(data[-1], "%Y-%m-%d").date()

            # if no stock data in db
            if len(latest) == 0:
                # insert stock_daily_info
                rsp = SQL.Insert_stock_daily_info(insert, data)
                if rsp > 0:
                    csvList.append([col])
                else:
                    print(str(col) + ' OK')
                    time.sleep(5)
            else:
                # update stock_daily_info
                if (latest[0][1] == date_url):
                    print("to do update")
                else:
                    # insert stock_daily_info
                    rsp = SQL.nsert_stock_daily_info(insert, data)
                    if rsp > 0:
                        csvList.append([col])
                    else:
                        print(str(col) + ' OK')
                        time.sleep(10)
    makeCSV(csvName, csvList)

def makeCSV(csvName, csvList):
    # 開啟 CSV 檔案
    with open('/Users/rihsianchen/Desktop/project/losscsv/' + csvName, 'w', newline='') as csvfile:
        # 建立 CSV 檔寫入器
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        # 寫入一列資料
        for line in csvList:
            writer.writerow(line)