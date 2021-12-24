import time
import csv
import sys
import SQL
import twse
import tpex
import DailyTrading
from yahoo_fin.stock_info import *

# 查詢資料SQL語法
query_all = "SELECT sid FROM stock order by sid asc"

def readCSV(csvName):
    list = []
    with open('/Users/rihsianchen/Desktop/project/losscsv/' + csvName, newline='') as csvfile:
        rows = csv.reader(csvfile)
        for row in rows:
            list += row
    return list

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    mytime = time.localtime()
    if mytime.tm_hour > 13:
        datadate = datetime.date.today()
    else :
        datadate = datetime.date.today() - datetime.timedelta(days=1)

    # 1 = only check data
    # 0 = insert data in stock_daily_info
    if (len(sys.argv) > 1):
        checkdata = sys.argv[1]
        # 證交所 - 上市
        twse.process(datadate, checkdata)
        # 櫃買中心 - 上櫃
        tpex.process(datadate, checkdata)
    else:
        print('no input')

    ##### Yahoo API test
    # 交易資料
    # tmp = get_data('2330.TW', '2021-12-20')
    # print(tmp)
    # 收益
    # tmp = get_earnings('2330.TW')
    # print(tmp['quarterly_revenue_earnings'])
    # 顯示下次營收顯示日期
    # tmp = get_next_earnings_date('2379.TW')

    # tmp = get_stats_valuation('2330.TW')
    # print(tmp)


    ### parser test
    # if (sys.argv[1] == 'rev'):
    #     print('run rev process')
    # elif (sys.argv[1] == 'profit'):
    #     print('run profit process')
    # else:
    #     print('run goodinfo')
    #     if (len(sys.argv) > 2):
    #         list = readCSV(sys.argv[2])
    #         print(list)
    #         DailyTrading.process(list)
    #     else:
    #         sids = SQL.Query_command(query_all)
    #         print(sids)
    #         DailyTrading.process(sids)