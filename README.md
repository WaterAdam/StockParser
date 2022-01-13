# StockParser

主要目標是透過收集下來的資料，每天可以搜尋自己想要的指標，EX:投本比、外資買賣超等。

資料由證交所&櫃買中心提供，將資料內容分析以後並放置在MySQL DB內，DB的設計請參考DB_build資料夾。

建置流程如下

step1:

建置DB, 執行DB_build/createDB內的三個create SQL

step2:

參考DB_build/insert_industry 寫入industry table

參考DB_build/stock_raw 寫入stock table, 且再執行DB_build/upadte_stock 補齊資本額資訊

step3:
執行程式, 預設會啟用flask建置的網站127.0.0.1:5000

如果要使用排程自動執行, 則在輸入參數帶入'today' 資訊

參考資料(有時間參數請自行調整)：

證交所法人買賣：https://www.twse.com.tw/fund/T86?response=json&date=20211223&selectType=ALLBUT0999

證交所每日收盤：https://www.twse.com.tw/exchangeReport/MI_INDEX?response=html&date=20220112&type=ALLBUT0999

櫃買中心法人買賣：https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php?l=zh-tw&o=htm&se=EW&t=D&d=110/12/22&s=0,asc

櫃買中心每日收盤：https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&o=htm&d=110/12/23&s=0,asc,0

資本額查詢：https://stock.wespai.com/p/28904