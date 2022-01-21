import time
import SQL
import twse
import tpex
import twse_index
import tpex_index
import datetime
import pandas as pd
import sys
from flask import Flask, request, render_template

order_list = ["ForeignTradePercent", "InvTradePercent", "ForeignInvVol", "InvVol"]

# 取得最新資料時間(每日16:00開始才會有法人進出data)
def getNowTime():
    mytime = time.localtime()
    if mytime.tm_hour > 15:
        datadate = datetime.date.today()
    else:
        datadate = datetime.date.today() - datetime.timedelta(days=1)
    return datadate

app = Flask(__name__)

@app.route("/")
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

# 檢查上市櫃是否已經有data
@app.route('/check', methods=['POST'])
def check():
    datadate = getNowTime();
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
        #  利用request取得表單欄位值
        if (request.values['act'] == 'checkTWSE'):
            print('check twse')
            file = twse.process(datadate, '1')
        else:
            print('check tpex')
            file = tpex.process(datadate, '1')

        a = pd.read_csv(file)
        html_file = a.to_html()
    return {'data':html_file, 'date':datadate.strftime("%Y-%m-%d")}

# 將當日證交所/櫃買中心的指數&個股資訊寫入DB
@app.route('/insert', methods=['POST'])
def insert():
    datadate = getNowTime();
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
        twse_index.process(datadate, '0')
        tpex_index.process(datadate, '0')
        file_twse = twse.process(datadate, '0')
        file2_tpex = tpex.process(datadate, '0')

        query_today = "SELECT i.sid, s.name, i.ForeignInvVol, InvVol, ForeignTradePercent, InvTradePercent, close, ChangePercent, Volume, AvgVol5, AvgVol20 from stock_daily_info as i " \
                      "inner join stock as s on s.sid = i.sid " \
                      "where date = %s"

        # check latest data in DB
        data = SQL.Query_command(query_today, datadate)
        # df = pd.DataFrame(data)
        df = pd.DataFrame(data, columns=['股號', '股名', '外資買賣超', '投信買賣超', '外本比', '投本比', '收盤', '漲跌%', '成交量', '5日均量', '20日均量'])

        # a = pd.read_csv(file)
        html_file = df.to_html()
    return {'data':html_file, 'date':datadate.strftime("%Y-%m-%d")}

# show出每日排名, 分別是外本比、投本比、外資買超、投信買超排名
# 並整合在同一個table內，方便直接貼上
@app.route('/raw_data_rank', methods=['POST'])
def raw_data_rank():
    datadate = getNowTime();
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
        df = pd.DataFrame(columns=['股號', '股名', '外資買賣超', '投信買賣超', '外本比', '投本比', '收盤', '漲跌%', '成交量', '5日均量', '20日均量', '本益比'])
        for order in order_list:
            query_rank = "SELECT i.sid, s.name, i.ForeignInvVol, InvVol, ForeignTradePercent, InvTradePercent, close, ChangePercent, Volume, AvgVol5, AvgVol20, per from stock_daily_info as i " \
                      "inner join stock as s on s.sid = i.sid " \
                      "where date = %s " \
                      "order by " + order + " desc limit 20"
            # check latest data in DB
            data = SQL.Query_command(query_rank, datadate)
            tmp = pd.DataFrame(data, columns=['股號', '股名', '外資買賣超', '投信買賣超', '外本比', '投本比', '收盤', '漲跌%', '成交量', '5日均量', '20日均量', '本益比'])
            df = df.append(tmp)

        html_file = df.to_html()
    return {'data':html_file, 'date':datadate.strftime("%Y-%m-%d")}

@app.route('/insert_interval', methods=['GET', 'POST'])
def insert_interval():
    return render_template('insert_interval.html')

# 選擇時間區間，並寫入該時段內的個股收盤資訊
@app.route('/insert_with_interval', methods=['POST'])
def insert_with_interval():
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
        begin = request.values['begin']
        end = request.values['end']
        done_date = ''
        fail_date = ''
        print("time interval is %s to %s" % (begin, end))

        a = pd.date_range(start=begin, end=end)
        # display only date using date() function
        for i in a:
            print(i.date())
            rsp_twse = twse.process(i.date(), '0')
            rsp_tpex = tpex.process(i.date(), '0')
            if (rsp_twse & rsp_tpex):
                done_date += "%s \n" % i.date().strftime("%Y-%m-%d")
            else:
                fail_date += "%s \n" % i.date().strftime("%Y-%m-%d")

    return {'done':done_date, 'fail':fail_date}

@app.route('/insert_index_interval', methods=['GET', 'POST'])
def insert_index_interval():
    return render_template('insert_index_interval.html')

# 選擇時間區間，並寫入該時段內的大盤收盤資訊
@app.route('/insert_index_with_interval', methods=['POST'])
def insert_index_with_interval():
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
        begin = request.values['begin']
        end = request.values['end']
        done_date = ''
        fail_date = ''
        print("time interval is %s to %s" % (begin, end))

        a = pd.date_range(start=begin, end=end)
        # display only date using date() function
        for i in a:
            print(i.date())
            rsp_twse = twse_index.process(i.date(), '0')
            rsp_tpex = tpex_index.process(i.date(), '0')
            if (rsp_twse & rsp_tpex):
                done_date += "%s \n" % i.date().strftime("%Y-%m-%d")
            else:
                fail_date += "%s \n" % i.date().strftime("%Y-%m-%d")

            time.sleep(15)

    return {'done':done_date, 'fail':fail_date}

@app.route('/pair_trade', methods=['GET', 'POST'])
def pair_trade():
    return render_template('pair_trade.html')

# 配對交易
@app.route('/ajax_pair_trade', methods=['POST'])
def ajax_pair_trade():
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
        sid1 = request.values['sid1']
        sid2 = request.values['sid2']
        print(sid1)
        print(sid2)
        # done_date = ''
        # fail_date = ''
        # print("time interval is %s to %s" % (begin, end))
        #
        # a = pd.date_range(start=begin, end=end)
        # # display only date using date() function
        # for i in a:
        #     print(i.date())
        #     rsp_twse = twse_index.process(i.date(), '0')
        #     # rsp_tpex = tpex_index.process(i.date(), '0')
        #     rsp_tpex = True
        #     if (rsp_twse & rsp_tpex):
        #         done_date += "%s \n" % i.date().strftime("%Y-%m-%d")
        #     else:
        #         fail_date += "%s \n" % i.date().strftime("%Y-%m-%d")
        #
        #     time.sleep(10)

    return {'done':sid1, 'fail':sid2}

# 使用sid取得stock name
@app.route('/ajax_stock_name', methods=['POST'])
def ajax_stock_name():
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
        sid = request.values['sid']
        query = "SELECT name from stock where sid = %s"

        # check latest data in DB
        data = SQL.Query_command(query, sid)
        name = ''
        if len(data) == 0:
            name = '無此股票'
        else:
            name = data[0][0]

    return {'name':name}

if __name__ == '__main__':
    if (len(sys.argv) > 1):
        # for debug test
        # datadate = datetime.date(2022, 1, 18)
        # twse.process(datadate, '0')

        if sys.argv[1] == 'latest':
            datadate = getNowTime()
            twse.process(datadate, '0')
            tpex.process(datadate, '0')
            twse_index.process(datadate, '0')
            tpex_index.process(datadate, '0')
    else:
        # app.debug = True
        app.run()

