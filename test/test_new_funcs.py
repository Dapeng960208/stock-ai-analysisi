import akshare as ak
import pandas as pd

def test_valuation():
    print("Testing stock_zh_valuation_baidu for 000858...")
    try:
        # stock_zh_valuation_baidu usually takes symbol like '000858'
        df = ak.stock_zh_valuation_baidu(symbol="000858", indicator="市盈率(TTM)", period="近1年")
        print(df.head())
        print(df.columns)
        
        df_pb = ak.stock_zh_valuation_baidu(symbol="000858", indicator="市净率", period="近1年")
        print(df_pb.head())
        print(df_pb.columns)

    except Exception as e:
        print(f"Error in valuation: {e}")

def test_financial():
    print("Testing stock_financial_report_sina for 000858...")
    try:
        # Sina requires prefix
        df = ak.stock_financial_report_sina(stock="sz000858", symbol="利润表")
        print(df.head())
        print(df.columns)
    except Exception as e:
        print(f"Error in financial (sina): {e}")

    print("Testing stock_profit_sheet_by_report_em for 000858...")
    try:
        # EastMoney usually takes pure code
        df = ak.stock_profit_sheet_by_report_em(symbol="000858")
        if df is not None:
             print(df.head())
             print(df.columns)
        else:
             print("Returned None")
    except Exception as e:
        print(f"Error in financial (em): {e}")

if __name__ == "__main__":
    test_valuation()
    test_financial()
