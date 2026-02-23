import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from .record_parser import RecordParser, RecordType, TRADE_TYPE_MAP, REPO_CODES


class DataCleaner:
    """
    数据清洗器
    
    负责读取和清洗券商清算文件，支持 CSV 和 XLS 格式
    """
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.raw_data: Optional[pd.DataFrame] = None
        self.cleaned_data: Optional[pd.DataFrame] = None
        self.parser = RecordParser()
        self.file_structure: Optional[Dict[str, Any]] = None
    
    def load_data(self) -> pd.DataFrame:
        """
        加载数据文件，自动检测格式
        
        Returns:
            原始数据 DataFrame
        """
        path = Path(self.filepath)
        suffix = path.suffix.lower()
        
        if suffix in ['.xls', '.xlsx']:
            # 先检查是否是文本格式（如从券商系统导出的假 .xls 文件）
            if self._is_text_format():
                return self._load_text_excel()
            return self._load_excel()
        elif suffix == '.csv':
            return self._load_csv()
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")
    
    def _is_text_format(self) -> bool:
        """
        检查 .xls 文件是否是文本格式（而非真正的 Excel 二进制格式）
        """
        try:
            with open(self.filepath, 'rb') as f:
                header = f.read(20)
                # 真正的 Excel 文件以特定的二进制标记开头
                # 文本文件则以可打印字符开头
                try:
                    header.decode('gbk')
                    return True  # 如果能用 GBK 解码，说明是文本文件
                except:
                    return False
        except:
            return False
    
    def _load_text_excel(self) -> pd.DataFrame:
        """
        加载文本格式的 .xls 文件（实际是制表符分隔的文本）
        """
        try:
            # 尝试用制表符分隔读取
            df = pd.read_csv(self.filepath, encoding='gbk', sep='\t', header=0)
        except:
            # 如果失败，尝试自动检测分隔符
            df = pd.read_csv(self.filepath, encoding='gbk', sep=None, engine='python', header=0)
        
        df = self._standardize_columns(df)
        
        records = []
        for idx, row in df.iterrows():
            try:
                record = self.parser.parse_record(row)
                records.append(record)
            except Exception as e:
                print(f"Warning: Failed to parse row {idx}: {e}")
        
        self.raw_data = pd.DataFrame(records)
        return self.raw_data
    
    def _load_excel(self) -> pd.DataFrame:
        """
        加载 Excel 文件，动态检测表头位置
        """
        df_raw = pd.read_excel(self.filepath, header=None)
        
        self.file_structure = self.parser.detect_file_structure(df_raw)
        header_row = self.file_structure['header_row']
        
        df = pd.read_excel(self.filepath, header=header_row)
        
        df = self._standardize_columns(df)
        
        records = []
        for idx, row in df.iterrows():
            try:
                record = self.parser.parse_record(row)
                records.append(record)
            except Exception as e:
                print(f"Warning: Failed to parse row {idx}: {e}")
        
        self.raw_data = pd.DataFrame(records)
        return self.raw_data
    
    def _load_csv(self) -> pd.DataFrame:
        """
        加载 CSV 文件
        """
        df_raw = pd.read_csv(self.filepath, header=None, encoding='utf-8')
        
        self.file_structure = self.parser.detect_file_structure(df_raw)
        header_row = self.file_structure['header_row']
        
        df = pd.read_csv(self.filepath, header=header_row, encoding='utf-8')
        
        df = self._standardize_columns(df)
        
        records = []
        for idx, row in df.iterrows():
            try:
                record = self.parser.parse_record(row)
                records.append(record)
            except Exception as e:
                print(f"Warning: Failed to parse row {idx}: {e}")
        
        self.raw_data = pd.DataFrame(records)
        return self.raw_data
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化列名，处理可能的列名变化
        """
        column_mapping = self.parser.COLUMN_MAPPING
        
        rename_map = {}
        for col in df.columns:
            col_str = str(col).strip()
            if col_str in column_mapping:
                rename_map[col] = column_mapping[col_str]
        
        df = df.rename(columns=rename_map)
        
        for col in column_mapping.values():
            if col not in df.columns:
                df[col] = None
        
        return df
    
    def clean(self) -> pd.DataFrame:
        """
        清洗数据
        
        Returns:
            清洗后的 DataFrame
        """
        if self.raw_data is None:
            self.load_data()
        
        df = self.raw_data.copy()
        
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d', errors='coerce')
        
        df = df.dropna(subset=['date'])
        
        df['is_repo'] = df['security_code'].isin(REPO_CODES)
        
        df['total_fee'] = df['commission'] + df['stamp_tax'] + df['transfer_fee'] + df['clearing_fee']
        
        df = df.reset_index()
        # 不再去重，因为交割单中的每笔记录都是独立的交易
        # 即使是同一天、同股票、同类型的多笔交易，也应该保留
        # 如果确实有重复数据，应该由数据库的 UNIQUE 约束来处理
        df = df.set_index('index')
        df = df.sort_index()
        
        df = df.reset_index(drop=True)
        
        self.cleaned_data = df
        return df
    
    def filter_by_date(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        按日期范围筛选数据
        
        Args:
            start_date: 开始日期 (yyyymmdd)
            end_date: 结束日期
            
        Returns:
            筛选后的 DataFrame
        """
        if self.cleaned_data is None:
            self.clean()
        
        df = self.cleaned_data.copy()
        
        if start_date:
            start_dt = pd.to_datetime(start_date, format='%Y%m%d')
            df = df[df['date'] >= start_dt]
        
        if end_date:
            end_dt = pd.to_datetime(end_date, format='%Y%m%d')
            df = df[df['date'] <= end_dt]
        
        return df
    
    def filter_by_stock(self, stock_code: str) -> pd.DataFrame:
        """
        按股票代码筛选数据
        
        Args:
            stock_code: 股票代码（支持用户输入 2050 或 002050）
            
        Returns:
            筛选后的 DataFrame
        """
        if self.cleaned_data is None:
            self.clean()
        
        from ..utils.code_formatter import normalize_user_code
        normalized_code = normalize_user_code(stock_code)
        
        return self.cleaned_data[self.cleaned_data['security_code'] == normalized_code].copy()
    
    def filter_by_trade_type(self, trade_types: List[str]) -> pd.DataFrame:
        """
        按交易类型筛选数据
        
        Args:
            trade_types: 交易类型列表，如 ['buy', 'sell']
            
        Returns:
            筛选后的 DataFrame
        """
        if self.cleaned_data is None:
            self.clean()
        
        return self.cleaned_data[self.cleaned_data['trade_type'].isin(trade_types)].copy()
    
    def get_trade_records(self) -> pd.DataFrame:
        """获取股票买卖记录"""
        if self.cleaned_data is None:
            self.clean()
        return self.cleaned_data[self.cleaned_data['trade_type'].isin(['buy', 'sell'])].copy()
    
    def get_repo_records(self) -> pd.DataFrame:
        """获取国债逆回购记录"""
        if self.cleaned_data is None:
            self.clean()
        return self.cleaned_data[self.cleaned_data['trade_type'].isin(['repo_lend', 'repo_return'])].copy()
    
    def get_dividend_records(self) -> pd.DataFrame:
        """获取分红记录"""
        if self.cleaned_data is None:
            self.clean()
        return self.cleaned_data[self.cleaned_data['trade_type'].isin(['dividend', 'dividend_tax', 'stock_dividend'])].copy()
    
    def get_transfer_records(self) -> pd.DataFrame:
        """获取银行转账记录"""
        if self.cleaned_data is None:
            self.clean()
        return self.cleaned_data[self.cleaned_data['trade_type'].isin(['transfer_in', 'transfer_out'])].copy()
    
    def get_interest_records(self) -> pd.DataFrame:
        """获取利息归本记录"""
        if self.cleaned_data is None:
            self.clean()
        return self.cleaned_data[self.cleaned_data['trade_type'] == 'interest'].copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """获取数据摘要"""
        if self.cleaned_data is None:
            self.clean()
        
        df = self.cleaned_data
        
        return {
            'total_records': len(df),
            'date_range': (df['date'].min(), df['date'].max()),
            'trade_count': len(df[df['trade_type'].isin(['buy', 'sell'])]),
            'buy_count': len(df[df['trade_type'] == 'buy']),
            'sell_count': len(df[df['trade_type'] == 'sell']),
            'repo_count': len(df[df['trade_type'].isin(['repo_lend', 'repo_return'])]),
            'dividend_count': len(df[df['trade_type'].isin(['dividend', 'dividend_tax', 'stock_dividend'])]),
            'unique_securities': df[df['security_code'] != '']['security_code'].nunique(),
            'file_structure': self.file_structure,
        }
    
    def get_business_type_summary(self) -> pd.DataFrame:
        """获取业务类型统计"""
        if self.cleaned_data is None:
            self.clean()
        
        return self.cleaned_data.groupby('business_type').size().reset_index(name='count')
