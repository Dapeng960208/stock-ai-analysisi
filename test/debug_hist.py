import akshare as ak
import pandas as pd
from datetime import datetime

try:
    df = ak.stock_zh_a_hist(symbol="000858", period="daily", start_date="20240101", end_date="20251231", adjust="qfq")
    print(df.columns)
    print(df.head())
except Exception as e:
    print(e)
