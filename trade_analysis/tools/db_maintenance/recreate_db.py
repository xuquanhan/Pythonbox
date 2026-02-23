"""
重新创建数据库表，应用新的唯一键
"""
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import sqlite3
import pandas as pd
from trade_analysis.db.database import DatabaseManager
from trade_analysis.models.data_cleaner import DataCleaner

DB_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'trade_data.db')
XLS_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'raw' / '23_26_交割单查询.xls')

def recreate_db():
    print("=" * 80)
    print("重新创建数据库表")
    print("=" * 80)

    # 1. 备份数据
    print("\n1. 备份现有数据...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trade_records")
    all_data = cursor.fetchall()
    cursor.execute("PRAGMA table_info(trade_records)")
    columns_info = cursor.fetchall()
    columns = [col[1] for col in columns_info]
    print(f"   备份了 {len(all_data)} 条记录")

    # 2. 删除旧表
    print("\n2. 删除旧表...")
    cursor.execute("DROP TABLE IF EXISTS trade_records")
    cursor.execute("DROP TABLE IF EXISTS daily_prices")
    cursor.execute("DROP TABLE IF EXISTS daily_positions")
    print("   旧表已删除")
    conn.commit()
    conn.close()

    # 3. 重新初始化数据库（使用新的表结构）
    print("\n3. 重新初始化数据库...")
    db = DatabaseManager(DB_PATH)
    print("   新表已创建")

    # 4. 读取并导入数据
    print("\n4. 读取交割单文件...")
    cleaner = DataCleaner(XLS_PATH)
    df = cleaner.clean()
    print(f"   读取到 {len(df)} 条记录")

    # 检查601989
    df_601989 = df[df['security_code'] == '601989']
    print(f"   601989 记录数: {len(df_601989)}")

    # 5. 导入数据
    print("\n5. 导入数据...")
    count = db.insert_trade_records(df)
    print(f"   成功导入 {count} 条记录")

    # 6. 验证
    print("\n6. 验证601989...")
    df_db = db.get_all_trade_records()
    db_601989 = df_db[df_db['security_code'] == '601989']
    print(f"   数据库中 601989 记录数: {len(db_601989)}")
    for _, row in db_601989.iterrows():
        date = row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])[:10]
        print(f"   {date} {row['trade_type']} {row['quantity']}股 佣金:{row['commission']} 印花税:{row['stamp_tax']} 过户费:{row['transfer_fee']}")

    print("\n" + "=" * 80)
    print("修复完成！")
    print("=" * 80)

if __name__ == "__main__":
    recreate_db()
