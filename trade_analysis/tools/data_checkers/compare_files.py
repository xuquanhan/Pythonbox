"""
对比 xls 和 xlsx 文件的内容
"""
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd

XLS_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'raw' / '23_26_交割单查询.xls')
XLSX_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'raw' / '23_26_settlement.xlsx')

def compare():
    print("=" * 80)
    print("对比 xls 和 xlsx 文件")
    print("=" * 80)

    # 读取 xls
    df_xls = pd.read_csv(XLS_PATH, encoding='gbk', sep='\t', header=0)

    # 读取 xlsx
    df_xlsx = pd.read_excel(XLSX_PATH, engine='openpyxl')

    print(f"\nxls 文件: {len(df_xls)} 条记录")
    print(f"xlsx 文件: {len(df_xlsx)} 条记录")

    # 对比 601989
    xls_601989 = df_xls[df_xls['证券代码'] == 601989.0]
    xlsx_601989 = df_xlsx[df_xlsx['证券代码'] == 601989.0]

    print(f"\n601989 在 xls 中: {len(xls_601989)} 条")
    print(f"601989 在 xlsx 中: {len(xlsx_601989)} 条")

    print("\nxls 中的 601989:")
    for _, row in xls_601989.iterrows():
        print(f"  {row['交割日期']} {row['业务类型']} {row['成交数量']}股")

    print("\nxlsx 中的 601989:")
    for _, row in xlsx_601989.iterrows():
        print(f"  {row['交割日期']} {row['业务类型']} {row['成交数量']}股")

if __name__ == "__main__":
    compare()
