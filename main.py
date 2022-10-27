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
import json
import numpy as np

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
        # 每日排名
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

        stock_rank = df.to_html()

    return {'data':stock_rank, 'date':datadate.strftime("%Y-%m-%d")}

# show 60日加權&櫃買指數資訊，含法人進出
@app.route('/raw_index_data', methods=['POST'])
def raw_index_data():
    datadate = getNowTime();
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
        # 每日大盤
        df = pd.DataFrame(
            columns=['指數', '收盤', '漲跌幅', '交易量', '外資買賣超', '投信買賣超', '5日均量', '20日均量', '日期'])
        query_index = "select * from (SELECT id, Close, ChangePercent, Volume, ForeignInvVol, InvVol, AvgVol5, AvgVol20, date from index_daily_info as i " \
                      "order by date desc limit 120) as t order by t.id desc, t.date desc"
        # check latest data in DB
        data = SQL.Query_command(query_index)
        tmp = pd.DataFrame(data,
                           columns=['指數', '收盤', '漲跌幅', '交易量', '外資買賣超', '投信買賣超', '5日均量', '20日均量', '日期'])
        df = df.append(tmp)
        df['漲跌幅'] = df['漲跌幅'].astype(str) + '%'
        df['交易量'] = df['交易量'].astype(int) / 100
        df['交易量'] = df['交易量'].astype(str) + '億'
        df['外資買賣超'] = df['外資買賣超'].astype(int) / 100
        df['外資買賣超'] = df['外資買賣超'].astype(str) + '億'
        df['投信買賣超'] = df['投信買賣超'].astype(int) / 100
        df['投信買賣超'] = df['投信買賣超'].astype(str) + '億'
        df['5日均量'] = df['5日均量'].astype(int) / 100
        df['5日均量'] = df['5日均量'].astype(str) + '億'
        df['20日均量'] = df['20日均量'].astype(int) / 100
        df['20日均量'] = df['20日均量'].astype(str) + '億'

        data = df.to_html()
    return {'data':data, 'date':datadate.strftime("%Y-%m-%d")}

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

        df = pd.DataFrame(
            columns=['date', 'closeA', 'volA', 'twse', 'tpex', 'closeB', 'volB'])

        query_index = "select a.date, aclose, avolume, a.twse, a.tpex, bclose, bvolume from " \
                      "(select si.date, si.close as aclose, si.Volume as avolume, ind.close as twse, ind2.close as tpex from " \
                      "stock as st " \
                      "inner join stock_daily_info as si on si.sid = st.sid " \
                      "inner join index_daily_info as ind on ind.date = si.date and ind.id = 'twse' " \
                      "inner join index_daily_info as ind2 on ind2.date = si.date and ind2.id = 'tpex' " \
                      "where si.sid = %s ORDER by si.date desc limit 120) as a " \
                      "inner join (select si.date, si.close as bclose, si.Volume as bvolume, ind.close as twse, ind2.close as tpex from " \
                      "stock as st " \
                      "inner join stock_daily_info as si on si.sid = st.sid " \
                      "inner join index_daily_info as ind on ind.date = si.date and ind.id = 'twse' " \
                      "inner join index_daily_info as ind2 on ind2.date = si.date and ind2.id = 'tpex' " \
                      "where si.sid = %s ORDER by si.date desc limit 120) as b " \
                      "on b.date = a.date order by a.date desc"
        # check latest data in DB
        data = SQL.Query_command(query_index, [sid1, sid2])
        tmp = pd.DataFrame(data,
                           columns=['date', 'closeA', 'volA', 'twse', 'tpex', 'closeB', 'volB'])
        df = df.append(tmp)
        df['diff'] = df['closeA'] - df['closeB']
        df['twseA'] = ''
        df['twseB'] = ''

        df = df[['date', 'twse', 'tpex', 'closeA', 'volA', 'twseA', 'closeB', 'volB', 'twseB', 'diff']]
        arr = df.values.tolist()

        column = df["diff"]
        max_value = column.max()
        min_value = column.min()
        avg_value = df["diff"].mean()

    return {'data': arr, 'avg' : avg_value, 'max' : max_value, 'min': min_value}

