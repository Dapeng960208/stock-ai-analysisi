import sys
import os
import pandas as pd
import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_tools.stock_data_provider import StockDataProvider
from data_tools.stock_visualizer import StockVisualizer

def test_visualizer():
    provider = StockDataProvider()
    visualizer = StockVisualizer()
    
    # 1. Valuation History (PE)
    print("Fetching and Plotting PE History...")
    symbols = ["000858.sz", "600519.sh"]
    indicator = "市盈率(TTM)"
    start_date = "2023-01-01"
    end_date = str(datetime.date.today())
    
    valuation_data = {}
    for symbol in symbols:
        print(f"Fetching valuation for {symbol}...")
        df = provider.get_stock_valuation(symbol, indicator=indicator)
        
        # Filter date here (or let visualizer handle it if we passed raw data, 
        # but the visualizer expects prepared data now, though it does some sorting)
        # Let's filter here to simulate "data preparation" layer
        if not df.empty:
             df['date'] = pd.to_datetime(df['date'])
             df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
             valuation_data[f"{symbol} {indicator}"] = df

    visualizer.plot_valuation_history(
        data=valuation_data,
        title=f"{indicator} Comparison ({start_date} to {end_date})"
    )
    
    # 2. Financial Bar (Revenue)
    print("Fetching and Plotting Revenue Bar Chart...")
    metric = "营业总收入"
    report_type = "利润表"
    
    financial_data = {}
    for symbol in symbols:
        print(f"Fetching financial report for {symbol}...")
        df = provider.get_stock_financial_report(symbol, report_type=report_type)
        if not df.empty and metric in df.columns:
            # Standardize column names for visualizer
            # Visualizer expects 'date' and 'value'
            # Financial report usually has '报告日'
            if '报告日' in df.columns:
                df['date'] = pd.to_datetime(df['报告日'], format='%Y%m%d') # Adjust format if needed
                df['value'] = df[metric]
                
                # Filter date
                df = df[df['date'] >= pd.to_datetime(start_date)]
                
                financial_data[symbol] = df[['date', 'value']]

    visualizer.plot_financial_bar(
        data=financial_data,
        title=f"{metric} Comparison",
        ylabel=metric
    )
    
    # 3. Pie Chart
    print("Plotting Pie Chart...")
    data = {"Stock A": 40, "Stock B": 30, "Stock C": 30}
    visualizer.plot_pie_chart(data=data, title="Portfolio Allocation")
    
    # 4. Stock Trend
    print("Fetching and Plotting Stock Trend...")
    trend_symbol = "000858.sz"
    print(f"Fetching history for {trend_symbol}...")
    trend_df = provider.get_stock_history(
        trend_symbol, 
        start_date="2024-01-01", 
        end_date=end_date
    )
    
    visualizer.plot_stock_trend(
        data=trend_df,
        title=f"{trend_symbol} Stock Trend",
        symbol=trend_symbol
    )

if __name__ == "__main__":
    test_visualizer()
