import os
import json
import pandas as pd
import akshare as ak
from datetime import datetime

class StockDataProvider:
    def __init__(self, data_dir="data"):
        """
        初始化股票数据提供者
        :param data_dir: 数据保存的根目录，默认为 "data"
        """
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _parse_symbol(self, symbol_input):
        """
        解析股票代码
        :param symbol_input: 输入格式如 "000858.sz" 或 "600519.sh"
        :return: (pure_code, xq_code)
                 pure_code: 纯数字代码，如 "000858" (用于历史数据接口和文件夹命名)
                 xq_code: 雪球格式代码，如 "SZ000858" (用于雪球个股信息接口)
        """
        symbol_input = symbol_input.strip().lower()
        
        if '.' in symbol_input:
            code, exchange = symbol_input.split('.')
            pure_code = code
            xq_code = f"{exchange.upper()}{code}"
        else:
            # 兼容未带后缀的情况，尝试简单推断（不一定完全准确，建议带后缀）
            # 6开头为沪市(SH)，0/3开头为深市(SZ)，4/8为北交所(BJ)
            pure_code = symbol_input
            if symbol_input.startswith('6'):
                xq_code = f"SH{symbol_input}"
            elif symbol_input.startswith('0') or symbol_input.startswith('3'):
                xq_code = f"SZ{symbol_input}"
            elif symbol_input.startswith('4') or symbol_input.startswith('8'):
                xq_code = f"BJ{symbol_input}"
            else:
                # 默认尝试SZ，或者直接使用原代码
                xq_code = f"SZ{symbol_input}" 
                
        return pure_code, xq_code

    def _get_stock_dir(self, symbol):
        """
        获取个股数据存储目录
        :param symbol: 股票代码（纯数字）
        :return: 目录路径
        """
        stock_dir = os.path.join(self.data_dir, symbol)
        if not os.path.exists(stock_dir):
            os.makedirs(stock_dir)
        return stock_dir

    def get_stock_info(self, symbol, force_update=False):
        """
        获取个股信息（雪球源）
        :param symbol: 股票代码 (e.g., "000858.sz")
        """
        pure_code, xq_code = self._parse_symbol(symbol)
        stock_dir = self._get_stock_dir(pure_code)
        info_path = os.path.join(stock_dir, "info.json")

        # 优先加载缓存
        if not force_update and os.path.exists(info_path):
            try:
                with open(info_path, 'r', encoding='utf-8') as f:
                    print(f"Loading stock info from cache: {info_path}")
                    return json.load(f)
            except Exception as e:
                print(f"Error reading cache: {e}, fetching from api...")

        # 调用akshare接口
        print(f"Fetching stock info for {symbol} (XueQiu: {xq_code}) from Akshare...")
        try:
            # 尝试使用雪球接口
            if hasattr(ak, "stock_individual_basic_info_xq"):
                # 注意：有些版本的 akshare 雪球接口可能直接接受 SZ000858，也可能需要 code='000858', exchange='SZ'
                # 但大多数 xq 接口直接传 symbol='SZ000858'
                df = ak.stock_individual_basic_info_xq(symbol=xq_code)
            elif hasattr(ak, "stock_individual_info_xq"):
                df = ak.stock_individual_info_xq(symbol=xq_code)
            else:
                print("Warning: XueQiu specific interface not found, trying EastMoney fallback...")
                df = ak.stock_individual_info_em(symbol=pure_code)

            # 处理返回数据
            if isinstance(df, pd.DataFrame):
                if 'item' in df.columns and 'value' in df.columns:
                    data = dict(zip(df['item'], df['value']))
                else:
                    data_list = df.to_dict(orient="records")
                    if data_list:
                        data = data_list[0] 
                    else:
                        data = {}
            else:
                data = dict(df)

            # 保存缓存
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            return data

        except Exception as e:
            print(f"Error fetching stock info: {e}")
            raise

    def get_stock_history(self, symbol, start_date, end_date, adjust="qfq"):
        """
        获取股票历史行情数据
        :param symbol: 股票代码 (e.g., "000858.sz")
        """
        pure_code, _ = self._parse_symbol(symbol)
        stock_dir = self._get_stock_dir(pure_code)
        file_name = "history_data.csv"
        file_path = os.path.join(stock_dir, file_name)
        meta_path = os.path.join(stock_dir, "history_meta.json")

        # 统一日期格式
        try:
            req_start_dt = pd.to_datetime(start_date).date()
            req_end_dt = pd.to_datetime(end_date).date()
        except Exception as e:
            print(f"Date format error: {e}")
            raise

        cached_df = None
        cache_hit = False
        
        # 读取元数据以判断覆盖范围
        covered_start = None
        covered_end = None
        
        if os.path.exists(meta_path) and os.path.exists(file_path):
            try:
                # Check if file is empty
                if os.path.getsize(file_path) > 0:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        covered_start = pd.to_datetime(meta.get("covered_start")).date()
                        covered_end = pd.to_datetime(meta.get("covered_end")).date()
                else:
                    print(f"Warning: Cache file {file_path} is empty. Ignoring.")
            except Exception as e:
                print(f"Error reading meta file: {e}")

        if covered_start and covered_end:
            # 检查请求范围是否在覆盖范围内
            # 逻辑：覆盖开始 <= 请求开始 且 覆盖结束 >= 请求结束
            if covered_start <= req_start_dt and covered_end >= req_end_dt:
                try:
                    df = pd.read_csv(file_path, dtype={'股票代码': str})
                    if '日期' in df.columns:
                        df['日期'] = pd.to_datetime(df['日期']).dt.date
                        print(f"Cache hit for {symbol} history ({start_date}-{end_date})")
                        mask = (df['日期'] >= req_start_dt) & (df['日期'] <= req_end_dt)
                        return df.loc[mask].sort_values('日期').reset_index(drop=True)
                except Exception as e:
                    print(f"Error reading cache file: {e}")
            else:
                 print(f"Cache miss or partial: Covered({covered_start} to {covered_end}), Requested({req_start_dt} to {req_end_dt})")
        
        # 如果未命中或部分命中，加载现有数据以便合并
        if os.path.exists(file_path):
            try:
                # Check if file is empty
                if os.path.getsize(file_path) > 0:
                    cached_df = pd.read_csv(file_path, dtype={'股票代码': str})
                    if '日期' in cached_df.columns:
                        cached_df['日期'] = pd.to_datetime(cached_df['日期']).dt.date
                    else:
                         print(f"Warning: Cache file {file_path} missing '日期' column. Ignoring.")
                         cached_df = None
                else:
                    print(f"Warning: Cache file {file_path} is empty. Ignoring.")
                    cached_df = None
            except Exception as e:
                print(f"Warning: Failed to read cache file {file_path}: {e}. Ignoring.")
                cached_df = None

        # 调用API获取数据
        print(f"Fetching history for {symbol} (Code: {pure_code}) from Akshare ({start_date}-{end_date})...")
        try:
            # ak.stock_zh_a_hist 
            new_df = ak.stock_zh_a_hist(
                symbol=pure_code, 
                period="daily", 
                start_date=start_date.replace("-", ""), 
                end_date=end_date.replace("-", ""), 
                adjust=adjust
            )
            
            if '日期' not in new_df.columns:
                print(f"Warning: '日期' column missing in history data for {symbol}. Columns: {new_df.columns}")
            
            if '日期' in new_df.columns:
                 new_df['日期'] = pd.to_datetime(new_df['日期']).dt.date
            
            # 合并缓存
            if cached_df is not None:
                print("Merging with cache...")
                combined_df = pd.concat([cached_df, new_df])
                combined_df = combined_df.drop_duplicates(subset=['日期'], keep='last')
                combined_df = combined_df.sort_values('日期').reset_index(drop=True)
                final_df = combined_df
            else:
                final_df = new_df

            # 保存数据
            final_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            # 更新元数据
            # 新的覆盖范围应该是：min(旧覆盖开始, 请求开始) 到 max(旧覆盖结束, 请求结束)
            # 注意：如果之前没有覆盖范围，则使用请求范围
            
            new_covered_start = req_start_dt
            new_covered_end = req_end_dt
            
            if covered_start:
                new_covered_start = min(covered_start, req_start_dt)
            if covered_end:
                new_covered_end = max(covered_end, req_end_dt)
                
            meta = {
                "covered_start": str(new_covered_start),
                "covered_end": str(new_covered_end),
                "last_update": str(datetime.now())
            }
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=4)
            
            # 返回请求范围内的数据
            mask = (final_df['日期'] >= req_start_dt) & (final_df['日期'] <= req_end_dt)
            return final_df.loc[mask].reset_index(drop=True)

        except Exception as e:
            print(f"Error fetching history data: {e}")
            raise

    def get_stock_dividend_info(self, symbol, start_date=None, end_date=None, force_update=False):
        """
        获取股票分红送配详情
        :param symbol: 股票代码 (e.g., "000858.sz")
        :param start_date: 开始日期 "YYYYMMDD" (可选，基于除权除息日过滤)
        :param end_date: 结束日期 "YYYYMMDD" (可选)
        :param force_update: 是否强制更新
        :return: DataFrame
        """
        pure_code, _ = self._parse_symbol(symbol)
        stock_dir = self._get_stock_dir(pure_code)
        file_path = os.path.join(stock_dir, "dividend_info.csv")

        # 优先加载缓存
        if not force_update and os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, dtype={'股票代码': str})
                print(f"Loading dividend info from cache: {file_path}")
            except Exception as e:
                print(f"Error reading dividend cache: {e}, fetching from api...")
                df = None
        else:
            df = None

        if df is None:
            # 调用akshare接口
            print(f"Fetching dividend info for {symbol} (Code: {pure_code}) from Akshare...")
            try:
                # stock_fhps_detail_em: 东方财富-分红送配详情
                df = ak.stock_fhps_detail_em(symbol=pure_code)
                
                # 保存缓存
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            except Exception as e:
                print(f"Error fetching dividend info: {e}")
                raise

        # 数据过滤
        if start_date or end_date:
            try:
                # 确保 '除权除息日' 列存在且为日期格式
                # 注意：有些分红可能没有除权除息日（未实施），或者列名不同
                # 常见列名: '除权除息日', '股权登记日', '预案公告日'
                # 我们优先使用 '除权除息日'，如果为空则尝试使用 '预案公告日' 进行筛选?
                # 通常用户关心的是除权除息日
                
                date_col = '除权除息日'
                if date_col not in df.columns:
                    # 尝试寻找包含日期的列
                    potential_cols = [c for c in df.columns if '日期' in c or '日' in c]
                    print(f"Warning: '{date_col}' column not found. Available columns: {df.columns}")
                    if potential_cols:
                        # 暂时不强制筛选，或者提醒用户
                        pass
                
                if date_col in df.columns:
                    # 转换为日期类型，处理无效日期(如 '--')
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.date
                    
                    mask = pd.Series([True] * len(df))
                    if start_date:
                        s_dt = pd.to_datetime(start_date).date()
                        mask &= (df[date_col] >= s_dt)
                    if end_date:
                        e_dt = pd.to_datetime(end_date).date()
                        mask &= (df[date_col] <= e_dt)
                    
                    df = df.loc[mask]
                
            except Exception as e:
                print(f"Error filtering dividend info: {e}")

        return df.reset_index(drop=True)

    def get_stock_research_report(self, symbol, start_date=None, end_date=None, force_update=False):
        """
        获取股票研报及盈利预测信息 (东方财富)
        :param symbol: 股票代码 (e.g., "000858.sz")
        :param start_date: 开始日期 "YYYYMMDD" (可选)
        :param end_date: 结束日期 "YYYYMMDD" (可选)
        :param force_update: 是否强制更新
        :return: DataFrame
        """
        pure_code, _ = self._parse_symbol(symbol)
        stock_dir = self._get_stock_dir(pure_code)
        file_path = os.path.join(stock_dir, "research_report.csv")

        df = None
        # 优先加载缓存
        if not force_update and os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, dtype={'股票代码': str})
                print(f"Loading research report from cache: {file_path}")
            except Exception as e:
                print(f"Error reading research report cache: {e}, fetching from api...")
                df = None

        if df is None:
            # 调用akshare接口
            print(f"Fetching research report for {symbol} (Code: {pure_code}) from Akshare...")
            try:
                # stock_research_report_em: 东方财富-个股研报
                df = ak.stock_research_report_em(symbol=pure_code)
                
                # 保存缓存
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            except Exception as e:
                print(f"Error fetching research report: {e}")
                raise
        
        # 数据过滤
        if start_date or end_date:
            try:
                # 研报日期列通常是 '日期'
                date_col = '日期'
                if date_col not in df.columns:
                     print(f"Warning: '{date_col}' column not found. Available columns: {df.columns}")
                else:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce').dt.date
                    mask = pd.Series([True] * len(df))
                    
                    if start_date:
                        s_dt = pd.to_datetime(start_date).date()
                        mask &= (df[date_col] >= s_dt)
                    if end_date:
                        e_dt = pd.to_datetime(end_date).date()
                        mask &= (df[date_col] <= e_dt)
                    
                    df = df.loc[mask]
            except Exception as e:
                print(f"Error filtering research report: {e}")
        
        return df.reset_index(drop=True)

    def get_stock_institute_recommendations(self, symbol, force_update=False):
        """
        获取机构推荐/评级详情 (新浪财经)
        :param symbol: 股票代码 (e.g., "000858.sz")
        :param force_update: 是否强制更新
        :return: DataFrame
        """
        pure_code, xq_code = self._parse_symbol(symbol)
        stock_dir = self._get_stock_dir(pure_code)
        file_path = os.path.join(stock_dir, "institute_recommendations.csv")

        # 优先加载缓存
        if not force_update and os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, dtype={'股票代码': str})
                print(f"Loading institute recommendations from cache: {file_path}")
                return df
            except Exception as e:
                print(f"Error reading institute recommendations cache: {e}, fetching from api...")

        # 调用akshare接口
        # stock_institute_recommend_detail 需要带前缀的小写代码，如 sz000858
        sina_symbol = xq_code.lower()
        print(f"Fetching institute recommendations for {symbol} (Sina: {sina_symbol}) from Akshare...")
        
        try:
            df = ak.stock_institute_recommend_detail(symbol=sina_symbol)
            
            # 保存缓存
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            return df
        except Exception as e:
            print(f"Error fetching institute recommendations: {e}")
            # 如果是空DataFrame或其他错误，返回空DataFrame而不是抛出异常，以免中断流程
            # 但如果是连接错误等，可能还是需要知道
            if "Empty DataFrame" in str(e) or "No tables found" in str(e):
                 return pd.DataFrame()
            raise

    def get_stock_valuation(self, symbol, indicator="市盈率(TTM)", period="全部", force_update=False):
        """
        获取股票估值数据 (百度股市通)
        :param symbol: 股票代码 (e.g., "000858.sz")
        :param indicator: 指标名称，如 "市盈率(TTM)", "市净率", "市销率", "市现率"
        :param period: 时间段，如 "近1年", "近3年", "近5年", "全部"
        :param force_update: 是否强制更新
        :return: DataFrame (包含 date, value)
        """
        pure_code, _ = self._parse_symbol(symbol)
        stock_dir = self._get_stock_dir(pure_code)
        # Use a safe filename for indicator
        safe_indicator = indicator.replace("(", "").replace(")", "").replace(" ", "_")
        file_path = os.path.join(stock_dir, f"valuation_{safe_indicator}.csv")

        # 优先加载缓存
        if not force_update and os.path.exists(file_path):
             try:
                 df = pd.read_csv(file_path)
                 if 'date' in df.columns:
                     df['date'] = pd.to_datetime(df['date']).dt.date
                 print(f"Loading valuation ({indicator}) from cache: {file_path}")
                 return df
             except Exception as e:
                 print(f"Error reading valuation cache: {e}, fetching from api...")

        print(f"Fetching valuation ({indicator}) for {symbol} (Code: {pure_code}) from Akshare...")
        try:
            # 总是获取全部数据以缓存
            df = ak.stock_zh_valuation_baidu(symbol=pure_code, indicator=indicator, period="全部")
            if 'date' in df.columns:
                 df['date'] = pd.to_datetime(df['date']).dt.date
            
            # Save cache
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            return df
        except Exception as e:
            print(f"Error fetching valuation: {e}")
            raise

    def get_stock_financial_report(self, symbol, report_type="利润表", force_update=False):
        """
        获取股票财务报表 (新浪财经)
        :param symbol: 股票代码 (e.g., "000858.sz")
        :param report_type: 报表类型: "资产负债表", "利润表", "现金流量表"
        :param force_update: 是否强制更新
        :return: DataFrame
        """
        pure_code, xq_code = self._parse_symbol(symbol)
        stock_dir = self._get_stock_dir(pure_code)
        safe_type = report_type.replace(" ", "_")
        file_path = os.path.join(stock_dir, f"financial_{safe_type}.csv")
        
        # 优先加载缓存
        if not force_update and os.path.exists(file_path):
             try:
                 df = pd.read_csv(file_path)
                 print(f"Loading financial report ({report_type}) from cache: {file_path}")
                 return df
             except Exception as e:
                 print(f"Error reading financial report cache: {e}, fetching from api...")

        sina_symbol = xq_code.lower() # e.g. sz000858
        print(f"Fetching financial report ({report_type}) for {symbol} (Sina: {sina_symbol}) from Akshare...")
        try:
            df = ak.stock_financial_report_sina(stock=sina_symbol, symbol=report_type)
            
            # Save cache
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            return df
        except Exception as e:
            print(f"Error fetching financial report: {e}")
            raise

if __name__ == "__main__":
    pass