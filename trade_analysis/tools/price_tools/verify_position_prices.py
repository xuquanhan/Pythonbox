"""
验证持仓股票的价格数据
"""
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
from trade_analysis.db.database import DatabaseManager
from trade_analysis.models.profit_calculator import ProfitCalculator
import sqlite3

DB_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'trade_data.db')

def verify():
    print("=" * 80)
    print("验证持仓股票价格数据")
    print("=" * 80)

    db = DatabaseManager(DB_PATH)
    df = db.get_all_trade_records()

    # 计算当前持仓
    calculator = ProfitCalculator(df)
    positions = calculator._calculate_positions()

    print(f"\n当前持仓股票: {len(positions)} 只\n")

    # 查询数据库中的价格
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for code in sorted(positions.keys()):
        pos = positions[code]

        # 查询该股票的价格记录
        cursor.execute('''
            SELECT COUNT(*), MIN(date), MAX(date)
            FROM daily_prices
            WHERE security_code = ?
        ''', (code,))
        result = cursor.fetchone()
        count, min_date, max_date = result

        if count > 0:
            print(f"✓ {code} {pos['name']}: {pos['quantity']}股")
            print(f"    价格数据: {count} 天 ({min_date} ~ {max_date})")
        else:
            print(f"✗ {code} {pos['name']}: {pos['quantity']}股 - 无价格数据")

    conn.close()

    print(f"\n" + "=" * 80)
    print("价格数据验证完成！")
    print("=" * 80)

if __name__ == "__main__":
    verify()
