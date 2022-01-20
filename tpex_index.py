import pandas
import SQL

FIdata = "https://www.tpex.org.tw/web/stock/3insti/3insti_summary/3itrdsum_result.php?l=zh-tw&t=D&p=1&d=%s&o=htm"
DTdata = "https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_index/st41_result.php?l=zh-tw&d=%s&s=0,asc,0&o=htm"

# 確認index_daily_info已存在最新data
check_data_exist = "SELECT id, date FROM index_daily_info where id = %s and date = %s limit 1"
# 新增資料SQL語法
insert = "INSERT INTO index_daily_info(id, Close, Volume, ChangePrice, ChangePercent, ForeignInvVol, InvVol, AvgVol5, AvgVol20, date) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
# 更新資料SQL語法
update = "UPDATE index_daily_info set Close = %s, Volume = %s, ChangePrice = %s, ChangePercent = %s, ForeignInvVol = %s, InvVol = %s, AvgVol5 = %s, AvgVol20 = %s where date = %s and id = %s"

def tpexFI(_url, ROCtime):
    print(_url)
    table_MN = pandas.read_html(_url)
    df = table_MN[-1].iloc[1:4]
    df.columns = ['dep', 'buy', 'sell', 'diff']

    mydict = [{'date': ROCtime, 'ForeignInvVol': df.iloc[0, 3], 'InvVol': df.iloc[2, 3]}]
    data = pandas.DataFrame(mydict)

    return data

def tpexDT(_url, ROCtime):
    print(_url)
    table_MN = pandas.read_html(_url)
    df = table_MN[-1]
    df.columns = ['date', 'number1', 'volume', 'number2', 'close', 'change']

    return df.loc[df['date'] == ROCtime]

def ROCdate(datadate):
    y, m, d = datadate.strftime("%Y-%m-%d").split('-')
    return str(int(y) - 1911) + '/' + m + '/' + d

def process(datadate, checkdata):
    print('TPEX index process date is %s' % datadate)

    try:
        ROCtime = ROCdate(datadate)
        # # get daily FI trading data
        FIlist = tpexFI(FIdata % ROCtime, ROCtime)
        DTlist = tpexDT(DTdata % ROCtime, ROCtime)
    except Exception as ex:
        print('get data fail')
        return False

    # inner join DTlist & FIlist by date
    result = pandas.merge(DTlist, FIlist, on=['date'], how='right')

    if checkdata == '1':
        print(result)
        File_Name = 'tpex_index' + datadate.strftime("%Y-%m-%d") + '.csv'
        result.to_csv(File_Name)
        return File_Name

    for index, row in result.iterrows():
        try:
            # pre calculate
            close = float(row['close'])
            volume = int(int(row['volume']) / 1000)
            change = float(row['change'])
            changeP = round(change / (close - change) * 100, 2)

            FVol = int(row['ForeignInvVol'] / 1000000)
            InvVol = int(row['InvVol'] / 1000000)

            # get average infomation
            query_latest20 = "SELECT Volume FROM index_daily_info where id = %s and date <= %s order by date desc limit 20"
            latest20 = SQL.Query_command(query_latest20, ('tpex', datadate))
            latest19 = latest20[0:19]
            latest4 = latest20[0:4]
            avg20 = avg_volume(latest19, volume)
            avg5 = avg_volume(latest4, volume)

            data = [
                'tpex',                         # id
                close,                          # close
                volume,                         # Volume
                change,                         # change
                changeP,                        # change %
                FVol,                           # F Volume
                InvVol,                         # I Volume
                avg5,                           # avg volume 5
                avg20,                          # avg volume 20
                datadate.strftime("%Y-%m-%d")
            ]

            # check latest data in DB
            exist_data = SQL.Query_command(check_data_exist, ('tpex', datadate))
            # if no stock data in db
            if len(exist_data) == 0:
                # insert index_daily_info
                rsp = SQL.Insert_index_daily_info(insert, data)
            else:
                # update index_daily_info
                if (exist_data[0][1] == datadate):
                    latest19 = latest20[1:20]
                    latest4 = latest20[1:5]
                    avg20 = avg_volume(latest19, volume)
                    avg5 = avg_volume(latest4, volume)

                    data = [
                        close,  # close
                        volume,  # Volume
                        change,  # change
                        changeP,  # change %
                        FVol,  # F Volume
                        InvVol,  # I Volume
                        avg5,  # avg volume 5
                        avg20,  # avg volume 20
                        datadate.strftime("%Y-%m-%d"),
                        'tpex'  # id
                    ]

                    # data_update = tuple(data)
                    rsp = SQL.Update_index_daily_info(update, data)
                else:
                    # insert index_daily_info
                    rsp = SQL.Insert_index_daily_info(insert, data)

            if rsp == 0:
                print(datadate.strftime("%Y-%m-%d") + ' tpex is ok')
        except Exception as ex:
            print(ex)

    return True

def avg_volume(list, vol):
    cnt = vol
    size = len(list) + 1

    for rows in list:
        cnt += rows[0]
    return cnt / size