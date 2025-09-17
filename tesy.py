import  akshare as ak
stock_news_em_df = ak.stock_news_em("069351")
stock_news_em_df.to_csv("G:\\stock\\data\\news.csv",encoding="GBK")
