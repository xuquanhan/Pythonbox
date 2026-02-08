import pandas as pd
import numpy as np

# 创建测试数据，模拟从第3行开始的数据
print("创建测试数据文件，模拟从第3行开始的数据...")

# 创建带头部信息的数据
dates = pd.date_range('2020-01-01', periods=50, freq='D')
prices = 100 * (1 + np.random.randn(50) * 0.02).cumprod()
volumes = np.random.randint(1000, 10000, 50)

# 创建数据DataFrame
data_df = pd.DataFrame({
    '日期': dates,
    '资产价格': prices,
    '交易量': volumes
})

# 创建头部信息
header_rows = [
    ['数据报告', '测试文件', ''],
    ['创建日期', '2023-12-01', ''],
]

# 将头部信息和数据合并
header_df = pd.DataFrame(header_rows, columns=['', '', ''])
full_df = pd.concat([header_df, data_df], ignore_index=True)

# 保存文件
filename = 'test_data_from_row3.xlsx'
full_df.to_excel(filename, index=False, header=False)
print(f"测试文件 '{filename}' 已创建")
print("文件结构:")
print("- 第1-2行: 头部信息")
print("- 第3行开始: 数据列标题")
print("- 第4行开始: 实际数据")

# 显示文件前几行
print("\n文件前8行内容:")
for i, row in full_df.head(8).iterrows():
    print(f"第{i+1}行: {list(row)}")