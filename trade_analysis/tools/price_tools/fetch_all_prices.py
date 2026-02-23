"""
获取所有股票的历史价格数据并存入数据库
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
from trade_analysis.services.price_fetcher import PriceFetcher
import time

DB_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'trade_data.db')

def fetch_all_prices():
    print("=" * 80)
    print("获取所有股票历史价格")
    print("=" * 80)

    db = DatabaseManager(DB_PATH)
    df = db.get_all_trade_records()

    # 获取所有交易过的股票
    trade_stocks = df[df['trade_type'].isin(['buy', 'sell'])]['security_code'].unique()
    print(f"\n需要获取价格的股票数量: {len(trade_stocks)}")

    # 获取日期范围
    start_date = min(df['date'])
    end_date = max(df['date'])
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    print(f"日期范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

    # 初始化价格获取器
    print("\n初始化价格获取器...")
    fetcher = PriceFetcher()

    # 检查可用数据源
    available_sources = fetcher.get_available_sources()
    print(f"可用数据源: {available_sources}")

    # 获取所有价格数据
    all_prices = []
    failed_stocks = []

    print(f"\n开始获取历史价格...")
    for i, code in enumerate(sorted(trade_stocks), 1):
        print(f"\n[{i}/{len(trade_stocks)}] 获取 {code} 的历史价格...")

        try:
            # 获取历史价格
            prices_df = fetcher.get_history_prices(code, start_date_str, end_date_str)

            if prices_df is not None and not prices_df.empty:
                print(f"  ✓ 获取到 {len(prices_df)} 天的价格数据")

                # 转换为数据库格式
                for _, row in prices_df.iterrows():
                    all_prices.append({
                        'date': row['date'],
                        'security_code': code,
                        'close_price': row['close']
                    })
            else:
                print(f"  ✗ 无法获取历史价格")
                failed_stocks.append(code)

        except Exception as e:
            print(f"  ✗ 错误: {e}")
            failed_stocks.append(code)

        # 每10只股票保存一次，避免数据丢失
        if i % 10 == 0 and all_prices:
            print(f"  保存进度...")
            save_prices_to_db(db, all_prices)
            all_prices = []

    # 保存剩余的价格数据
    if all_prices:
        save_prices_to_db(db, all_prices)

    print(f"\n" + "=" * 80)
    print(f"获取完成")
    print(f"  成功: {len(trade_stocks) - len(failed_stocks)} 只")
    print(f"  失败: {len(failed_stocks)} 只")
    if failed_stocks:
        print(f"  失败列表: {failed_stocks}")

def save_prices_to_db(db: DatabaseManager, prices: list):
    """保存价格数据到数据库"""
    if not prices:
        return

    conn = db._get_connection()
    cursor = conn.cursor()

    inserted = 0
    for price in prices:
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
    print(f"  已保存 {inserted} 条价格记录")

if __name__ == "__main__":
    fetch_all_prices()
