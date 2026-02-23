"""
添加 159937 黄金9999 的历史价格到数据库
使用 Wind 终端获取的数据
"""
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import sqlite3
from datetime import datetime

DB_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'trade_data.db')

def add_159937_prices():
    print("=" * 80)
    print("添加 159937 黄金9999 价格数据")
    print("=" * 80)

    # 这里需要填入从 Wind 获取的实际价格数据
    # 格式: [(日期, 收盘价), ...]
    # 示例数据，请替换为实际数据
    prices_data = []

    print("\n请提供从 Wind 获取的 159937 价格数据")
    print("格式: 日期(YYYYMMDD), 收盘价")
    print("例如: 20260123, 3.85")
    print("\n或者您可以直接修改此脚本，将价格数据填入 prices_data 列表")

    # 如果已经有数据，请取消下面的注释并填入实际数据
    # prices_data = [
    #     ('20260123', 3.85),
    #     ('20260124', 3.86),
    #     ...
    # ]

    if not prices_data:
        print("\n⚠️ 暂无价格数据，请从 Wind 终端导出后填入脚本")
        return

    # 保存到数据库
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted = 0
    for date_str, close_price in prices_data:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO daily_prices (date, security_code, close_price, created_at)
                VALUES (?, ?, ?, ?)
            ''', (
                date_str,
                '159937',
                float(close_price),
                datetime.now().isoformat()
            ))
            inserted += 1
        except Exception as e:
            print(f"  保存失败 {date_str}: {e}")

    conn.commit()
    conn.close()

    print(f"\n成功保存 {inserted} 条价格记录")

if __name__ == "__main__":
    add_159937_prices()
