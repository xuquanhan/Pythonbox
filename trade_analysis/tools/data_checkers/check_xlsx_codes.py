"""
检查xlsx文件中的证券代码格式
"""
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd

XLSX_PATH = str(Path(__file__).parent.parent.parent / 'data' / 'raw' / '23_26_settlement.xlsx')

def check_codes():
    print("=" * 80)
    print("检查 xlsx 文件中的证券代码")
    print("=" * 80)

    df = pd.read_excel(XLSX_PATH, engine='openpyxl')

    print(f"\n总记录数: {len(df)}")

    # 检查证券代码的数据类型和唯一值
    print(f"\n证券代码数据类型: {df['证券代码'].dtype}")

    print(f"\n包含 '989' 的代码:")
    for code in df['证券代码'].unique():
        if pd.notna(code) and '989' in str(code):
            count = len(df[df['证券代码'] == code])
            print(f"  {code} ({type(code).__name__}): {count} 条")

    # 检查601989的各种格式
    print(f"\n检查 601989 的各种格式:")
    for code in ['601989', 601989, '601989.0', 601989.0]:
        matches = df[df['证券代码'] == code]
        print(f"  '{code}' ({type(code).__name__}): {len(matches)} 条")

if __name__ == "__main__":
    check_codes()
