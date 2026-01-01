import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import platform
from typing import Dict, Any, Union

# Set font for Chinese characters
system_name = platform.system()
if system_name == "Windows":
    plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows
elif system_name == "Darwin":
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # macOS
else:
    plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']  # Linux (fallback)

plt.rcParams['axes.unicode_minus'] = False

class StockVisualizer:
    def __init__(self):
        # ECharts classic palette
        self.echarts_colors = [
            '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', 
            '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'
        ]
        
        # Apply seaborn theme with custom palette
        sns.set_theme(style="whitegrid", palette=self.echarts_colors)
        
        # Re-apply Chinese font after seaborn theme reset
        if system_name == "Windows":
            plt.rcParams['font.sans-serif'] = ['SimHei']
        elif system_name == "Darwin":
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
        else:
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei']
        plt.rcParams['axes.unicode_minus'] = False

    def plot_valuation_history(self, data: Dict[str, pd.DataFrame], title=None, xlabel="Date", ylabel="Value"):
        """
        绘制多个系列的估值历史折线图 (Line chart for valuation history).
        
        Args:
            data (Dict[str, pd.DataFrame]): 
                包含数据的字典。
                - Key (str): 系列名称 (Legend Label).
                - Value (pd.DataFrame): 数据框，必须包含以下列：
                    - 'date': 日期 (datetime or string)
                    - 'value': 数值 (float)
            title (str, optional): 图表标题. Defaults to None.
            xlabel (str, optional): X轴标签. Defaults to "Date".
            ylabel (str, optional): Y轴标签. Defaults to "Value".
        """
        plt.figure(figsize=(12, 6))
        
        has_data = False
        # Create color iterator
        colors = self.echarts_colors * (len(data) // len(self.echarts_colors) + 1)
        
        for i, (label, df) in enumerate(data.items()):
            try:
                if df.empty:
                    continue
                
                # Ensure date format
                df = df.copy()
                if not pd.api.types.is_datetime64_any_dtype(df['date']):
                    df['date'] = pd.to_datetime(df['date'])
                
                df = df.sort_values('date')
                
                # Explicitly pass color to lineplot
                sns.lineplot(data=df, x='date', y='value', label=label, linewidth=2, color=colors[i])
                has_data = True
            except Exception as e:
                print(f"Error plotting {label}: {e}")

        if has_data:
            plt.title(title or "Valuation History", fontsize=16, pad=20)
            plt.xlabel(xlabel, fontsize=12)
            plt.ylabel(ylabel, fontsize=12)
            plt.legend(fontsize=10)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
        else:
            print("No data to plot for valuation.")

    def plot_financial_bar(self, data: Dict[str, pd.DataFrame], title=None, xlabel="Report Date", ylabel="Value"):
        """
        绘制多个系列的财务指标柱状图 (Bar chart for financial metrics).
        
        Args:
            data (Dict[str, pd.DataFrame]):
                包含数据的字典。
                - Key (str): 系列名称 (Legend Label).
                - Value (pd.DataFrame): 数据框，必须包含以下列：
                    - 'date': 日期 (datetime or string)
                    - 'value': 数值 (float)
            title (str, optional): 图表标题. Defaults to None.
            xlabel (str, optional): X轴标签. Defaults to "Report Date".
            ylabel (str, optional): Y轴标签. Defaults to "Value".
        """
        # Combine data for seaborn
        combined_data = []
        for label, df in data.items():
            if df.empty:
                continue
            df = df.copy()
            # Ensure date is datetime
            if not pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = pd.to_datetime(df['date'])
            
            # Format date as string for categorical plotting if needed, 
            # but keeping as datetime is usually better for sorting. 
            # For bar charts, we often want specific quarters.
            df['Series'] = label
            combined_data.append(df[['date', 'value', 'Series']])
            
        if not combined_data:
            print("No data to plot")
            return

        full_df = pd.concat(combined_data)
        full_df = full_df.sort_values('date')
        
        # Convert date to string for cleaner x-axis labels in bar chart
        full_df['DateStr'] = full_df['date'].dt.strftime('%Y-%m-%d')
        
        plt.figure(figsize=(12, 6))
        
        # Use palette explicitly
        sns.barplot(data=full_df, x='DateStr', y='value', hue='Series', palette=self.echarts_colors)
        
        plt.title(title or "Financial Comparison", fontsize=16, pad=20)
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.xticks(rotation=45)
        plt.legend(title=None)
        plt.tight_layout()
        plt.show()

    def plot_pie_chart(self, data: Dict[str, float], title="Composition"):
        """
        绘制饼状图 (Pie chart).
        
        Args:
            data (Dict[str, float]):
                包含数据的字典。
                - Key (str): 扇区标签 (Label).
                - Value (float): 数值/大小 (Size).
            title (str, optional): 图表标题. Defaults to "Composition".
        """
        labels = list(data.keys())
        sizes = list(data.values())
        
        plt.figure(figsize=(8, 8))
        
        # Use echarts color palette
        # Pie chart in matplotlib needs explicit colors
        colors = self.echarts_colors[0:len(labels)]
        
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140, 
                textprops={'fontsize': 12})
        
        plt.title(title, fontsize=16, pad=20)
        plt.axis('equal')
        plt.show()

    def plot_stock_trend(self, data: pd.DataFrame, title=None, symbol="Stock"):
        """
        绘制股票走势图 (Line chart for Stock Trend).
        
        Args:
            data (pd.DataFrame):
                包含股票历史数据的 DataFrame。必须包含以下列：
                - 'date' 或 '日期': 日期 (datetime or string)
                - 'close' 或 '收盘': 收盘价 (float)
            title (str, optional): 图表标题. Defaults to None.
            symbol (str, optional): 股票代码或名称 (用于默认标题). Defaults to "Stock".
        """
        try:
            df = data # Rename for clarity internally
            if df.empty:
                print(f"No history data for {symbol}")
                return
            
            df = df.copy()
            if '日期' in df.columns and 'date' not in df.columns:
                df['date'] = pd.to_datetime(df['日期'])
            elif 'date' not in df.columns:
                print("DataFrame must contain '日期' or 'date' column")
                return
            else:
                df['date'] = pd.to_datetime(df['date'])

            if '收盘' in df.columns and 'close' not in df.columns:
                df['close'] = df['收盘']
            elif 'close' not in df.columns:
                 print("DataFrame must contain '收盘' or 'close' column")
                 return
                
            plt.figure(figsize=(12, 6))
            
            # Use first color for Close price
            sns.lineplot(data=df, x='date', y='close', label='Close', linewidth=2, color=self.echarts_colors[0])
            
            # Optional: Add MA
            if len(df) > 20:
                df['MA20'] = df['close'].rolling(window=20).mean()
                # Use second color for MA
                sns.lineplot(data=df, x='date', y='MA20', label='MA20', alpha=0.7, linewidth=1.5, linestyle='--', color=self.echarts_colors[1])
            
            plt.title(title or f"{symbol} Stock Trend", fontsize=16, pad=20)
            plt.xlabel("Date", fontsize=12)
            plt.ylabel("Price", fontsize=12)
            plt.legend()
            plt.grid(True)
            plt.show()
            
        except Exception as e:
            print(f"Error plotting trend for {symbol}: {e}")