# 計算correl係數
@app.route('/ajax_get_correl', methods=['POST'])
def ajax_get_correl():
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
        json_object = request.json

        df = pd.DataFrame(json_object)
        # df = df[['date', 'twse', 'tpex', 'closeA', 'volA', 'twseA', 'closeB', 'volB', 'twseB', 'diff']]
        df['1'] = pd.to_numeric(df['1'])
        df['2'] = pd.to_numeric(df['2'])
        df['3'] = pd.to_numeric(df['3'])
        df['4'] = pd.to_numeric(df['4'])
        df['5'] = pd.to_numeric(df['5'])
        df['6'] = pd.to_numeric(df['6'])
        df['7'] = pd.to_numeric(df['7'])
        df['8'] = pd.to_numeric(df['8'])
        df['9'] = pd.to_numeric(df['9'])
        twse = df['1'].to_numpy()
        tpex = df['2'].to_numpy()
        closeA = df['3'].tolist()
        volA = df['4'].tolist()
        twseA = df['5'].tolist()
        closeB = df['6'].tolist()
        volB = df['7'].tolist()
        twseB = df['8'].tolist()
        diff = df['9'].tolist()
        c_closeA_twseA = np.corrcoef(closeA, twseA)[0][1]
        c_volA_twseA = np.corrcoef(volA, twseA)[0][1]
        c_closeB_twseB = np.corrcoef(closeB, twseB)[0][1]
        c_volB_twseB = np.corrcoef(volB, twseB)[0][1]
        c_twse_diff = np.corrcoef(twse, diff)[0][1]
        c_tpex_diff = np.corrcoef(tpex, diff)[0][1]
        c_closeA_closeB = np.corrcoef(closeA, closeB)[0][1]
        c_volA_closeB = np.corrcoef(volA, volB)[0][1]

    return {
        'c_closeA_twseA':c_closeA_twseA,
        'c_volA_twseA':c_volA_twseA,
        'c_closeB_twseB':c_closeB_twseB,
        'c_volB_twseB': c_volB_twseB,
        'c_twse_diff': c_twse_diff,
        'c_tpex_diff': c_tpex_diff,
        'c_closeA_closeB': c_closeA_closeB,
        'c_volA_closeB': c_volA_closeB,
    }

@app.route('/obos_rank', methods=['GET', 'POST'])
def obos_rank():
    return render_template('obos_rank.html')

