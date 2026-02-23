import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = str(Path(__file__).parent.parent / 'data' / 'trade_data.db')


class DatabaseManager:
    """
    数据库管理器
    
    使用 SQLite 存储清算数据，支持增量更新
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = DEFAULT_DB_PATH
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
    
    def _init_database(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                security_code TEXT,
                security_name TEXT,
                business_type TEXT,
                trade_type TEXT,
                price REAL,
                quantity INTEGER,
                amount REAL,
                commission REAL,
                stamp_tax REAL,
                transfer_fee REAL,
                clearing_fee REAL,
                net_amount REAL,
                balance REAL,
                position INTEGER,
                shareholder_code TEXT,
                currency TEXT,
                trade_id TEXT,
                security_full_name TEXT,
                remark TEXT,
                record_type TEXT,
                is_repo INTEGER,
                total_fee REAL,
                created_at TEXT,
                UNIQUE(date, security_code, trade_type, quantity, amount, price, trade_id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_trade_records_date 
            ON trade_records(date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_trade_records_code 
            ON trade_records(security_code)
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                security_code TEXT NOT NULL,
                close_price REAL,
                created_at TEXT,
                UNIQUE(date, security_code)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_daily_prices_date 
            ON daily_prices(date)
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                security_code TEXT NOT NULL,
                security_name TEXT,
                quantity INTEGER,
                cost_price REAL,
                close_price REAL,
                market_value REAL,
                created_at TEXT,
                UNIQUE(date, security_code)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_daily_positions_date 
            ON daily_positions(date)
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_net_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                cash_balance REAL,
                repo_amount REAL,
                stock_market_value REAL,
                total_net_value REAL,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_last_date(self) -> Optional[str]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT MAX(date) FROM trade_records')
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result and result[0] else None
    
    def insert_trade_records(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        inserted = 0
        created_at = datetime.now().isoformat()
        
        for _, row in df.iterrows():
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO trade_records (
                        date, security_code, security_name, business_type, trade_type,
                        price, quantity, amount, commission, stamp_tax, transfer_fee,
                        clearing_fee, net_amount, balance, position, shareholder_code,
                        currency, trade_id, security_full_name, remark, record_type,
                        is_repo, total_fee, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['date'].strftime('%Y%m%d') if hasattr(row['date'], 'strftime') else str(row['date']),
                    str(row.get('security_code', '')),
                    str(row.get('security_name', '')),
                    str(row.get('business_type', '')),
                    str(row.get('trade_type', '')),
                    float(row.get('price', 0)),
                    int(row.get('quantity', 0)),
                    float(row.get('amount', 0)),
                    float(row.get('commission', 0)),
                    float(row.get('stamp_tax', 0)),
                    float(row.get('transfer_fee', 0)),
                    float(row.get('clearing_fee', 0)),
                    float(row.get('net_amount', 0)),
                    float(row.get('balance', 0)),
                    int(row.get('position', 0)),
                    str(row.get('shareholder_code', '')),
                    str(row.get('currency', '人民币')),
                    str(row.get('trade_id', '')),
                    str(row.get('security_full_name', '')),
                    str(row.get('remark', '')),
                    str(row.get('record_type', '')),
                    1 if row.get('is_repo', False) else 0,
                    float(row.get('total_fee', 0)),
                    created_at
                ))
                inserted += 1
            except Exception as e:
                logger.warning(f"插入记录失败: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"成功插入 {inserted} 条记录")
        return inserted
    
    def load_trade_records(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        conn = self._get_connection()
        
        query = "SELECT * FROM trade_records WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        
        return df
    
    def get_all_trade_records(self) -> pd.DataFrame:
        return self.load_trade_records()
    
    def save_daily_prices(self, prices: List[Dict[str, Any]]) -> int:
        if not prices:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        
        inserted = 0
        for p in prices:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_prices (date, security_code, close_price, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (p['date'], p['security_code'], p['close_price'], created_at))
                inserted += 1
            except Exception as e:
                logger.warning(f"保存价格失败: {e}")
        
        conn.commit()
        conn.close()
        return inserted
    
    def get_daily_prices(self, security_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        conn = self._get_connection()
        
        query = "SELECT * FROM daily_prices WHERE security_code = ?"
        params = [security_code]
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        
        return df

    def get_latest_price(self, security_code: str) -> Optional[float]:
        """
        获取某只股票最新的收盘价

        Args:
            security_code: 股票代码

        Returns:
            最新收盘价，如果没有则返回 None
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT close_price FROM daily_prices
            WHERE security_code = ?
            ORDER BY date DESC
            LIMIT 1
        ''', (security_code,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result and result[0] is not None else None

    def get_all_latest_prices(self) -> Dict[str, float]:
        """
        获取所有股票的最新收盘价

        Returns:
            字典 {股票代码: 收盘价}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT security_code, close_price FROM daily_prices
            WHERE (security_code, date) IN (
                SELECT security_code, MAX(date)
                FROM daily_prices
                GROUP BY security_code
            )
        ''')

        results = cursor.fetchall()
        conn.close()

        return {row[0]: row[1] for row in results if row[1] is not None}

    def save_daily_net_values(self, net_values: List[Dict[str, Any]]) -> int:
        if not net_values:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        
        inserted = 0
        for nv in net_values:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_net_values 
                    (date, cash_balance, repo_amount, stock_market_value, total_net_value, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    nv['date'], nv['cash_balance'], nv['repo_amount'],
                    nv['stock_market_value'], nv['total_net_value'], created_at
                ))
                inserted += 1
            except Exception as e:
                logger.warning(f"保存净值失败: {e}")
        
        conn.commit()
        conn.close()
        return inserted
    
    def get_daily_net_values(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        conn = self._get_connection()
        
        query = "SELECT * FROM daily_net_values WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
        
        return df
    
    def get_record_count(self) -> int:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM trade_records')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def clear_all_data(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM trade_records')
        cursor.execute('DELETE FROM daily_prices')
        cursor.execute('DELETE FROM daily_positions')
        cursor.execute('DELETE FROM daily_net_values')
        conn.commit()
        conn.close()
        logger.info("数据库已清空")
