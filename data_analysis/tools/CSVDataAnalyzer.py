import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import acf, pacf
from scipy.fft import fft, fftfreq
import tkinter as tk
from tkinter import filedialog
import string

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def column_letter_to_index(letter):
    """将Excel列字母转换为数字索引 (例如: A->0, B->1, AA->26)"""
    letter = letter.upper()
    result = 0
    for char in letter:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1  # 转换为0基索引

def parse_range_input(range_str):
    """解析范围输入，例如 "B3:B222" """
    parts = range_str.split(':')
    if len(parts) != 2:
        raise ValueError("范围格式不正确，请使用例如 'B3:B222' 的格式")
    
    start_part = parts[0].strip()
    end_part = parts[1].strip()
    
    # 提取列和行信息
    start_col = ''.join([c for c in start_part if c.isalpha()]).upper()
    start_row = int(''.join([c for c in start_part if c.isdigit()]))
    end_row = int(''.join([c for c in end_part if c.isdigit()]))
    
    return start_col, start_row, end_row

def select_csv_file():
    """打开文件选择对话框让用户选择CSV文件"""
    # 隐藏主窗口
    root = tk.Tk()
    root.withdraw()
    
    # 打开文件选择对话框
    file_path = filedialog.askopenfilename(
        title="选择CSV文件",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    # 销毁主窗口
    root.destroy()
    
    return file_path

def convert_to_numeric(data):
    """将数据转换为数值类型"""
    numeric_data = []
    for item in data:
        try:
            # 尝试转换为浮点数
            numeric_data.append(float(item))
        except (ValueError, TypeError):
            # 如果转换失败，跳过该项
            print(f"警告: 无法将 '{item}' 转换为数值，已跳过")
            continue
    return numeric_data

def read_csv_data():
    """读取CSV数据"""
    # 让用户选择CSV文件
    print("请选择CSV文件...")
    file_path = select_csv_file()
    
    if not file_path:
        print("未选择文件，程序退出。")
        return None
    
    # 尝试不同的编码读取CSV文件
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
    df = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"成功读取文件: {file_path} (编码: {encoding})")
            break
        except Exception as e:
            print(f"使用 {encoding} 编码读取失败: {str(e)[:50]}...")
            continue
    
    if df is None:
        print("尝试多种编码后仍然无法读取文件，请检查文件格式。")
        return None
    
    print(f"数据集包含 {len(df)} 行")
    
    # 询问用户是否知道数据集长度
    know_length = input("您是否知道需要读取的数据范围？(y/n): ").lower().strip()
    
    if know_length == 'y':
        # 用户知道数据范围，要求输入范围
        range_input = input("请输入数据范围 (例如: B3:B222): ").strip()
        try:
            # 解析范围输入
            col, start_row, end_row = parse_range_input(range_input)
            # 将列字母转换为索引
            col_index = column_letter_to_index(col)
            # 提取数据
            data = df.iloc[start_row-1:end_row, col_index].dropna().tolist()
            print(f"成功从范围 {range_input} 提取 {len(data)} 个数据点")
            # 转换为数值类型
            numeric_data = convert_to_numeric(data)
            print(f"转换后得到 {len(numeric_data)} 个数值数据点")
            return numeric_data
        except Exception as e:
            print(f"解析范围输入失败: {e}")
            return None
    else:
        # 用户不知道数据范围，要求输入列
        column_input = input("请输入数据所在的列 (例如: C): ").strip().upper()
        try:
            # 将列字母转换为索引
            col_index = column_letter_to_index(column_input)
            # 提取整列数据并去除空值
            data = df.iloc[:, col_index].dropna().tolist()
            print(f"成功从列 {column_input} 提取 {len(data)} 个数据点")
            # 转换为数值类型
            numeric_data = convert_to_numeric(data)
            print(f"转换后得到 {len(numeric_data)} 个数值数据点")
            return numeric_data
        except Exception as e:
            print(f"读取列数据失败: {e}")
            return None

