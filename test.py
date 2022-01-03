import SQL
import DailyTrading
from yahoo_fin.stock_info import *

# 查詢資料SQL語法
query_all = "SELECT sid FROM stock order by sid asc"

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