"""
读取并显示特定日期的交易记录
"""
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd

filepath = str(Path(__file__).parent.parent.parent / 'data' / 'raw' / '2025_2026settlement.xls')

def read_specific_dates():
    df = pd.read_excel(filepath, sheet_name=0, header=None)

    print("=== 2025年12月15-17日的交易记录 ===\n")

    for i, row in df.iterrows():
        date_val = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ''

        if date_val in ['20251215', '20251216', '20251217']:
            print(f"日期: {row.iloc[0]}")
            print(f"证券代码: {row.iloc[1]}")
            print(f"证券名称: {row.iloc[2]}")
            print(f"业务类型: {row.iloc[3]}")
            print(f"价格: {row.iloc[4]}")
            print(f"数量: {row.iloc[5]}")
            print(f"成交金额: {row.iloc[6]}")
            print(f"印花税: {row.iloc[7]}")
            print(f"过户费: {row.iloc[8]}")
            print(f"其他费: {row.iloc[9]}")
            print(f"净额: {row.iloc[10]}")
            print(f"余额: {row.iloc[11]}")
            print(f"剩余数量: {row.iloc[12]}")
            print("-" * 50)

if __name__ == "__main__":
    read_specific_dates()
