import akshare as ak
import pandas as pd

symbol = "601857"

print(f"Testing for symbol: {symbol}")

try:
    print("\n--- Testing stock_profit_forecast_ths (indicator='业绩预测详表-机构') ---")
    df = ak.stock_profit_forecast_ths(symbol=symbol, indicator="业绩预测详表-机构")
    print(df.head())
    print(df.columns)
except Exception as e:
    print(f"Error: {e}")

try:
    print("\n--- Testing stock_profit_forecast_ths (indicator='业绩预测详表-详细指标预测') ---")
    df = ak.stock_profit_forecast_ths(symbol=symbol, indicator="业绩预测详表-详细指标预测")
    print(df.head())
    print(df.columns)
except Exception as e:
    print(f"Error: {e}")

try:
    print("\n--- Testing stock_research_report_em ---")
    df = ak.stock_research_report_em(symbol=symbol)
    print(df.head())
    print(df.columns)
except Exception as e:
    print(f"Error: {e}")

try:
    print("\n--- Testing stock_institute_recommend_detail ---")
    df = ak.stock_institute_recommend_detail(symbol=f"sz{symbol}") # Sina usually needs prefix
    print(df.head())
    print(df.columns)
except Exception as e:
    print(f"Error: {e}")
