import pandas as pd
import numpy as np

print("请选择要创建的示例数据类型:")
print("1. 包含成交量的完整数据")
print("2. 不包含成交量的简化数据")
choice = input("请输入选择 (1 或 2, 默认为1): ").strip()

if choice == "2":
    # 创建不包含成交量的简化数据
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    prices = 100 * (1 + np.random.randn(100) * 0.02).cumprod()

    # 创建简化版DataFrame
    df = pd.DataFrame({
        '日期': dates,
        '资产价格': prices
    })
    
    filename = 'sample_data_simple.xlsx'
else:
    # 创建包含成交量的完整数据
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    prices = 100 * (1 + np.random.randn(100) * 0.02).cumprod()

    # 创建完整版DataFrame
    df = pd.DataFrame({
        '日期': dates,
        '资产价格': prices,
        '交易量': np.random.randint(1000, 10000, 100)
    })
    
    filename = 'sample_data.xlsx'

# 保存为Excel文件
df.to_excel(filename, index=False)
print(f"\n示例数据文件 '{filename}' 已创建")
print("\n数据结构说明:")
print("列名:")
for i, col in enumerate(df.columns):
    print(f"  {i+1}. {col}")

print("\n数据预览:")
print(df.head(10))

if '交易量' in df.columns:
    print("\n这是一个包含成交量的完整数据集")
else:
    print("\n这是一个不包含成交量的简化数据集")
    print("注意: 成交量是可选数据，模型可以在没有成交量的情况下正常工作")