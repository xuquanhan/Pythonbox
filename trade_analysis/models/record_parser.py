import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field


@dataclass
class RecordType:
    TRADE: str = 'trade'
    TRANSFER: str = 'transfer'
    INTEREST: str = 'interest'
    DIVIDEND: str = 'dividend'
    DIVIDEND_TAX: str = 'dividend_tax'
    STOCK_DIVIDEND: str = 'stock_dividend'
    REPO: str = 'repo'
    DESIGNATE: str = 'designate'
    UNKNOWN: str = 'unknown'


TRADE_TYPE_MAP = {
    '证券买入': 'buy',
    '证券卖出': 'sell',
    '融券回购': 'repo_lend',
    '融券购回': 'repo_return',
    '银行转证券': 'transfer_in',
    '证券转银行': 'transfer_out',
    '利息归本': 'interest',
    '红利入账': 'dividend',
    '股息红利差异扣税': 'dividend_tax',
    '红股入账': 'stock_dividend',
    '指定交易': 'designate',
    '指定登记': 'designate',
}

REPO_CODES = ['131810', '204001', '204002', '204003', '204004', '204007', '204014', '204028', '204091']

TRANSFER_KEYWORDS = ['银行转证券', '证券转银行']
INTEREST_KEYWORDS = ['利息归本']


