import pandas as pd
import numpy as np

print("请选择要创建的示例数据类型:")
print("1. 包含成交量的完整数据 (日频)")
print("2. 不包含成交量的简化数据 (日频)")
print("3. 月频数据示例")
print("4. 带有额外头部信息的示例数据")
print("5. 模拟Wind数据库格式的数据")
choice = input("请输入选择 (1-5, 默认为1): ").strip()

if choice == "2":
    # 创建不包含成交量的日频数据
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    prices = 100 * (1 + np.random.randn(100) * 0.02).cumprod()

    # 创建简化版DataFrame
    df = pd.DataFrame({
        '日期': dates,
        '资产价格': prices
    })
    
    filename = 'sample_data_simple_daily.xlsx'
    frequency = "日频"
elif choice == "3":
    # 创建月频数据
    dates = pd.date_range('2020-01-01', periods=36, freq='M')
    prices = 100 * (1 + np.random.randn(36) * 0.05).cumprod()

    # 创建月频DataFrame
    df = pd.DataFrame({
        '日期': dates,
        '资产价格': prices
    })
    
    filename = 'sample_data_monthly.xlsx'
    frequency = "月频"
elif choice == "4":
    # 创建带有额外头部信息的数据
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    prices = 100 * (1 + np.random.randn(100) * 0.02).cumprod()
    volumes = np.random.randint(1000, 10000, 100)

    # 创建带头部信息的DataFrame
    df = pd.DataFrame({
        '日期': dates,
        '资产价格': prices,
        '交易量': volumes
    })
    
    # 添加头部信息行
    header_info = pd.DataFrame([
        ['数据来源: 示例数据库', '', ''],
        ['创建时间: 2023-01-01', '', '']
    ])
    
    # 合并头部信息和数据
    full_df = pd.concat([header_info, df], ignore_index=True)
    
    filename = 'sample_data_with_header.xlsx'
    frequency = "带头部信息的日频"
elif choice == "5":
    # 创建模拟Wind数据库格式的数据
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    prices = 100 * (1 + np.random.randn(100) * 0.02).cumprod()

    # 创建Wind格式的DataFrame
    wind_df = pd.DataFrame({
        '指标名称': dates,
        '现货价(伦敦市场):黄金:美元': prices
    })
    
    filename = 'wind_format_sample.xlsx'
    frequency = "Wind格式日频"
else:
    # 创建包含成交量的日频数据
    dates = pd.date_range('2020-01-01', periods=100, freq='D')
    prices = 100 * (1 + np.random.randn(100) * 0.02).cumprod()

    # 创建完整版DataFrame
    df = pd.DataFrame({
        '日期': dates,
        '资产价格': prices,
        '交易量': np.random.randint(1000, 10000, 100)
    })
    
    filename = 'sample_data_daily.xlsx'
    frequency = "日频"

# 保存为Excel文件
if choice == "4":
    full_df.to_excel(filename, index=False, header=False)
elif choice == "5":
    wind_df.to_excel(filename, index=False)
else:
    df.to_excel(filename, index=False)
    
print(f"\n{frequency}示例数据文件 '{filename}' 已创建")

if choice not in ["4", "5"]:
    print("\n数据结构说明:")
    print("列名:")
    for i, col in enumerate(df.columns):
        print(f"  {i+1}. {col}")

    print("\n数据预览:")
    print(df.head(10))

    if '交易量' in df.columns:
        print(f"\n这是一个包含成交量的{frequency}数据集")
    else:
        print(f"\n这是一个不包含成交量的{frequency}数据集")
        print("注意: 成交量是可选数据，模型可以在没有成交量的情况下正常工作")
        
    print(f"\n提示: 使用{frequency}数据时，请相应调整模型的时间参数")
elif choice == "4":
    print("\n数据包含2行头部信息，数据从第3行开始")
    print("列名: 日期, 资产价格, 交易量")
    print("此文件可用于测试从第3行开始读取数据的功能")
else:
    print("\n数据采用Wind数据库格式")
    print("列名: 指标名称, 现货价(伦敦市场):黄金:美元")
    print("此文件可用于测试特殊列名格式的处理")