def explain_analysis_to_beginner(data, outliers, autocorr, yf_positive, xf_positive, slope, r_value):
    """为统计学入门者提供易于理解的分析解释"""
    print("\n" + "=" * 60)
    print("简易数据分析报告（入门版）")
    print("=" * 60)
    
    print("\n这份报告将用通俗易懂的语言解释数据分析结果：")
    
    # 基本统计解释
    print(f"\n1. 数据概况:")
    print(f"   我们分析了 {len(data)} 个数据点")
    print(f"   这些数据的平均值是 {np.mean(data):.4f}")
    print(f"   数据最小值是 {min(data):.4f}，最大值是 {max(data):.4f}")
    print(f"   数据的标准差是 {np.std(data):.4f}，这个数值越大说明数据波动越大")
    
    # 趋势解释
    print(f"\n2. 数据趋势:")
    if slope > 0.001:
        print("   整体来看，数据呈上升趋势")
        print(f"   每增加一个数据点，数值平均增加 {slope:.6f}")
    elif slope < -0.001:
        print("   整体来看，数据呈下降趋势")
        print(f"   每增加一个数据点，数值平均减少 {abs(slope):.6f}")
    else:
        print("   整体来看，数据没有明显的上升或下降趋势")
    
    # 异常值解释
    print(f"\n3. 异常数据:")
    if len(outliers) > 0:
        print(f"   我们发现了 {len(outliers)} 个异常数据点")
        print("   这些数据点与其他数据差异较大，可能是特殊情况或测量误差")
    else:
        print("   没有发现明显的异常数据点")
    
    # 相关性解释
    print(f"\n4. 数据的规律性:")
    if abs(autocorr[1]) > 0.3:
        print("   数据具有一定的规律性，当前值与前一个值有一定关联")
    else:
        print("   数据看起来比较随机，当前值与前一个值关联不大")
    
    # 周期性解释
    print(f"\n5. 数据的周期性:")
    top_freq_indices = np.argsort(yf_positive)[-3:]  # 前3个主要频率
    periodic_found = False
    for idx in reversed(top_freq_indices):
        if xf_positive[idx] > 0.001:
            period = 1 / xf_positive[idx] if xf_positive[idx] > 0 else float('inf')
            if period < len(data)/2:  # 只考虑合理周期
                print(f"   数据可能存在周期性变化，大约每 {period:.1f} 个数据点重复一次")
                periodic_found = True
                break
    
    if not periodic_found:
        print("   数据没有明显的周期性变化")
    
    print("\n" + "=" * 60)
    print("简易分析报告结束")
    print("=" * 60)