# 配對交易
@app.route('/ajax_obos_rank', methods=['POST'])
def ajax_obos_rank():
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
        # get date list within 60 days
        # get date sql
        date_query = "select distinct date from stock_daily_info ORDER by date desc limit 60"
        # run command
        date_command = SQL.Query_command(date_query)
        # get simple sql data list
        arr_list = pd.DataFrame(date_command, columns=['date']).values.tolist()
        date1 = arr_list[0][0].strftime("%Y-%m-%d")
        date3 = arr_list[2][0].strftime("%Y-%m-%d")
        date5 = arr_list[4][0].strftime("%Y-%m-%d")
        date10 = arr_list[9][0].strftime("%Y-%m-%d")
        date20 = arr_list[19][0].strftime("%Y-%m-%d")
        date60 = arr_list[59][0].strftime("%Y-%m-%d")

        inv = request.values['inv'] # 1 for inv, 2 for finv
        column = request.values['order[0][column]']
        dir = request.values['order[0][dir]']

        order_col_index = column if column else 0
        order_col_dir = dir if dir else 'desc'
        order_col = ['stock.sid', 'stock.name', 'd1.invp', 'd1.avgprice', 'd3.invp', 'd3.avgprice', 'd5.invp',
                     'd5.avgprice', 'd10.invp', 'd10.avgprice', 'd20.invp', 'd20.avgprice', 'd60.invp',
                     'd60.avgprice', 'industry.name']

        # get obos data
        if inv == '1':
            query = "select stock.sid as sid, stock.name as stock_name, d1.invp as d1_invp, d1.avgprice as d1_avgprice, d3.invp as d3_invp, d3.avgprice as d3_avgprice, d5.invp as d3_invp, d5.avgprice as d3_avgprice, d10.invp as d3_invp, d10.avgprice as d3_avgprice, d20.invp as d3_invp, d20.avgprice as d3_avgprice, d60.invp as d3_invp, d60.avgprice as d3_avgprice, industry.name as industry_name " \
                    "from stock " \
                    "inner join industry on industry.id = stock.industry " \
                    "inner join (select sid, SUM(InvTradePercent) as invp, AVG(AvgPrice) as avgprice " \
                    "from stock_daily_info " \
                    "where date >= %s " \
                    "GROUP by sid) as d1 on d1.sid = stock.sid " \
                    "inner join (select sid, SUM(InvTradePercent) as invp, AVG(AvgPrice) as avgprice " \
                    "from stock_daily_info " \
                    "where date >= %s " \
                    "GROUP by sid) as d3 on d3.sid = stock.sid " \
                    "inner join (select sid, SUM(InvTradePercent) as invp, AVG(AvgPrice) as avgprice " \
                    "from stock_daily_info " \
                    "where date >= %s " \
                    "GROUP by sid) as d5 on d5.sid = stock.sid " \
                    "inner join (select sid, SUM(InvTradePercent) as invp, AVG(AvgPrice) as avgprice " \
                    "from stock_daily_info " \
                    "where date >= %s " \
                    "GROUP by sid) as d10 on d10.sid = stock.sid " \
                    "inner join (select sid, SUM(InvTradePercent) as invp, AVG(AvgPrice) as avgprice " \
                    "from stock_daily_info " \
                    "where date >= %s " \
                    "GROUP by sid) as d20 on d20.sid = stock.sid " \
                    "inner join (select sid, SUM(InvTradePercent) as invp, AVG(AvgPrice) as avgprice " \
                    "from stock_daily_info " \
                    "where date >= %s " \
                    "GROUP by sid) as d60 on d60.sid = stock.sid " \
                    "ORDER by " + order_col[int(order_col_index)] + " " + order_col_dir + " limit 20"
        else:
            query = "select stock.sid as sid, stock.name as stock_name, d1.invp as d1_invp, d1.avgprice as d1_avgprice, d3.invp as d3_invp, d3.avgprice as d3_avgprice, d5.invp as d3_invp, d5.avgprice as d3_avgprice, d10.invp as d3_invp, d10.avgprice as d3_avgprice, d20.invp as d3_invp, d20.avgprice as d3_avgprice, d60.invp as d3_invp, d60.avgprice as d3_avgprice, industry.name as industry_name " \
                    "from stock " \
                    "inner join industry on industry.id = stock.industry " \
                    "inner join (select sid, SUM(ForeignTradePercent) as invp, AVG(AvgPrice) as avgprice " \
                    "from stock_daily_info " \
                    "where date >= %s " \
                    "GROUP by sid) as d1 on d1.sid = stock.sid " \
                    "inner join (select sid, SUM(ForeignTradePercent) as invp, AVG(AvgPrice) as avgprice " \
                    "from stock_daily_info " \
                    "where date >= %s " \
                    "GROUP by sid) as d3 on d3.sid = stock.sid " \
                    "inner join (select sid, SUM(ForeignTradePercent) as invp, AVG(AvgPrice) as avgprice " \
                    "from stock_daily_info " \
                    "where date >= %s " \
                    "GROUP by sid) as d5 on d5.sid = stock.sid " \
                    "inner join (select sid, SUM(ForeignTradePercent) as invp, AVG(AvgPrice) as avgprice " \
                    "from stock_daily_info " \
                    "where date >= %s " \
                    "GROUP by sid) as d10 on d10.sid = stock.sid " \
                    "inner join (select sid, SUM(ForeignTradePercent) as invp, AVG(AvgPrice) as avgprice " \
                    "from stock_daily_info " \
                    "where date >= %s " \
                    "GROUP by sid) as d20 on d20.sid = stock.sid " \
                    "inner join (select sid, SUM(ForeignTradePercent) as invp, AVG(AvgPrice) as avgprice " \
                    "from stock_daily_info " \
                    "where date >= %s " \
                    "GROUP by sid) as d60 on d60.sid = stock.sid " \
                    "ORDER by " + order_col[int(order_col_index)] + " " + order_col_dir + " limit 20"
        # run command
        command = SQL.Query_command(query, [date1, date3, date5, date10, date20, date60])
        # get simple sql data list
        data = pd.DataFrame(command).values.tolist()
    return {'data': data}

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
        app.debug = True
        app.run()

