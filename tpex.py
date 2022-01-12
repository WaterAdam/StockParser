import csv
import os.path
import requests
import urllib.request
import pandas
import SQL
from bs4 import BeautifulSoup

FIdata = "https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php?l=zh-tw&o=htm&se=EW&t=D&d=%s&s=0,asc"
DTdata = "https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&o=htm&d=%s&se=EW&s=0,asc,0"

# 查詢資本額
capital_query = "SELECT sid, Capital FROM stock where sid = %s limit 1"
# 確認stock_daily_info已存在最新data
check_data_exist = "SELECT sid, date FROM stock_daily_info where sid = %s and date = %s limit 1"
# 新增資料SQL語法
insert = "INSERT INTO stock_daily_info(sid, Open, Close, Volume, ChangePrice, ChangePercent, High, Low, AvgPrice, PreviousPrice, ForeignInvVol, InvVol, ForeignTradePercent, InvTradePercent, AvgVol5, AvgVol20, date, per) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
# 更新資料SQL語法
update = "UPDATE stock_daily_info set Open = %s, Close = %s, Volume = %s, ChangePrice = %s, ChangePercent = %s, High = %s, Low = %s, AvgPrice = %s, PreviousPrice = %s, ForeignInvVol = %s, InvVol = %s, ForeignTradePercent = %s, InvTradePercent = %s, AvgVol5 = %s, AvgVol20 = %s, per = %s where date = %s and sid = %s"

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

def getTableRow(table, head, end = None):
    trs = table.find_all('tr')[head:end]
    rows = list()
    for tr in trs:
        rows.append([td.text.replace('\n', '').replace('\xa0', '') for td in tr.find_all('td')])

    return rows

def tpexParser(_url):
    print(_url)
    rsp = requests.get(_url)
    rsp.encoding = 'UTF-8'
    soup = BeautifulSoup(rsp.text, "lxml")  # 指定 lxml 作為解析器
    table1 = soup.find('table')
    table1rows = getTableRow(table1, 3, -1)
    df = pandas.DataFrame.from_dict(table1rows)

    return df

def ROCdate(datadate):
    y, m, d = datadate.strftime("%Y-%m-%d").split('-')
    return str(int(y) - 1911) + '/' + m + '/' + d

def process(datadate, checkdata):
    print('TPEX process date is %s' % datadate)
    csvList = []

    ROCtime = ROCdate(datadate)
    print(ROCtime)
    try:
        # get daily FI trading data
        FIlist = tpexParser(FIdata % ROCtime)
        FIlist.columns = ['sid', 'name_fi', 'f2', 'f3', 'FVol', 'f5', 'f6', 'f7', 'f8', 'f9', 'F10', 'f11', 'f12', 'InvVol', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f20', 'f21', 'f22', 'f23']
        # print(FIlist)

        # get daily trading data
        DTlist = tpexParser(DTdata % ROCtime)
        DTlist.columns = ['sid', 'name', 'close', 'change', 'open', 'high', 'low', 'volume', 'money', 'total', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7']
        # print(DTlist)
    except Exception as ex:
        print(ex)
        print('get data fail')
        return False

    # inner join DTlist & FIlist by sid
    result = pandas.merge(DTlist, FIlist, on=['sid'], how='right')
    print(len(result))

    if checkdata == '1':
        File_Name = 'tpex' + datadate.strftime("%Y-%m-%d") + '.csv'
        result.to_csv(File_Name)
        return File_Name

    for index, row in result.iterrows():
        try:
            # filter some stocks
            if len(row['sid']) != 4:
                print(row['sid'])
                continue

            # pre calculate
            sid = int(row['sid'])
            volume = int(int(row['volume'].replace(',', '')) / 1000)
            close = float(row['close'].replace(',', ''))
            change = float(row['change'])
            changeP = round(change / (close - change) * 100, 2)
            FVol = int(int(row['FVol'].replace(',', '')) / 1000)
            InvVol = int(int(row['InvVol'].replace(',', '')) / 1000)
            avgPrice = int(row['money'].replace(',', '')) / volume / 1000

            # 計算方式：買超張數 / 股本（億） / 10000 * 100% = xx( %)
            capital = SQL.Query_command(capital_query, row['sid'])
            Fpercent = FVol / capital[0][1] / 100
            Ipercent = InvVol / capital[0][1] / 100

            # get average infomation
            query_latest20 = "SELECT Volume FROM stock_daily_info where sid = %s and date <= %s order by date desc limit 20"
            latest20 = SQL.Query_command(query_latest20, (row['sid'], datadate))
            latest19 = latest20[0:19]
            latest4 = latest20[0:4]
            avg20 = avg_volume(latest19, volume)
            avg5 = avg_volume(latest4, volume)

            data = [
                sid,
                row['open'].replace(',', ''),   # open
                row['close'].replace(',', ''),  # close
                volume,                         # Volume
                row['change'],                  # change
                changeP,                        # change %
                row['high'].replace(',', ''),   # high
                row['low'].replace(',', ''),    # low
                avgPrice,                       # avg price
                round(close - change, 2),       # pre price
                FVol,                           # F Volume
                InvVol,                         # I Volume
                Fpercent,                       # 外資成交佔比
                Ipercent,                       # 投信成交占比
                avg5,                           # avg volume 5
                avg20,                          # avg volume 20
                datadate.strftime("%Y-%m-%d"),
                0
            ]

            # check latest data in DB
            exist_data = SQL.Query_command(check_data_exist, (sid, datadate))

            # if no stock data in db
            if len(exist_data) == 0:
                # insert stock_daily_info
                rsp = SQL.Insert_stock_daily_info(insert, data)
                if rsp > 0:
                    csvList.append([sid])
                else:
                    print(str(sid) + ' OK')
            else:
                # update stock_daily_info
                if (exist_data[0][1] == datadate):
                    latest19 = latest20[1:20]
                    latest4 = latest20[1:5]
                    avg20 = avg_volume(latest19, volume)
                    avg5 = avg_volume(latest4, volume)

                    data = [
                        row['open'].replace(',', ''),  # open
                        row['close'].replace(',', ''),  # close
                        volume,  # Volume
                        row['change'],  # change
                        changeP,  # change %
                        row['high'].replace(',', ''),  # high
                        row['low'].replace(',', ''),  # low
                        avgPrice,  # avg price
                        round(close - change, 2),  # pre price
                        FVol,  # F Volume
                        InvVol,  # I Volume
                        Fpercent,  # 外資成交佔比
                        Ipercent,  # 投信成交占比
                        avg5,  # avg volume 5
                        avg20,  # avg volume 20
                        0,
                        datadate.strftime("%Y-%m-%d"),
                        sid,
                    ]

                    data_update = tuple(data)
                    rsp = SQL.Update_stock_daily_info(update, data_update)
                    if rsp > 0:
                        csvList.append([sid])
                    else:
                        print('update ' + str(sid) + ' OK')
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
    makeCSV(os.path.join(os.getcwd(), "loss/tpex") + datadate.strftime("%Y%m%d") + ".csv", csvList)
    return os.path.join(os.getcwd(), "loss/tpex") + datadate.strftime("%Y%m%d") + ".csv", csvList

def avg_volume(list, vol):
    cnt = vol
    size = len(list) + 1

    for rows in list:
        cnt += rows[0]
    return cnt / size