def analyze_data(data):
    """执行数据分析"""
    if len(data) == 0:
        print("错误: 没有有效的数值数据可供分析")
        return
        
    print("=" * 60)
    print("数据趋势分析报告")
    print("=" * 60)

    # 1. 基本统计分析
    print(f"\n1. 数据基本信息:")
    print(f"   数据总量: {len(data)} 个点")
    print(f"   数据范围: {min(data):.4f} 到 {max(data):.4f}")
    print(f"   平均值: {np.mean(data):.6f}")
    print(f"   标准差: {np.std(data):.6f}")
    print(f"   中位数: {np.median(data):.6f}")
    print(f"   偏度: {stats.skew(data):.6f}")
    print(f"   峰度: {stats.kurtosis(data):.6f}")

    # 创建主图
    fig = plt.figure(figsize=(20, 16))

    # 2. 整体趋势可视化
    ax1 = plt.subplot(4, 4, 1)
    plt.plot(data, 'b-', alpha=0.7, linewidth=0.8)
    plt.title('原始数据序列', fontsize=12, fontweight='bold')
    plt.xlabel('数据点索引')
    plt.ylabel('数值')
    plt.grid(True, alpha=0.3)

    # 3. 移动平均趋势
    ax2 = plt.subplot(4, 4, 2)
    window_size = min(50, len(data) // 10)  # 自适应窗口大小
    moving_avg = pd.Series(data).rolling(window=window_size, center=True).mean()
    plt.plot(data, 'b-', alpha=0.3, linewidth=0.5, label='原始数据')
    plt.plot(moving_avg, 'r-', linewidth=2, label=f'{window_size}点移动平均')
    plt.title('移动平均趋势', fontsize=12, fontweight='bold')
    plt.xlabel('数据点索引')
    plt.ylabel('数值')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 4. 数据分布直方图
    ax3 = plt.subplot(4, 4, 3)
    n, bins, patches = plt.hist(data, bins=100, alpha=0.7, edgecolor='black', density=True)
    plt.title('数据分布直方图', fontsize=12, fontweight='bold')
    plt.xlabel('数值')
    plt.ylabel('概率密度')
    plt.grid(True, alpha=0.3)

    # 添加正态分布曲线对比
    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)
    p = stats.norm.pdf(x, np.mean(data), np.std(data))
    plt.plot(x, p, 'r-', linewidth=2, label='正态分布')
    plt.axvline(np.mean(data), color='r', linestyle='--', label=f'均值: {np.mean(data):.4f}')
    plt.axvline(np.median(data), color='g', linestyle='--', label=f'中位数: {np.median(data):.4f}')
    plt.legend()

    # 5. Q-Q图（正态性检验）
    ax4 = plt.subplot(4, 4, 4)
    stats.probplot(data, dist="norm", plot=plt)
    plt.title('Q-Q图 (正态性检验)', fontsize=12, fontweight='bold')
    plt.grid(True, alpha=0.3)

    # 6. 波动性分析 - 滚动标准差
    ax5 = plt.subplot(4, 4, 5)
    rolling_std = pd.Series(data).rolling(window=window_size, center=True).std()
    plt.plot(rolling_std, 'g-', linewidth=1.5)
    plt.title(f'{window_size}点滚动标准差', fontsize=12, fontweight='bold')
    plt.xlabel('数据点索引')
    plt.ylabel('标准差')
    plt.grid(True, alpha=0.3)

    # 7. 异常值检测
    ax6 = plt.subplot(4, 4, 6)
    z_scores = np.abs(stats.zscore(data))
    outliers = np.where(z_scores > 3)[0]
    plt.plot(data, 'b-', alpha=0.5, linewidth=0.8)
    plt.scatter(outliers, [data[i] for i in outliers], color='red', s=30, zorder=5, label='异常值 (|z|>3)')
    plt.title(f'异常值检测 (共{len(outliers)}个)', fontsize=12, fontweight='bold')
    plt.xlabel('数据点索引')
    plt.ylabel('数值')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 8. 自相关函数 (ACF)
    ax7 = plt.subplot(4, 4, 7)
    lags = min(100, len(data) // 10)  # 自适应滞后数
    autocorr = acf(data, nlags=lags)
    plt.stem(range(lags + 1), autocorr, basefmt=" ")
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    plt.axhline(y=1.96 / np.sqrt(len(data)), color='r', linestyle='--', alpha=0.5, label='95%置信区间')
    plt.axhline(y=-1.96 / np.sqrt(len(data)), color='r', linestyle='--', alpha=0.5)
    plt.title('自相关函数 (ACF)', fontsize=12, fontweight='bold')
    plt.xlabel('滞后')
    plt.ylabel('自相关系数')
    plt.grid(True, alpha=0.3)
    plt.legend()

    # 9. 偏自相关函数 (PACF)
    ax8 = plt.subplot(4, 4, 8)
    partial_autocorr = pacf(data, nlags=min(50, lags))
    plt.stem(range(len(partial_autocorr)), partial_autocorr, basefmt=" ")
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    plt.axhline(y=1.96 / np.sqrt(len(data)), color='r', linestyle='--', alpha=0.5, label='95%置信区间')
    plt.axhline(y=-1.96 / np.sqrt(len(data)), color='r', linestyle='--', alpha=0.5)
    plt.title('偏自相关函数 (PACF)', fontsize=12, fontweight='bold')
    plt.xlabel('滞后')
    plt.ylabel('偏自相关系数')
    plt.grid(True, alpha=0.3)
    plt.legend()

    # 10. 频谱分析
    ax9 = plt.subplot(4, 4, 9)
    yf = fft(data)
    xf = fftfreq(len(data), 1)
    positive_freq = xf > 0
    xf_positive = xf[positive_freq]
    yf_positive = 2.0 / len(data) * np.abs(yf[positive_freq])
    plt.plot(xf_positive, yf_positive)
    plt.title('频谱分析', fontsize=12, fontweight='bold')
    plt.xlabel('频率')
    plt.ylabel('幅度')
    plt.grid(True, alpha=0.3)

    # 11. 累积分布函数
    ax10 = plt.subplot(4, 4, 10)
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    plt.plot(sorted_data, cdf, 'b-', linewidth=2)
    plt.title('累积分布函数 (CDF)', fontsize=12, fontweight='bold')
    plt.xlabel('数值')
    plt.ylabel('累积概率')
    plt.grid(True, alpha=0.3)

    # 12. 箱线图
    ax11 = plt.subplot(4, 4, 11)
    plt.boxplot(data, vert=True)
    plt.title('箱线图', fontsize=12, fontweight='bold')
    plt.ylabel('数值')
    plt.grid(True, alpha=0.3)

    # 13. 分段趋势分析 (前4段)
    ax12 = plt.subplot(4, 4, 12)
    num_segments = 4
    segment_length = len(data) // num_segments
    colors = ['blue', 'green', 'red', 'purple']

    for i in range(num_segments):
        start_idx = i * segment_length
        end_idx = (i + 1) * segment_length if i < num_segments - 1 else len(data)
        segment_data = data[start_idx:end_idx]

        # 计算每段的趋势线
        x_segment = np.array(range(len(segment_data)))
        slope_segment, intercept, r_value_segment, p_value, std_err = stats.linregress(x_segment, segment_data)

        plt.plot(range(start_idx, end_idx), segment_data, color=colors[i], alpha=0.7,
                 linewidth=1, label=f'段{i + 1}')

    plt.title('数据分段展示', fontsize=12, fontweight='bold')
    plt.xlabel('数据点索引')
    plt.ylabel('数值')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 14. 移动平均对比 (不同窗口)
    ax13 = plt.subplot(4, 4, 13)
    windows = [10, 30, 50]
    for window in windows:
        if window < len(data):
            ma = pd.Series(data).rolling(window=window, center=True).mean()
            plt.plot(ma, label=f'{window}点移动平均', linewidth=1.5)
    plt.title('不同窗口移动平均对比', fontsize=12, fontweight='bold')
    plt.xlabel('数据点索引')
    plt.ylabel('数值')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 15. 数据差分 (检测平稳性)
    ax14 = plt.subplot(4, 4, 14)
    diff_data = np.diff(data)
    plt.plot(range(1, len(data)), diff_data, 'b-', alpha=0.7, linewidth=0.8)
    plt.title('一阶差分序列', fontsize=12, fontweight='bold')
    plt.xlabel('数据点索引')
    plt.ylabel('差分值')
    plt.grid(True, alpha=0.3)

    # 16. 滚动统计量
    ax15 = plt.subplot(4, 4, 15)
    rolling_mean = pd.Series(data).rolling(window=window_size, center=True).mean()
    rolling_std = pd.Series(data).rolling(window=window_size, center=True).std()

    plt.plot(rolling_mean, 'b-', label='滚动均值', linewidth=1.5)
    plt.plot(rolling_std, 'r-', label='滚动标准差', linewidth=1.5)
    plt.title('滚动统计量', fontsize=12, fontweight='bold')
    plt.xlabel('数据点索引')
    plt.ylabel('数值')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 17. 季节性分解模拟 (简单版本)
    ax16 = plt.subplot(4, 4, 16)
    # 使用移动平均来近似趋势成分
    trend = pd.Series(data).rolling(window=100, center=True).mean()
    # 残差 = 原始数据 - 趋势
    residual = [data[i] - (trend[i] if not pd.isna(trend[i]) else 0) for i in range(len(data))]

    plt.plot(data, 'b-', alpha=0.3, label='原始数据', linewidth=0.8)
    plt.plot(trend, 'r-', label='趋势成分', linewidth=1.5)
    plt.plot(residual, 'g-', alpha=0.5, label='残差成分', linewidth=0.8)
    plt.title('趋势-残差分解', fontsize=12, fontweight='bold')
    plt.xlabel('数据点索引')
    plt.ylabel('数值')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()

    # 输出详细分析报告
    print(f"\n2. 异常值分析:")
    print(f"   检测到 {len(outliers)} 个异常值 (Z-score > 3)")
    if len(outliers) > 0:
        print(f"   最大异常值: {max([data[i] for i in outliers]):.4f}")
        print(f"   最小异常值: {min([data[i] for i in outliers]):.4f}")

    print(f"\n3. 自相关分析:")
    print(f"   一阶自相关系数: {autocorr[1]:.4f}")
    print(f"   二阶自相关系数: {autocorr[2]:.4f}")

    print(f"\n4. 频谱分析:")
    top_freq_indices = np.argsort(yf_positive)[-5:]  # 前5个主要频率
    print("   主要频率成分:")
    for idx in top_freq_indices:
        if xf_positive[idx] > 0.001:  # 忽略接近零的频率
            period = 1 / xf_positive[idx] if xf_positive[idx] > 0 else float('inf')
            print(f"     频率: {xf_positive[idx]:.6f}, 周期: {period:.1f}点, 幅度: {yf_positive[idx]:.6f}")

    print(f"\n5. 趋势分析:")
    # 计算整体趋势
    x = np.array(range(len(data)))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)
    print(f"   整体趋势斜率: {slope:.8f}")
    print(f"   趋势显著性 (R²): {r_value ** 2:.4f}")
    if slope > 0:
        print("   整体趋势: 上升")
    elif slope < 0:
        print("   整体趋势: 下降")
    else:
        print("   整体趋势: 平稳")

    print(f"\n6. 数据质量评估:")
    missing_values = sum(pd.isna(data)) if hasattr(data, 'isna') else 0
    print(f"   缺失值数量: {missing_values}")
    print(f"   数据完整性: {(1 - missing_values / len(data)) * 100:.2f}%")

    # 为统计学入门者提供简易解释
    explain_analysis_to_beginner(data, outliers, autocorr, yf_positive, xf_positive, slope, r_value)

    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)

def main():
    # 读取数据
    data = read_csv_data()
    if data is None:
        print("数据读取失败，程序退出。")
        return
    
    # 执行分析
    analyze_data(data)

# 运行主程序
if __name__ == "__main__":
    main()