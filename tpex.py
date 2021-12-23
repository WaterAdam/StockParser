from datetime import date, datetime
import csv
import os.path
import requests
import urllib.request
import pandas
import SQL

FIdata = "https://www.twse.com.tw/fund/T86?response=json&date=%s&selectType=ALLBUT0999"
DTdata = "https://www.twse.com.tw/exchangeReport/STOCK_DAY_ALL?response=open_data"

# 確認stock_daily_info已存在最新data
check_data_exist = "SELECT sid, date FROM stock_daily_info where sid = %s order by lid desc limit 1"
# 新增資料SQL語法
insert = "INSERT INTO stock_daily_info(sid, Open, Close, Volume, ChangePrice, ChangePercent, High, Low, AvgPrice, PreviousPrice, ForeignInvVol, InvVol, ForeignTradePercent, InvTradePercent, AvgVol5, AvgVol20, date) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

def makeCSV(path, csvList):
    # 開啟 CSV 檔案
    with open(path, 'w', newline='') as csvfile:
        # 建立 CSV 檔寫入器
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        # 寫入一列資料
        for line in csvList:
            writer.writerow([line])

def readCSV(path):
    lists = list(csv.reader(open(path)))

    return lists

def downloadCSV(_url, _path):
    print(_url)
    urllib.request.urlretrieve(_url, _path)

def twseFI(_url):
    print(_url)
    rsp = requests.get(_url)
    inv_json = rsp.json()
    df = pandas.DataFrame.from_dict(inv_json['data'])
    return df


def process(datadate):
    print('process date is %s' % datadate)
    csvList = []

    try:
        # get daily FI trading data
        FIlist = twseFI(FIdata % datadate.strftime("%Y%m%d"))
        FIlist.columns = ['sid', 'name_fi', 'f2', 'f3', 'FVol', 'f5', 'f6', 'f7', 'f8', 'f9', 'InvVol', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18']

        # get daily trading data
        path = os.path.join(os.getcwd(), "DTdata/") + date.today().strftime("%Y%m%d") + ".csv"
        downloadCSV(DTdata, path)
        DTlist = pandas.read_csv(path)
        DTlist.columns = ['sid', 'name', 'volume', 'money', 'open', 'high', 'low', 'close', 'change', 'total']
    except Exception as ex:
        print(ex)
        print('get data fail')
        return False

    # inner join DTlist & FIlist by sid
    result = pandas.merge(DTlist, FIlist, on=['sid'], how='right')
    # result.to_csv('tmp.csv')
    print(len(result))

    for index, row in result.iterrows():
        try:
            # filter some stocks
            if len(row['sid']) != 4:
                print(row['sid'])
                continue

            # pre calculate
            sid = int(row['sid'])
            volume = int(int(row['volume']) / 1000)
            changeP = round(row['change'] / (row['close'] - row['change']) * 100, 2)
            FVol = int(int(row['FVol'].replace(',', '')) / 1000)
            InvVol = int(int(row['InvVol'].replace(',', '')) / 1000)

            # 計算方式：買超張數 / 股本（億） / 10000 * 100% = xx( %)
            # Fpercent = FVol / RegCapital / 100
            # Ipercent = InvVol / RegCapital / 100

            # get average infomation
            query_latest19 = "SELECT Volume FROM stock_daily_info where sid = %s order by lid desc limit 19"
            latest19 = SQL.Query_command(query_latest19, row['sid'])
            latest4 = latest19[0:4]
            avg20 = avg_volume(latest19, volume)
            avg5 = avg_volume(latest4, volume)

            data = [
                sid,
                row['open'],                    # open
                row['close'],                   # close
                volume,                         # Volume
                row['change'],                  # change
                changeP,                        # change %
                row['high'],                    # high
                row['low'],                     # low
                row['money'] / row['volume'],   # avg price
                row['close'] - row['change'],   # pre price
                FVol,                           # F Volume
                InvVol,                         # I Volume
                0,                              # 外資成交佔比
                0,                              # 投信成交占比
                avg5,                           # avg volume 5
                avg20,                          # avg volume 20
                datadate.strftime("%Y-%m-%d")
            ]

            # check latest data in DB
            latest = SQL.Query_command(check_data_exist, sid)

            # trans string to datetime
            date_url = datetime.strptime(data[-1], "%Y-%m-%d").date()

            # if no stock data in db
            if len(latest) == 0:
                # insert stock_daily_info
                rsp = SQL.Insert_stock_daily_info(insert, data)
                if rsp > 0:
                    csvList.append([sid])
                else:
                    print(str(sid) + ' OK')
            else:
                # update stock_daily_info
                if (latest[0][1] == date_url):
                    print("to do update")
                else:
                    # insert stock_daily_info
                    rsp = SQL.Insert_stock_daily_info(insert, data)
                    if rsp > 0:
                        csvList.append([sid])
                    else:
                        print(str(sid) + ' OK')
        except Exception as ex:
            print(ex)
            csvList.append(row['sid'])

    print('fail collect stocks:')
    print(csvList)
    makeCSV(os.path.join(os.getcwd(), "loss/") + date.today().strftime("%Y%m%d") + ".csv", csvList)

def avg_volume(list, vol):
    cnt = vol
    size = len(list) + 1

    for rows in list:
        cnt += rows[0]
    return cnt / size