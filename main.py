import time
import sys
import twse
import tpex
import datetime
import pandas as pd
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

@app.route("/")
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    #  利用request取得使用者端傳來的方法為何
    if request.method == 'POST':
        mytime = time.localtime()
        if mytime.tm_hour > 13:
            datadate = datetime.date.today()
        else:
            datadate = datetime.date.today() - datetime.timedelta(days=1)

        #  利用request取得表單欄位值
        if (request.values['act'] == 'checkTWSE'):
            print('check twse')
            file = twse.process(datadate, '1')
        else:
            print('check tpex')
            file = tpex.process(datadate, '1')

        # to read csv file named "samplee"
        a = pd.read_csv(file)
        html_file = a.to_html()
    return {'data':html_file}

if __name__ == '__main__':
    # mytime = time.localtime()
    # if mytime.tm_hour > 13:
    #     datadate = datetime.date.today()
    # else :
    #     datadate = datetime.date.today() - datetime.timedelta(days=1)
    #
    # # 1 = only check data
    # # 0 = insert data in stock_daily_info
    # if (len(sys.argv) > 1):
    #     checkdata = sys.argv[1]
    #     # 證交所 - 上市
    #     twse.process(datadate, checkdata)
    #     # 櫃買中心 - 上櫃
    #     tpex.process(datadate, checkdata)
    # else:
    #     print('no input')

    app.debug = True
    app.run()