class RecordParser:
    """
    交易记录解析器
    
    支持解析以下类型的记录：
    - 证券买入/卖出
    - 融券回购/购回（国债逆回购）
    - 银行转账
    - 利息归本
    - 红利入账/红股入账
    - 股息红利差异扣税
    - 指定交易
    """
    
    COLUMN_MAPPING = {
        '交割日期': 'date',
        '证券代码': 'security_code',
        '证券名称': 'security_name',
        '业务类型': 'business_type',
        '成交价格': 'price',
        '成交数量': 'quantity',
        '成交金额': 'amount',
        '佣金': 'commission',
        '印花税': 'stamp_tax',
        '过户费': 'transfer_fee',
        '清算费（B股）': 'clearing_fee',
        '发生金额': 'net_amount',
        '剩余金额': 'balance',
        '证券数量': 'position',
        '股东代码': 'shareholder_code',
        '币种': 'currency',
        '成交编号': 'trade_id',
        '证券全称': 'security_full_name',
        '备注': 'remark',
    }
    
    def __init__(self):
        self.record_type = RecordType()
    
    def detect_file_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        动态检测文件结构
        
        Args:
            df: 原始DataFrame（无表头）
            
        Returns:
            包含表头行索引、列名等信息的字典
        """
        header_keywords = ['交割日期', '证券代码', '业务类型']
        
        for i in range(min(20, len(df))):
            row_vals = df.iloc[i].dropna().astype(str).tolist()
            if any(kw in row_vals for kw in header_keywords):
                return {
                    'header_row': i,
                    'columns': row_vals,
                    'total_rows': len(df),
                    'total_cols': len(df.columns)
                }
        
        raise ValueError("无法识别文件格式：未找到有效表头")
    
    def identify_record_type(self, row: pd.Series) -> str:
        """
        识别单条记录的类型
        
        Args:
            row: 数据行
            
        Returns:
            记录类型字符串
        """
        security_code = str(row.get('security_code', ''))
        business_type = str(row.get('business_type', ''))
        
        # 检查银行转账（通过 security_code 或 business_type）
        if security_code in ['银行转证券', '证券转银行']:
            return RecordType.TRANSFER
        
        if business_type in ['银行转证券', '证券转银行']:
            return RecordType.TRANSFER
        
        if security_code == '利息归本':
            return RecordType.INTEREST
        
        if business_type == '利息归本':
            return RecordType.INTEREST
        
        if business_type == '0' or business_type == '0.0':
            if security_code in ['银行转证券', '证券转银行']:
                return RecordType.TRANSFER
            return RecordType.UNKNOWN
        
        if business_type in ['证券买入', '证券卖出']:
            return RecordType.TRADE
        
        if business_type in ['融券回购', '融券购回']:
            return RecordType.REPO
        
        if business_type == '红利入账':
            return RecordType.DIVIDEND
        
        if business_type == '红股入账':
            return RecordType.STOCK_DIVIDEND
        
        if business_type == '股息红利差异扣税':
            return RecordType.DIVIDEND_TAX
        
        if business_type in ['指定交易', '指定登记']:
            return RecordType.DESIGNATE
        
        return RecordType.UNKNOWN
    
    def parse_record(self, row: pd.Series) -> Dict[str, Any]:
        """
        解析单条记录，返回标准化格式
        
        Args:
            row: 数据行（已映射列名）
            
        Returns:
            标准化的记录字典
        """
        record_type = self.identify_record_type(row)
        
        if record_type == RecordType.TRANSFER:
            return self._parse_transfer(row)
        elif record_type == RecordType.INTEREST:
            return self._parse_interest(row)
        elif record_type == RecordType.TRADE:
            return self._parse_trade(row)
        elif record_type == RecordType.REPO:
            return self._parse_repo(row)
        elif record_type == RecordType.DIVIDEND:
            return self._parse_dividend(row)
        elif record_type == RecordType.STOCK_DIVIDEND:
            return self._parse_stock_dividend(row)
        elif record_type == RecordType.DIVIDEND_TAX:
            return self._parse_dividend_tax(row)
        elif record_type == RecordType.DESIGNATE:
            return self._parse_designate(row)
        else:
            return self._parse_unknown(row)
    
    def _parse_transfer(self, row: pd.Series) -> Dict[str, Any]:
        transfer_type = str(row.get('security_code', ''))
        business_type = '银行转证券' if transfer_type == '银行转证券' else '证券转银行'
        
        net_amount, balance, currency = self._detect_misaligned_fields(row)
        
        return {
            'date': str(row.get('date', '')),
            'security_code': '',
            'security_name': '',
            'business_type': business_type,
            'trade_type': TRADE_TYPE_MAP.get(business_type, 'unknown'),
            'price': 0.0,
            'quantity': 0,
            'amount': 0.0,
            'commission': 0.0,
            'stamp_tax': 0.0,
            'transfer_fee': 0.0,
            'clearing_fee': 0.0,
            'net_amount': net_amount,
            'balance': balance,
            'position': 0,
            'shareholder_code': '',
            'currency': currency,
            'trade_id': '',
            'security_full_name': '',
            'remark': '',
            'record_type': RecordType.TRANSFER,
        }
    
    def _parse_interest(self, row: pd.Series) -> Dict[str, Any]:
        net_amount, balance, currency = self._detect_misaligned_fields(row)
        
        return {
            'date': str(row.get('date', '')),
            'security_code': '',
            'security_name': '',
            'business_type': '利息归本',
            'trade_type': 'interest',
            'price': 0.0,
            'quantity': 0,
            'amount': 0.0,
            'commission': 0.0,
            'stamp_tax': 0.0,
            'transfer_fee': 0.0,
            'clearing_fee': 0.0,
            'net_amount': net_amount,
            'balance': balance,
            'position': 0,
            'shareholder_code': '',
            'currency': currency,
            'trade_id': '',
            'security_full_name': '',
            'remark': str(row.get('balance', '')),
            'record_type': RecordType.INTEREST,
        }
    
    def _detect_misaligned_fields(self, row: pd.Series) -> Tuple[float, float, str]:
        """
        自动检测错位字段，返回 (发生金额, 剩余金额, 币种)
        
        银行转账/利息归本记录可能存在字段错位：
        - 正常情况: 发生金额在 net_amount 字段
        - 错位情况: 发生金额在 stamp_tax 字段，币种在 net_amount 字段
        """
        net_amount = 0.0
        balance = 0.0
        currency = '人民币'
        
        for col in ['net_amount', 'stamp_tax', 'transfer_fee', 'clearing_fee']:
            val = row.get(col)
            if val is not None:
                val_str = str(val).strip()
                if val_str in ['人民币', 'RMB', 'CNY']:
                    currency = val_str
                elif self._is_numeric(val):
                    num_val = self._safe_float(val)
                    if col == 'net_amount' and num_val != 0:
                        pass
                    elif col == 'stamp_tax' and abs(num_val) >= 1:
                        net_amount = num_val
                    elif col == 'transfer_fee' and abs(num_val) >= 1:
                        balance = num_val
        
        if net_amount == 0:
            net_amount = self._safe_float(row.get('net_amount', 0))
        if balance == 0:
            balance = self._safe_float(row.get('balance', 0))
        
        return net_amount, balance, currency
    
    def _is_numeric(self, value) -> bool:
        if value is None:
            return False
        try:
            float(str(value).replace(',', '').strip())
            return True
        except (ValueError, TypeError):
            return False
    
    def _parse_trade(self, row: pd.Series) -> Dict[str, Any]:
        business_type = str(row.get('business_type', ''))
        return {
            'date': str(row.get('date', '')),
            'security_code': self._format_code(row.get('security_code', '')),
            'security_name': str(row.get('security_name', '')),
            'business_type': business_type,
            'trade_type': TRADE_TYPE_MAP.get(business_type, 'unknown'),
            'price': self._safe_float(row.get('price', 0)),
            'quantity': self._safe_int(row.get('quantity', 0)),
            'amount': self._safe_float(row.get('amount', 0)),
            'commission': self._safe_float(row.get('commission', 0)),
            'stamp_tax': self._safe_float(row.get('stamp_tax', 0)),
            'transfer_fee': self._safe_float(row.get('transfer_fee', 0)),
            'clearing_fee': self._safe_float(row.get('clearing_fee', 0)),
            'net_amount': self._safe_float(row.get('net_amount', 0)),
            'balance': self._safe_float(row.get('balance', 0)),
            'position': self._safe_int(row.get('position', 0)),
            'shareholder_code': str(row.get('shareholder_code', '')),
            'currency': str(row.get('currency', '人民币')),
            'trade_id': str(row.get('trade_id', '')),
            'security_full_name': str(row.get('security_full_name', '')),
            'remark': str(row.get('remark', '')),
            'record_type': RecordType.TRADE,
        }
    
    def _parse_repo(self, row: pd.Series) -> Dict[str, Any]:
        business_type = str(row.get('business_type', ''))
        return {
            'date': str(row.get('date', '')),
            'security_code': self._format_code(row.get('security_code', '')),
            'security_name': str(row.get('security_name', '')),
            'business_type': business_type,
            'trade_type': TRADE_TYPE_MAP.get(business_type, 'repo'),
            'price': self._safe_float(row.get('price', 0)),
            'quantity': self._safe_int(row.get('quantity', 0)),
            'amount': self._safe_float(row.get('amount', 0)),
            'commission': self._safe_float(row.get('commission', 0)),
            'stamp_tax': self._safe_float(row.get('stamp_tax', 0)),
            'transfer_fee': self._safe_float(row.get('transfer_fee', 0)),
            'clearing_fee': self._safe_float(row.get('clearing_fee', 0)),
            'net_amount': self._safe_float(row.get('net_amount', 0)),
            'balance': self._safe_float(row.get('balance', 0)),
            'position': 0,
            'shareholder_code': str(row.get('shareholder_code', '')),
            'currency': str(row.get('currency', '人民币')),
            'trade_id': str(row.get('trade_id', '')),
            'security_full_name': str(row.get('security_full_name', '')),
            'remark': str(row.get('remark', '')),
            'record_type': RecordType.REPO,
        }
    
    def _parse_dividend(self, row: pd.Series) -> Dict[str, Any]:
        return {
            'date': str(row.get('date', '')),
            'security_code': self._format_code(row.get('security_code', '')),
            'security_name': str(row.get('security_name', '')),
            'business_type': '红利入账',
            'trade_type': 'dividend',
            'price': 0.0,
            'quantity': self._safe_int(row.get('quantity', 0)),
            'amount': self._safe_float(row.get('amount', 0)),
            'commission': 0.0,
            'stamp_tax': 0.0,
            'transfer_fee': 0.0,
            'clearing_fee': 0.0,
            'net_amount': self._safe_float(row.get('net_amount', 0)),
            'balance': self._safe_float(row.get('balance', 0)),
            'position': 0,
            'shareholder_code': str(row.get('shareholder_code', '')),
            'currency': str(row.get('currency', '人民币')),
            'trade_id': '',
            'security_full_name': str(row.get('security_full_name', '')),
            'remark': '',
            'record_type': RecordType.DIVIDEND,
        }
    
    def _parse_stock_dividend(self, row: pd.Series) -> Dict[str, Any]:
        return {
            'date': str(row.get('date', '')),
            'security_code': self._format_code(row.get('security_code', '')),
            'security_name': str(row.get('security_name', '')),
            'business_type': '红股入账',
            'trade_type': 'stock_dividend',
            'price': 0.0,
            'quantity': self._safe_int(row.get('quantity', 0)),
            'amount': 0.0,
            'commission': 0.0,
            'stamp_tax': 0.0,
            'transfer_fee': 0.0,
            'clearing_fee': 0.0,
            'net_amount': 0.0,
            'balance': self._safe_float(row.get('balance', 0)),
            'position': self._safe_int(row.get('position', 0)),
            'shareholder_code': str(row.get('shareholder_code', '')),
            'currency': str(row.get('currency', '人民币')),
            'trade_id': '',
            'security_full_name': str(row.get('security_full_name', '')),
            'remark': '',
            'record_type': RecordType.STOCK_DIVIDEND,
        }
    
    def _parse_dividend_tax(self, row: pd.Series) -> Dict[str, Any]:
        return {
            'date': str(row.get('date', '')),
            'security_code': self._format_code(row.get('security_code', '')),
            'security_name': str(row.get('security_name', '')),
            'business_type': '股息红利差异扣税',
            'trade_type': 'dividend_tax',
            'price': 0.0,
            'quantity': 0,
            'amount': 0.0,
            'commission': 0.0,
            'stamp_tax': 0.0,
            'transfer_fee': self._safe_float(row.get('transfer_fee', 0)),
            'clearing_fee': 0.0,
            'net_amount': 0.0,
            'balance': self._safe_float(row.get('balance', 0)),
            'position': 0,
            'shareholder_code': str(row.get('shareholder_code', '')),
            'currency': str(row.get('currency', '人民币')),
            'trade_id': '',
            'security_full_name': str(row.get('security_full_name', '')),
            'remark': '',
            'record_type': RecordType.DIVIDEND_TAX,
        }
    
    def _parse_designate(self, row: pd.Series) -> Dict[str, Any]:
        return {
            'date': str(row.get('date', '')),
            'security_code': self._format_code(row.get('security_code', '')),
            'security_name': str(row.get('security_name', '')),
            'business_type': '指定交易',
            'trade_type': 'designate',
            'price': 0.0,
            'quantity': 0,
            'amount': 0.0,
            'commission': 0.0,
            'stamp_tax': 0.0,
            'transfer_fee': 0.0,
            'clearing_fee': 0.0,
            'net_amount': 0.0,
            'balance': 0.0,
            'position': 0,
            'shareholder_code': str(row.get('shareholder_code', '')),
            'currency': str(row.get('currency', '人民币')),
            'trade_id': str(row.get('trade_id', '')),
            'security_full_name': str(row.get('security_full_name', '')),
            'remark': '',
            'record_type': RecordType.DESIGNATE,
        }
    
    def _parse_unknown(self, row: pd.Series) -> Dict[str, Any]:
        return {
            'date': str(row.get('date', '')),
            'security_code': self._format_code(row.get('security_code', '')),
            'security_name': str(row.get('security_name', '')),
            'business_type': str(row.get('business_type', '')),
            'trade_type': 'unknown',
            'price': self._safe_float(row.get('price', 0)),
            'quantity': self._safe_int(row.get('quantity', 0)),
            'amount': self._safe_float(row.get('amount', 0)),
            'commission': self._safe_float(row.get('commission', 0)),
            'stamp_tax': self._safe_float(row.get('stamp_tax', 0)),
            'transfer_fee': self._safe_float(row.get('transfer_fee', 0)),
            'clearing_fee': self._safe_float(row.get('clearing_fee', 0)),
            'net_amount': self._safe_float(row.get('net_amount', 0)),
            'balance': self._safe_float(row.get('balance', 0)),
            'position': self._safe_int(row.get('position', 0)),
            'shareholder_code': str(row.get('shareholder_code', '')),
            'currency': str(row.get('currency', '人民币')),
            'trade_id': str(row.get('trade_id', '')),
            'security_full_name': str(row.get('security_full_name', '')),
            'remark': str(row.get('remark', '')),
            'record_type': RecordType.UNKNOWN,
        }
    
    def _format_code(self, code) -> str:
        if code is None:
            return ''
        code_str = str(code).strip()
        if code_str == '' or code_str == 'nan':
            return ''
        if '.' in code_str:
            code_str = code_str.split('.')[0]
        if code_str.isdigit():
            return code_str.zfill(6)
        return code_str
    
    def _safe_float(self, value) -> float:
        if value is None:
            return 0.0
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_int(self, value) -> int:
        if value is None:
            return 0
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return int(float(value))
        except (ValueError, TypeError):
            return 0
