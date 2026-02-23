"""
只获取当前持仓股票的历史价格
"""
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
from datetime import datetime
from trade_analysis.db.database import DatabaseManager
from trade_analysis.models.profit_calculator import ProfitCalculator
from trade_analysis.services.price_fetcher import PriceFetcher
import sqlite3

DB_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'trade_data.db')

def fetch_position_prices():
    print("=" * 80)
    print("获取持仓股票历史价格")
    print("=" * 80)

    db = DatabaseManager(DB_PATH)
    df = db.get_all_trade_records()

    # 计算当前持仓
    calculator = ProfitCalculator(df)
    positions = calculator._calculate_positions()

    # 只获取有持仓的股票
    position_stocks = list(positions.keys())

    print(f"\n当前持仓股票数量: {len(position_stocks)}")
    for code in position_stocks:
        print(f"  - {code} {positions[code]['name']}: {positions[code]['quantity']}股")

    # 获取日期范围
    start_date = min(df['date']).strftime('%Y%m%d')
    end_date = max(df['date']).strftime('%Y%m%d')
    print(f"\n日期范围: {start_date} ~ {end_date}")

    # 初始化价格获取器
    print("\n初始化价格获取器...")
    fetcher = PriceFetcher()

    # 获取价格
    all_prices = []
    failed_stocks = []

    print(f"\n开始获取持仓股票价格...")
    for i, code in enumerate(position_stocks, 1):
        print(f"\n[{i}/{len(position_stocks)}] 获取 {code} 的历史价格...")

        try:
            prices_df = fetcher.get_history_prices(code, start_date, end_date)

            if prices_df is not None and not prices_df.empty:
                print(f"  ✓ 获取到 {len(prices_df)} 天的价格数据")

                for _, row in prices_df.iterrows():
                    # 将日期转换为字符串格式
                    if isinstance(row['date'], pd.Timestamp):
                        date_str = row['date'].strftime('%Y%m%d')
                    else:
                        date_str = str(row['date']).replace('-', '')[:8]

                    all_prices.append({
                        'date': date_str,
                        'security_code': code,
                        'close_price': float(row['close'])
                    })
            else:
                print(f"  ✗ 无法获取历史价格")
                failed_stocks.append(code)

        except Exception as e:
            print(f"  ✗ 错误: {e}")
            failed_stocks.append(code)

    print(f"\n获取完成，共 {len(all_prices)} 条价格记录")

    # 保存到数据库
    if all_prices:
        print(f"\n保存到数据库...")
        conn = db._get_connection()
        cursor = conn.cursor()

        inserted = 0
        for price in all_prices:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_prices (date, security_code, close_price, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    price['date'],
                    price['security_code'],
                    price['close_price'],
                    datetime.now().isoformat()
                ))
                inserted += 1
            except Exception as e:
                print(f"  保存失败 {price['security_code']} {price['date']}: {e}")

        conn.commit()
        conn.close()
        print(f"成功保存 {inserted} 条价格记录")

    # 验证
    print(f"\n验证...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM daily_prices")
    count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT security_code) FROM daily_prices")
    stock_count = cursor.fetchone()[0]
    conn.close()

    print(f"  数据库中共有 {count} 条价格记录")
    print(f"  覆盖 {stock_count} 只股票")

    if failed_stocks:
        print(f"\n失败股票: {failed_stocks}")

if __name__ == "__main__":
    fetch_position_prices()
