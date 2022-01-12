import time
import SQL
import twse
import tpex
import datetime
import pandas as pd
from flask import Flask, request, render_template

order_list = ["ForeignTradePercent", "InvTradePercent", "ForeignInvVol", "InvVol"]

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

@app.route('/insert', methods=['POST'])
def insert():
    datadate = getNowTime();
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
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

@app.route('/raw_data_rank', methods=['POST'])
def raw_data_rank():
    datadate = getNowTime();
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
        df = pd.DataFrame(columns=['股號', '股名', '外資買賣超', '投信買賣超', '外本比', '投本比', '收盤', '漲跌%', '成交量', '5日均量', '20日均量'])
        for order in order_list:
            query_rank = "SELECT i.sid, s.name, i.ForeignInvVol, InvVol, ForeignTradePercent, InvTradePercent, close, ChangePercent, Volume, AvgVol5, AvgVol20 from stock_daily_info as i " \
                      "inner join stock as s on s.sid = i.sid " \
                      "where date = %s " \
                      "order by " + order + " desc limit 20"
            # check latest data in DB
            data = SQL.Query_command(query_rank, datadate)
            tmp = pd.DataFrame(data, columns=['股號', '股名', '外資買賣超', '投信買賣超', '外本比', '投本比', '收盤', '漲跌%', '成交量', '5日均量', '20日均量'])
            df = df.append(tmp)

        html_file = df.to_html()
    return {'data':html_file, 'date':datadate.strftime("%Y-%m-%d")}

@app.route('/insert_interval', methods=['GET', 'POST'])
def insert_interval():
    return render_template('insert_interval.html')

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
            try:
                file_twse = twse.process(i.date(), '0')
                file2_tpex = tpex.process(i.date(), '0')
                done_date += "%s \n" % i.date().strftime("%Y-%m-%d")
            except Exception as ex:
                print(ex)
                print("fail date is " + i.date().strftime("%Y-%m-%d"))
                fail_date += "%s \n" % i.date().strftime("%Y-%m-%d")

    return {'done':done_date, 'fail':fail_date}

if __name__ == '__main__':
    # for debug test
    # datadate = getNowTime()
    # twse.process(datadate, '0')

    app.debug = True
    app.run()
