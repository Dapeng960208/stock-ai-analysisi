import sys
import os
import unittest
import pandas as pd

# 添加父目录到 sys.path 以便导入 data_tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_tools.stock_data_provider import StockDataProvider

class TestStockDataProvider(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider = StockDataProvider(data_dir="test_data")
        cls.symbol = "601857.sh"
        cls.pure_symbol = "601857"

    def test_01_parse_symbol(self):
        pure, xq = self.provider._parse_symbol("000858.sz")
        self.assertEqual(pure, "000858")
        self.assertEqual(xq, "SZ000858")
        
        pure, xq = self.provider._parse_symbol("600519.sh")
        self.assertEqual(pure, "600519")
        self.assertEqual(xq, "SH600519")

    def test_02_get_stock_info(self):
        print("\nTesting get_stock_info...")
        info = self.provider.get_stock_info(self.symbol)
        self.assertIsInstance(info, dict)
        self.assertTrue(len(info) > 0)
        print("Stock Info Sample:", list(info.keys())[:5])

    def test_03_get_stock_history(self):
        print("\nTesting get_stock_history...")
        start = "20230101"
        end = "20230131"
        df = self.provider.get_stock_history(self.symbol, start, end)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        self.assertTrue('日期' in df.columns)
        print(f"History rows: {len(df)}")

    def test_04_get_stock_dividend_info(self):
        print("\nTesting get_stock_dividend_info...")
        # 1. 获取所有数据
        df_all = self.provider.get_stock_dividend_info(self.symbol, force_update=True)
        self.assertIsInstance(df_all, pd.DataFrame)
        self.assertFalse(df_all.empty)
        print(f"Total dividend records: {len(df_all)}")
        if not df_all.empty:
            print("Columns:", df_all.columns.tolist())
            print("First row:", df_all.iloc[0].to_dict())

        # 2. 测试日期筛选
        # 假设五粮液在2020年到2023年有分红
        start_filter = "20200101"
        end_filter = "20231231"
        df_filter = self.provider.get_stock_dividend_info(self.symbol, start_date=start_filter, end_date=end_filter)
        print(f"Filtered dividend records ({start_filter}-{end_filter}): {len(df_filter)}")
        
        # 验证筛选结果
        if not df_filter.empty and '除权除息日' in df_filter.columns:
            dates = pd.to_datetime(df_filter['除权除息日']).dt.date
            s_dt = pd.to_datetime(start_filter).date()
            e_dt = pd.to_datetime(end_filter).date()
            self.assertTrue((dates >= s_dt).all())
            self.assertTrue((dates <= e_dt).all())

    def test_05_get_stock_research_report(self):
        print("\nTesting get_stock_research_report...")
        df = self.provider.get_stock_research_report(self.symbol, force_update=True)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print("Research Report Columns:", df.columns.tolist())
        print("First Report:", df.iloc[0].to_dict())
        
        # Check for expected columns
        expected_cols = ['股票代码', '报告名称', '机构']
        for col in expected_cols:
            self.assertTrue(col in df.columns, f"Column {col} missing in research report")

        # Test date filtering for research report
        # Assuming we have data, let's filter the last month or year
        if not df.empty and '日期' in df.columns:
            # Get min and max date from current df to pick a valid range
            dates = pd.to_datetime(df['日期']).dt.date
            min_date = dates.min()
            max_date = dates.max()
            
            # Create a range that should include some data (e.g., last 30 days of data range)
            # Or just use the max date as start date to get at least one record
            start_filter = max_date.strftime("%Y%m%d")
            # end_filter = max_date.strftime("%Y%m%d") # Optional
            
            print(f"Testing research report filter: start_date={start_filter}")
            df_filtered = self.provider.get_stock_research_report(self.symbol, start_date=start_filter)
            print(f"Filtered report records: {len(df_filtered)}")
            
            if not df_filtered.empty:
                filtered_dates = pd.to_datetime(df_filtered['日期']).dt.date
                self.assertTrue((filtered_dates >= max_date).all())


    def test_06_get_stock_institute_recommendations(self):
        print("\nTesting get_stock_institute_recommendations...")
        df = self.provider.get_stock_institute_recommendations(self.symbol, force_update=True)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        print("Institute Recommendations Columns:", df.columns.tolist())
        print("First Recommendation:", df.iloc[0].to_dict())
        
        # Check for expected columns based on terminal output
        # ['股票代码', '股票名称', '目标价', '最新评级', '评级机构', '分析师', '行业', '评级日期']
        expected_cols = ['股票代码', '目标价', '最新评级', '评级机构']
        for col in expected_cols:
            self.assertTrue(col in df.columns, f"Column {col} missing in institute recommendations")

if __name__ == '__main__':
    unittest.main()
