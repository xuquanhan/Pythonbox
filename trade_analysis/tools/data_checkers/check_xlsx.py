"""
检查新的 xlsx 清算文件
"""
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd

XLSX_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'raw' / '23_26_settlement.xlsx')

def check_xlsx():
    print("=" * 80)
    print("检查 xlsx 清算文件")
    print("=" * 80)

    try:
        # 尝试读取 xlsx
        df = pd.read_excel(XLSX_PATH, engine='openpyxl')
        print(f"\n✓ 成功读取 xlsx 文件")
        print(f"  总行数: {len(df)}")
        print(f"  总列数: {len(df.columns)}")

        print(f"\n列名:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")

        print(f"\n前5行数据:")
        print(df.head().to_string())

        # 检查601989
        if '证券代码' in df.columns:
            df_601989 = df[df['证券代码'] == '601989']
            print(f"\n601989 记录数: {len(df_601989)}")
            if len(df_601989) > 0:
                print(df_601989.to_string())

    except Exception as e:
        print(f"\n✗ 读取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_xlsx()
