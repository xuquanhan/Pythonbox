#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对数周期幂律(LPPL)模型
基于Sornette教授的理论，用于检测金融市场中的泡沫并预测可能的崩盘时间
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
import os

try:
    import tkinter as tk
    from tkinter import filedialog

    TK_AVAILABLE = True
except ImportError:
    TK_AVAILABLE = False

warnings.filterwarnings('ignore')

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class LPPLModel:
    """
    对数周期幂律(LPPL)模型类
    基于Sornette教授的理论，用于检测金融市场中的泡沫并预测可能的崩盘时间
    """

    def __init__(self):
        self.data = None
        self.parameters = {}
        self.results = {}
        self.data_frequency = "daily"  # 默认为日频数据
        self.column_mapping = {}  # 列映射信息
        self.lppl_params = None  # LPPL模型参数

    def load_data_with_dialog(self):
        """
        使用弹窗选择并加载Excel数据
        """
        if not TK_AVAILABLE:
            print("Tkinter不可用，无法使用图形文件选择对话框")
            return self.load_data_manual()

        # 创建根窗口并隐藏
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        # 打开文件选择对话框
        file_path = filedialog.askopenfilename(
            title="选择Excel数据文件",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )

        # 销毁根窗口
        root.destroy()

        if not file_path:
            print("未选择文件，将使用模拟数据")
            return False

        return self.load_data(file_path)

    def load_data_manual(self):
        """
        手动输入路径加载Excel数据
        """
        while True:
            excel_file = input("请输入Excel数据文件路径 (直接回车跳过数据加载): ").strip()
            if not excel_file:
                print("未提供文件路径，将使用模拟数据")
                return False
            if os.path.exists(excel_file):
                return self.load_data(excel_file)
            else:
                print(f"文件 '{excel_file}' 不存在，请重新输入")
                retry = input("是否重新输入文件路径? (y/n): ").strip().lower()
                if retry != 'y':
                    print("将使用模拟数据")
                    return False

    def load_data(self, excel_file):
        """
        加载Excel数据

        参数:
        excel_file (str): Excel文件路径
        """
        try:
            # 先尝试读取前几行来检查数据结构
            header_preview = pd.read_excel(excel_file, nrows=10)
            print("文件前10行预览:")
            print(header_preview.to_string())

            # 询问用户数据从哪一行开始
            start_row_input = input(f"\n数据从第几行开始? (默认为第3行): ").strip()
            start_row = int(start_row_input) - 1 if start_row_input.isdigit() else 2

            # 询问是否有列标题行
            has_header = input("是否有列标题行? (y/n, 默认y): ").strip().lower()

            # 读取Excel文件
            if has_header != 'n':
                # 有标题行的情况
                self.data = pd.read_excel(excel_file, header=start_row, skiprows=range(start_row))
            else:
                # 没有标题行的情况
                self.data = pd.read_excel(excel_file, header=None, skiprows=range(start_row))

            print(f"成功加载数据，共有 {len(self.data)} 行数据")

            # 处理列名
            if has_header == 'n':
                # 如果没有标题行，给列命名
                cols = [f"列{i + 1}" for i in range(len(self.data.columns))]
                self.data.columns = cols
                print("数据列名(自动生成):")
            else:
                # 清理列名中的NaN值和特殊值
                cols = []
                for i, col in enumerate(self.data.columns):
                    if pd.isna(col):
                        cols.append(f"列{i + 1}")
                    else:
                        cols.append(str(col))
                self.data.columns = cols
                print("数据列名:")

            for i, col in enumerate(self.data.columns):
                print(f"  {i + 1}. {col}")

            # 显示前几行数据样本
            print("\n数据样本:")
            print(self.data.head().to_string())

            # 检查关键列并询问数据频率
            self._check_data_columns()
            self._ask_data_frequency()

            return True
        except FileNotFoundError:
            print(f"错误: 找不到文件 '{excel_file}'")
            return False
        except Exception as e:
            print(f"加载数据时发生错误: {str(e)}")
            return False

    def _check_data_columns(self):
        """
        检查数据列并给出建议
        """
        if self.data is None:
            return

        columns = self.data.columns.tolist()
        print(f"\n检测到的数据列: {', '.join(map(str, columns))}")

        # 检查是否有日期列 - 使用更广泛的检测方法
        date_cols = []
        price_cols = []
        volume_cols = []

        # 基于列名检测
        for col in columns:
            col_str = str(col).lower()
            if any(keyword in col_str for keyword in ['date', 'time', '日期', '时间']):
                date_cols.append(col)
            elif any(keyword in col_str for keyword in ['price', '价值', '价格', '收盘', 'close']):
                price_cols.append(col)
            elif any(keyword in col_str for keyword in ['volume', '交易量', '成交', 'vol']):
                volume_cols.append(col)

        # 如果基于列名没有检测到，尝试基于数据内容检测
        if not date_cols and not price_cols:
            print("未通过列名检测到明确的日期或价格列，尝试基于数据内容推断...")
            self._infer_columns_from_data()
            return  # 不再重复调用_ask_data_mapping

        # 报告检测结果
        if date_cols:
            self.column_mapping['date'] = date_cols[0]
            print(f"检测到日期列: {', '.join(map(str, date_cols))}")
        else:
            print("警告: 未检测到明确的日期列")

        if price_cols:
            self.column_mapping['price'] = price_cols[0]
            print(f"检测到价格列: {', '.join(map(str, price_cols))}")
        else:
            print("警告: 未检测到明确的价格列")

        if volume_cols:
            self.column_mapping['volume'] = volume_cols[0]
            print(f"检测到成交量列: {', '.join(map(str, volume_cols))}")
        else:
            print("提示: 未检测到成交量列，模型将仅基于价格数据进行分析")

        # 询问用户确认或修正自动检测的列映射
        self._ask_data_mapping()

    def _infer_columns_from_data(self):
        """
        基于数据内容推断列类型
        """
        if self.data is None or len(self.data) == 0:
            return

        columns = self.data.columns.tolist()
        date_candidates = []
        price_candidates = []

        # 检查前几行数据来推断列类型
        sample_size = min(5, len(self.data))
        for i, col in enumerate(columns):
            # 检查该列是否可能是日期
            is_date_candidate = True
            is_price_candidate = True

            for j in range(sample_size):
                val = self.data.iloc[j, i] if j < len(self.data) else None

                # 检查是否为日期
                if val is not None:
                    try:
                        pd.to_datetime(val)
                        # 如果能转换为日期，则很可能是日期列
                    except:
                        is_date_candidate = False

                # 检查是否为数值（价格）
                if val is not None:
                    try:
                        float(val)
                        # 如果能转换为浮点数，则很可能是价格列
                    except:
                        is_price_candidate = False

            if is_date_candidate:
                date_candidates.append((i, col))
            if is_price_candidate:
                price_candidates.append((i, col))

        # 输出推断结果
        if date_candidates:
            print(f"推断第{date_candidates[0][0] + 1}列为日期列: {date_candidates[0][1]}")
            # 自动设置日期列映射
            if not hasattr(self, 'column_mapping') or self.column_mapping is None:
                self.column_mapping = {}
            self.column_mapping['date'] = date_candidates[0][1]
        else:
            print("警告: 未能推断出明确的日期列")

        if price_candidates:
            print(f"推断第{price_candidates[0][0] + 1}列为价格列: {price_candidates[0][1]}")
            # 自动设置价格列映射
            if not hasattr(self, 'column_mapping') or self.column_mapping is None:
                self.column_mapping = {}
            self.column_mapping['price'] = price_candidates[0][1]
        else:
            print("警告: 未能推断出明确的价格列")

        print("提示: 未检测到成交量列，模型将仅基于价格数据进行分析")

    def _ask_data_mapping(self):
        """
        询问用户数据列映射
        """
        if self.data is None:
            return

        columns = self.data.columns.tolist()
        print("\n请指定各列的含义:")

        # 显示列信息
        print("可用的列:")
        for i, col in enumerate(columns):
            # 显示列名和前几个值
            sample_values = self.data[col].head(3).tolist()
            print(f"  {i + 1}. {col} (示例值: {sample_values})")

        # 询问每列的含义
        date_col_idx = input("请指定日期列编号 (直接回车跳过): ").strip()
        price_col_idx = input("请指定价格列编号 (直接回车跳过): ").strip()

        # 保存用户指定的列映射
        # 注意：这里不清空已有的column_mapping，而是在其基础上更新
        if not hasattr(self, 'column_mapping') or self.column_mapping is None:
            self.column_mapping = {}

        if date_col_idx.isdigit() and 1 <= int(date_col_idx) <= len(columns):
            self.column_mapping['date'] = columns[int(date_col_idx) - 1]
            print(f"已将列 '{columns[int(date_col_idx) - 1]}' 设置为日期列")

        if price_col_idx.isdigit() and 1 <= int(price_col_idx) <= len(columns):
            self.column_mapping['price'] = columns[int(price_col_idx) - 1]
            print(f"已将列 '{columns[int(price_col_idx) - 1]}' 设置为价格列")

    def _ask_data_frequency(self):
        """
        询问用户数据频率
        """
        print("\n请选择您的数据频率:")
        print("1. 日频数据 (默认)")
        print("2. 周频数据")
        print("3. 月频数据")
        print("4. 其他频率")

        choice = input("请输入选择 (1-4, 默认为1): ").strip()

        frequency_map = {
            "1": "daily",
            "2": "weekly",
            "3": "monthly",
            "4": "other"
        }

        self.data_frequency = frequency_map.get(choice, "daily")
        print(f"数据频率已设置为: {self.data_frequency}")

        # 根据数据频率给出参数建议
        if self.data_frequency == "weekly":
            print("提示: 对于周频数据，您可能需要调整时间相关的参数值")
        elif self.data_frequency == "monthly":
            print("提示: 对于月频数据，您可能需要显著调整时间相关的参数值")

    def lppl_equation(self, t, A, B, C, tc, m, omega, phi):
        """
        LPPL模型方程
        p(t) = A + B*(tc - t)^m + C*(tc - t)^m*cos(ω*ln(tc - t) + φ)

        参数:
        t : 时间序列
        A, B, C : 幅度参数
        tc : 临界时间(崩盘时间)
        m : 幂律指数
        ω : 对数周期频率
        φ : 相位参数
        """
        delta_t = tc - t
        # 防止出现负数或零的幂运算
        delta_t = np.where(delta_t > 0, delta_t, 1e-8)
        return A + B * (delta_t ** m) + C * (delta_t ** m) * np.cos(omega * np.log(delta_t) + phi)

    def fit_lppl_model(self, max_attempts=10):
        """
        拟合LPPL模型参数

        参数:
        max_attempts : 最大尝试次数
        """
        if self.data is None or 'price' not in self.column_mapping:
            print("缺少必要的价格数据，无法拟合LPPL模型")
            return None

        try:
            # 获取价格和时间数据
            prices = pd.to_numeric(self.data[self.column_mapping['price']], errors='coerce').dropna().values
            times = np.arange(len(prices))

            # 如果数据点太少，无法有效拟合
            if len(prices) < 10:
                print("数据点太少，无法有效拟合LPPL模型")
                return None

            # 使用非线性最小二乘法拟合参数
            from scipy.optimize import minimize

            # 定义目标函数（残差平方和）
            def objective(params):
                A, B, C, tc, m, omega, phi = params
                # 对参数施加约束
                if tc <= times[-1] or tc >= times[-1] + len(times):  # tc必须在未来但不能太远
                    return 1e10
                if m <= 0 or m >= 1:  # m应在(0, 1)范围内
                    return 1e10
                if omega <= 0 or omega >= 50:  # omega应在合理范围内
                    return 1e10

                try:
                    predicted = self.lppl_equation(times, A, B, C, tc, m, omega, phi)
                    residuals = prices - predicted
                    return np.sum(residuals ** 2)
                except:
                    return 1e10

            # 初始参数猜测
            A_guess = np.mean(prices)
            B_guess = (np.max(prices) - np.min(prices)) / 2
            C_guess = B_guess / 2
            tc_guess = len(times) * 1.2  # 预测在数据长度的1.2倍处
            m_guess = 0.5
            omega_guess = 10
            phi_guess = 0

            # 参数边界 - 修改B参数为正值，以确保价格上涨趋势
            bounds = [
                (np.min(prices) * 0.5, np.max(prices) * 2),  # A
                (0, np.abs(B_guess) * 2),  # B - 确保为正值，表示价格上涨趋势
                (-np.abs(C_guess) * 2, np.abs(C_guess) * 2),  # C
                (len(times), len(times) * 3),  # tc
                (0.1, 0.9),  # m
                (1, 30),  # omega
                (0, 2 * np.pi)  # phi
            ]

            best_result = None
            best_error = np.inf

            # 多次尝试不同的初始值以找到最佳拟合
            for attempt in range(max_attempts):
                # 添加一些随机扰动到初始猜测
                p0 = [
                    A_guess * np.random.uniform(0.9, 1.1),
                    B_guess * np.random.uniform(0.8, 1.2),
                    C_guess * np.random.uniform(0.8, 1.2),
                    tc_guess * np.random.uniform(0.9, 1.1),
                    m_guess * np.random.uniform(0.9, 1.1),
                    omega_guess * np.random.uniform(0.8, 1.2),
                    phi_guess + np.random.uniform(0, 2 * np.pi)
                ]

                # 确保初始参数在边界内
                for i in range(len(p0)):
                    p0[i] = max(bounds[i][0], min(bounds[i][1], p0[i]))

                try:
                    result = minimize(objective, p0, method='L-BFGS-B', bounds=bounds,
                                      options={'maxiter': 1000})

                    if result.success and result.fun < best_error:
                        best_result = result
                        best_error = result.fun

                except Exception as e:
                    continue

            if best_result is not None:
                A, B, C, tc, m, omega, phi = best_result.x
                self.lppl_params = {
                    'A': A, 'B': B, 'C': C,
                    'tc': tc, 'm': m,
                    'omega': omega, 'phi': phi
                }

                # 计算拟合结果
                fitted_prices = self.lppl_equation(times, A, B, C, tc, m, omega, phi)

                self.results['prices'] = prices
                self.results['fitted_prices'] = fitted_prices
                self.results['time'] = times
                self.results['residuals'] = prices - fitted_prices

                print(f"LPPL模型拟合完成!")
                print(f"预测临界时间(崩盘时间): {tc:.2f} (当前数据点: {len(times)})")
                print(f"参数 A: {A:.2f}, B: {B:.2f}, C: {C:.2f}")
                print(f"参数 m: {m:.2f}, ω: {omega:.2f}, φ: {phi:.2f}")

                return fitted_prices
            else:
                print("LPPL模型拟合失败，请检查数据质量")
                return None

        except Exception as e:
            print(f"拟合LPPL模型时发生错误: {str(e)}")
            return None

    def detect_cycles(self, window_size=None):
        """
        棺测价格序列中的多个周期性波动

        参数:
        window_size: 窗口大小，用于分段检测，默认为数据长度的1/3
        """
        if self.data is None or 'price' not in self.column_mapping:
            print("缺少必要的价格数据，无法检测周期")
            return None

        try:
            # 获取价格和时间数据
            prices = pd.to_numeric(self.data[self.column_mapping['price']], errors='coerce').dropna().values
            times = np.arange(len(prices))

            # 使用更智能的窗口划分方法
            windows = self._identify_significant_periods(prices, times, max_windows=5)

            # 存储多个LPPL模型的结果
            self.multi_lppl_params = []
            self.multi_fitted_prices = []

            # 对每个识别出的重要周期进行LPPL拟合
            for start, end in windows:
                if end - start >= 30:  # 确保窗口至少有30个数据点
                    # 提取窗口数据
                    window_prices = prices[start:end]
                    window_times = times[start:end]

                    # 对窗口数据拟合LPPL模型
                    window_params = self._fit_window_lppl(window_times, window_prices)

                    if window_params is not None:
                        self.multi_lppl_params.append({
                            'params': window_params,
                            'start_time': start,
                            'end_time': end
                        })

                        # 计算窗口内的拟合价格
                        fitted = self.lppl_equation(window_times, **window_params)
                        self.multi_fitted_prices.append({
                            'fitted_prices': fitted,
                            'start_time': start,
                            'end_time': end
                        })

            print(f"检测到 {len(self.multi_lppl_params)} 个潜在的泡沫周期")
            return len(self.multi_lppl_params)

        except Exception as e:
            print(f"检测周期时发生错误: {str(e)}")
            return None

    def _identify_significant_periods(self, prices, times, max_windows=5):
        """
        基于价格波动性和局部极值点识别重要周期

        参数:
        prices: 价格序列
        times: 时间序列
        max_windows: 最大窗口数量，默认为5

        返回:
        windows: 重要周期的时间窗口列表 [(start, end), ...]
        """
        if len(prices) < 30:
            return [(0, len(prices))]

        # 计算价格的移动平均和标准差
        window_size = min(30, len(prices) // 10)  # 动态窗口大小
        if window_size < 10:
            window_size = 10

        # 计算滚动波动率
        rolling_std = pd.Series(prices).rolling(window=window_size, center=True).std()
        rolling_mean = pd.Series(prices).rolling(window=window_size, center=True).mean()

        # 识别高波动区域
        high_volatility_threshold = np.nanpercentile(rolling_std, 70)
        high_volatility_regions = rolling_std > high_volatility_threshold

        # 识别局部极值点
        local_maxima = []
        local_minima = []

        for i in range(1, len(prices) - 1):
            if prices[i] > prices[i - 1] and prices[i] > prices[i + 1]:
                local_maxima.append(i)
            elif prices[i] < prices[i - 1] and prices[i] < prices[i + 1]:
                local_minima.append(i)

        # 合并相邻的高波动区域
        windows = []
        if np.any(high_volatility_regions):
            # 将连续的高波动区域合并为窗口
            in_high_volatility = False
            start = 0

            for i in range(len(high_volatility_regions)):
                if high_volatility_regions.iloc[i] and not in_high_volatility:
                    # 开始一个新的高波动区域
                    start = max(0, i - window_size // 2)
                    in_high_volatility = True
                elif not high_volatility_regions.iloc[i] and in_high_volatility:
                    # 结束当前高波动区域
                    end = min(len(prices), i + window_size // 2)
                    windows.append((start, end))
                    in_high_volatility = False

            # 处理最后一个区域
            if in_high_volatility:
                end = len(prices)
                windows.append((start, end))

        # 如果没有检测到高波动区域，使用局部极值点进行分割
        if not windows and (local_maxima or local_minima):
            significant_points = sorted(local_maxima + local_minima)
            if len(significant_points) > 1:
                # 至少需要两个显著点才能形成窗口
                avg_distance = np.mean(np.diff(significant_points))
                min_window_size = max(30, int(avg_distance * 0.5))

                # 创建窗口，确保窗口之间有一定重叠以捕获完整周期
                for i in range(len(significant_points) - 1):
                    start = max(0, significant_points[i] - min_window_size // 2)
                    end = min(len(prices), significant_points[i] + min_window_size // 2)
                    windows.append((start, end))

        # 如果仍然没有窗口，则使用滑动窗口方法
        if not windows:
            base_window_size = min(len(prices) // 3, 252)  # 最大一年的数据（假设日频）
            step_size = base_window_size // 2  # 50%重叠
            start = 0

            while start < len(prices):
                end = min(start + base_window_size, len(prices))
                windows.append((start, end))
                if end == len(prices):
                    break
                start += step_size

        # 移除过小的窗口并去重
        filtered_windows = []
        for start, end in windows:
            if end - start >= 30:  # 至少需要30个数据点
                # 检查是否与已有窗口重叠过多
                overlap = False
                for f_start, f_end in filtered_windows:
                    intersection = max(0, min(end, f_end) - max(start, f_start))
                    union = max(end, f_end) - min(start, f_start)
                    if union > 0 and intersection / union > 0.7:  # 重叠超过70%
                        overlap = True
                        break
                if not overlap:
                    filtered_windows.append((start, end))

        # 如果过滤后没有窗口，返回整个数据集
        if not filtered_windows:
            filtered_windows = [(0, len(prices))]

        return filtered_windows

    def _fit_window_lppl(self, times, prices):
        """
        在给定的时间和价格窗口内拟合LPPL模型

        参数:
        times: 时间序列
        prices: 价格序列
        """
        try:
            from scipy.optimize import minimize

            # 定义目标函数（残差平方和）
            def objective(params):
                A, B, C, tc, m, omega, phi = params
                # 对参数施加约束
                if tc <= times[-1] or tc >= times[-1] + len(times):  # tc必须在未来但不能太远
                    return 1e10
                if m <= 0 or m >= 1:  # m应在(0, 1)范围内
                    return 1e10
                if omega <= 0 or omega >= 50:  # omega应在合理范围内
                    return 1e10

                try:
                    predicted = self.lppl_equation(times, A, B, C, tc, m, omega, phi)
                    residuals = prices - predicted
                    return np.sum(residuals ** 2)
                except:
                    return 1e10

            # 初始参数猜测
            A_guess = np.mean(prices)
            B_guess = (np.max(prices) - np.min(prices)) / 2
            C_guess = B_guess / 2
            tc_guess = len(times) * 1.2  # 预测在数据长度的1.2倍处
            m_guess = 0.5
            omega_guess = 10
            phi_guess = 0

            # 参数边界 - 确保B为正值
            bounds = [
                (np.min(prices) * 0.5, np.max(prices) * 2),  # A
                (0, np.abs(B_guess) * 2),  # B - 确保为正值
                (-np.abs(C_guess) * 2, np.abs(C_guess) * 2),  # C
                (len(times), len(times) * 3),  # tc
                (0.1, 0.9),  # m
                (1, 30),  # omega
                (0, 2 * np.pi)  # phi
            ]

            best_result = None
            best_error = np.inf

            # 多次尝试不同的初始值以找到最佳拟合
            for attempt in range(5):  # 减少尝试次数以提高效率
                # 添加一些随机扰动到初始猜测
                p0 = [
                    A_guess * np.random.uniform(0.9, 1.1),
                    B_guess * np.random.uniform(0.8, 1.2),
                    C_guess * np.random.uniform(0.8, 1.2),
                    tc_guess * np.random.uniform(0.9, 1.1),
                    m_guess * np.random.uniform(0.9, 1.1),
                    omega_guess * np.random.uniform(0.8, 1.2),
                    phi_guess + np.random.uniform(0, 2 * np.pi)
                ]

                # 确保初始参数在边界内
                for i in range(len(p0)):
                    p0[i] = max(bounds[i][0], min(bounds[i][1], p0[i]))

                try:
                    result = minimize(objective, p0, method='L-BFGS-B', bounds=bounds,
                                      options={'maxiter': 500})

                    if result.success and result.fun < best_error:
                        best_result = result
                        best_error = result.fun

                except Exception as e:
                    continue

            if best_result is not None:
                A, B, C, tc, m, omega, phi = best_result.x
                
                # 验证拟合结果是否符合整体趋势
                # 计算拟合曲线的斜率
                fitted_values = self.lppl_equation(times, A, B, C, tc, m, omega, phi)
                if len(fitted_values) > 1:
                    # 计算拟合曲线的平均斜率
                    slope = np.mean(np.diff(fitted_values))
                    # 如果斜率为负且绝对值较大，可能不符合整体上涨趋势
                    if slope < -0.1 * np.mean(fitted_values):
                        print("警告: 拟合曲线斜率为负，可能不符合整体上涨趋势")
                        return None
                
                return {
                    'A': A, 'B': B, 'C': C,
                    'tc': tc, 'm': m,
                    'omega': omega, 'phi': phi
                }
            else:
                return None

        except Exception as e:
            return None

    def plot_results_with_multiple_peaks(self):
        """
        绘制包含多个波峰的图表
        """
        if 'prices' not in self.results:
            print("请先运行模型拟合或多波峰分析")
            return

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'LPPL模型多波峰分析结果 ({self.data_frequency}频率数据)', fontsize=16, fontweight='bold')

        # 获取价格数据
        prices = self.results['prices']
        times = self.results['time']

        # 计算价格范围，仅基于实际价格数据，增加10%的边距
        price_min, price_max = np.min(prices), np.max(prices)
        margin = (price_max - price_min) * 0.1
        y_min, y_max = price_min - margin, price_max + margin

        # 价格走势图和拟合曲线 (主图)
        axes[0, 0].plot(times, prices, 'b-', linewidth=1.5, label='实际价格', alpha=0.7)

        # 绘制多个窗口的LPPL拟合曲线，最多显示最新的5个周期
        if hasattr(self, 'multi_fitted_prices') and self.multi_fitted_prices:
            # 只显示最新的5个周期
            latest_cycles = self.multi_fitted_prices[-5:] if len(
                self.multi_fitted_prices) > 5 else self.multi_fitted_prices
            for i, fit_data in enumerate(latest_cycles):
                start = fit_data['start_time']
                end = fit_data['end_time']
                fitted = fit_data['fitted_prices']
                axes[0, 0].plot(times[start:end], fitted, '-', linewidth=2,
                                label=f'周期{len(self.multi_fitted_prices) - len(latest_cycles) + i + 1}拟合')
        else:
            # 如果没有多周期拟合结果，尝试绘制主拟合结果
            if 'fitted_prices' in self.results:
                axes[0, 0].plot(times, self.results['fitted_prices'], 'r--', linewidth=2, label='LPPL拟合')

        axes[0, 0].set_ylim(y_min, y_max)  # 设置Y轴范围仅基于实际价格数据
        axes[0, 0].legend(loc='upper left')
        axes[0, 0].set_title('资产价格走势和多周期拟合')
        axes[0, 0].set_xlabel('时间')
        axes[0, 0].set_ylabel('价格')
        axes[0, 0].grid(True, alpha=0.3)

        # 绘制多个周期的临界时间点，最多显示最新的5个周期
        if hasattr(self, 'multi_lppl_params') and self.multi_lppl_params:
            # 只处理最新的5个周期
            latest_params = self.multi_lppl_params[-5:] if len(self.multi_lppl_params) > 5 else self.multi_lppl_params
            for i, param_data in enumerate(latest_params):
                params = param_data['params']
                tc = params['tc']
                start_time = param_data['start_time']
                end_time = param_data['end_time']
                actual_tc = start_time + tc  # 转换为全局时间

                # 只显示未来的临界时间点
                if actual_tc > end_time:
                    axes[0, 0].axvline(x=actual_tc, color=plt.cm.Set1(i), linestyle='--',
                                       linewidth=1.5, alpha=0.8)
                    axes[0, 0].scatter(actual_tc, y_max - (i + 1) * (y_max - y_min) * 0.05,
                                       color=plt.cm.Set1(i), marker='v', s=100)
                    axes[0, 0].text(actual_tc, y_max - (i + 1) * (y_max - y_min) * 0.08,
                                    f'周期{len(self.multi_lppl_params) - len(latest_params) + i + 1}\n预测:{actual_tc:.0f}',
                                    color=plt.cm.Set1(i), fontsize=9, ha='center', va='top',
                                    bbox=dict(boxstyle="round,pad=0.3", facecolor=plt.cm.Set1(i), alpha=0.2))

        # 收益率图
        if len(prices) > 1:
            returns = np.diff(prices) / prices[:-1]
            axes[0, 1].plot(range(1, len(returns) + 1), returns, 'g-', linewidth=1, alpha=0.7)
            axes[0, 1].set_title('收益率')
            axes[0, 1].set_xlabel('时间')
            axes[0, 1].set_ylabel('收益率')
            axes[0, 1].grid(True, alpha=0.3)
            # 添加均值线
            axes[0, 1].axhline(y=np.mean(returns), color='r', linestyle='--', alpha=0.7,
                               label=f'平均收益率: {np.mean(returns) * 100:.2f}%')
            axes[0, 1].legend()

        # 回撤
        if len(prices) > 1:
            peak = np.maximum.accumulate(prices)
            drawdown = (prices - peak) / peak
            axes[1, 0].fill_between(times, drawdown * 100, 0, alpha=0.3, color='red')
            axes[1, 0].plot(times, drawdown * 100, 'r-', linewidth=1.5)
            axes[1, 0].set_title('回撤 (%)')
            axes[1, 0].set_xlabel('时间')
            axes[1, 0].set_ylabel('回撤 (%)')
            axes[1, 0].grid(True, alpha=0.3)
            axes[1, 0].axhline(y=np.min(drawdown) * 100, color='darkred', linestyle=':',
                               label=f'最大回撤: {np.min(drawdown) * 100:.2f}%')
            axes[1, 0].legend()

        # 价格分布直方图
        n, bins, patches = axes[1, 1].hist(prices, bins=50, alpha=0.7, color='purple', edgecolor='black', linewidth=0.5)
        axes[1, 1].set_title('价格分布')
        axes[1, 1].set_xlabel('价格')
        axes[1, 1].set_ylabel('频次')
        axes[1, 1].grid(True, alpha=0.3)

        # 标注平均价格
        mean_price = np.mean(prices)
        axes[1, 1].axvline(mean_price, color='red', linestyle='--',
                           label=f'平均价格: {mean_price:.2f}')
        axes[1, 1].legend()

        plt.tight_layout()
        plt.show()

    def plot_individual_cycles(self):
        """
        绘制单独的周期图表，仅显示最新的5个周期
        """
        if 'prices' not in self.results:
            print("请先运行模型拟合或多波峰分析")
            return

        if not hasattr(self, 'multi_lppl_params') or not self.multi_lppl_params:
            print("没有多周期拟合结果")
            return

        # 只处理最新的5个周期
        latest_params = self.multi_lppl_params[-5:] if len(self.multi_lppl_params) > 5 else self.multi_lppl_params
        prices = self.results['prices']
        times = self.results['time']

        # 确定显示范围：从最老的那个周期（即最新的5个周期中最开始的那个）开始显示
        start_time_display = min([param['start_time'] for param in latest_params])
        
        # 裁剪数据到显示范围
        display_times = times[start_time_display:]
        display_prices = prices[start_time_display:]

        # 创建新的图表，只显示实际价格和各周期的拟合曲线
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # 绘制实际价格（仅显示需要的范围）
        ax.plot(display_times, display_prices, 'b-', linewidth=1.5, label='实际价格', alpha=0.7)

        # 绘制每个周期的拟合曲线
        for i, param_data in enumerate(latest_params):
            start_time = param_data['start_time']
            end_time = param_data['end_time']
            
            # 提取该周期内的数据
            cycle_times = times[start_time:end_time]
            cycle_prices = prices[start_time:end_time]
            cycle_length = len(cycle_times)
            
            # 使用该周期的参数生成拟合曲线
            params = param_data['params']
            
            # 创建时间序列用于LPPL方程计算，从0开始到周期长度
            # tc是相对于窗口开始的临界时间点，所以对于窗口内的每个点t，我们计算的是t相对于窗口开始的时间
            relative_times = np.arange(cycle_length)
            
            # 使用LPPL方程计算拟合值
            # 这里tc是拟合时使用的临界时间（相对于窗口开始），relative_times是当前时间点（相对于窗口开始）
            fitted_values = self.lppl_equation(relative_times, 
                                             params['A'], params['B'], params['C'], 
                                             params['tc'], params['m'], params['omega'], params['phi'])
            
            # 在图上绘制拟合曲线，确保只在对应的时间范围内显示
            ax.plot(cycle_times, fitted_values, '-', linewidth=2, 
                   label=f'周期{len(self.multi_lppl_params) - len(latest_params) + i + 1}拟合',
                   alpha=0.8)

        # 设置Y轴范围基于实际价格数据，避免异常值
        price_min, price_max = np.min(display_prices), np.max(display_prices)
        margin = (price_max - price_min) * 0.1
        ax.set_ylim(price_min - margin, price_max + margin)

        ax.set_title(f'LPPL模型 - 最新5个周期分析 ({self.data_frequency}频率数据)', fontsize=14, fontweight='bold')
        ax.set_xlabel('时间')
        ax.set_ylabel('价格')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def predict_critical_time(self):
        """        预测临界时间(崩盘时间)
        """
        if self.lppl_params is None:
            print("模型尚未拟合，请先拟合LPPL模型")
            return None

        tc = self.lppl_params['tc']
        # 计算距离当前数据点的时间差
        current_time = len(self.results['prices'])
        time_diff = tc - current_time

        # 根据时间差给出不同的解释
        if time_diff < 0:
            print(f"警告: 预测的临界时间({tc:.2f})已经过去，当前数据点:{current_time}")
            print(f"这表明市场可能已经经历了崩盘，或模型拟合存在问题")
        elif time_diff == 0:
            print(f"预测的临界时间({tc:.2f})正好在当前数据点，市场处于临界状态")
        else:
            print(f"预测临界时间(泡沫结束时间): {tc:.2f} (当前数据点: {current_time})")
            print(f"距离预测崩盘还有 {time_diff:.2f} 个时间单位")

        # 显示多个周期的临界时间，最多显示最新的5个
        if hasattr(self, 'multi_lppl_params') and self.multi_lppl_params:
            latest_params = self.multi_lppl_params[-5:] if len(self.multi_lppl_params) > 5 else self.multi_lppl_params
            print("\n检测到的多个周期临界时间 (显示最新的5个):")
            for i, param_data in enumerate(latest_params):
                params = param_data['params']
                cycle_tc = params['tc']
                start_time = param_data['start_time']
                actual_tc = start_time + cycle_tc
                print(
                    f"  周期 {len(self.multi_lppl_params) - len(latest_params) + i + 1}: {actual_tc:.2f} (窗口内时间: {cycle_tc:.2f})")

        return tc

    def calculate_confidence_indicator(self):
        """
        计算泡沫信心指数
        """
        if self.lppl_params is None or 'prices' not in self.results:
            print("模型尚未拟合或缺少价格数据")
            return None

        # 泡沫信心指数基于参数B和C的比值
        B = self.lppl_params['B']
        C = self.lppl_params['C']

        # 确保分母不为零
        if abs(B) < 1e-10:
            confidence = 0
        else:
            confidence = abs(C / B)

        # 将信心指数归一化到0-100范围
        confidence = min(100, confidence * 100)

        print(f"泡沫信心指数: {confidence:.2f}")

        # 根据信心指数给出解释
        if confidence < 20:
            print("泡沫风险较低，市场相对稳定")
        elif confidence < 50:
            print("存在泡沫迹象，需密切关注市场动态")
        elif confidence < 80:
            print("泡沫风险较高，市场处于不稳定状态")
        else:
            print("泡沫风险极高，市场可能即将崩溃")

        return confidence

    def analyze_real_data(self):
        """
        分析实际加载的数据（使用LPPL模型拟合）
        """
        print("使用LPPL模型分析实际数据...")
        # 首先进行标准LPPL拟合
        result = self.fit_lppl_model()

        # 然后检测多个周期
        print("检测多个周期性波动...")
        self.detect_cycles()

        return result

    def analyze_multiple_peaks(self):
        """
        专门分析多个波峰的函数
        """
        if self.data is None or 'price' not in self.column_mapping:
            print("缺少必要的价格数据")
            return None

        try:
            # 获取价格和时间数据
            prices = pd.to_numeric(self.data[self.column_mapping['price']], errors='coerce').dropna().values
            times = np.arange(len(prices))

            # 保存结果到results中以便绘图使用
            self.results['prices'] = prices
            self.results['time'] = times

            print(f"分析数据集，共 {len(prices)} 个数据点")

            # 检测多个周期
            num_cycles = self.detect_cycles()

            if num_cycles is None or num_cycles == 0:
                print("未检测到明显的周期性波动")
                return None

            print(f"\n=== 多波峰分析结果 ===")
            print(f"总共检测到 {num_cycles} 个显著的泡沫周期")

            # 只分析最新的5个周期
            latest_params = self.multi_lppl_params[-5:] if len(self.multi_lppl_params) > 5 else self.multi_lppl_params

            peak_times = []
            peak_values = []
            crash_times = []

            for i, param_data in enumerate(latest_params):
                params = param_data['params']
                cycle_tc = params['tc']
                start_time = param_data['start_time']
                end_time = param_data['end_time']
                actual_tc = start_time + cycle_tc

                # 获取该周期内的最高价格点
                cycle_prices = prices[start_time:end_time]
                cycle_times = times[start_time:end_time]
                max_price_idx = np.argmax(cycle_prices)
                peak_time = cycle_times[max_price_idx]
                peak_value = cycle_prices[max_price_idx]

                peak_times.append(peak_time)
                peak_values.append(peak_value)
                crash_times.append(actual_tc)

                # 输出周期信息
                cycle_index = len(self.multi_lppl_params) - len(latest_params) + i + 1
                print(f"\n周期 {cycle_index}:")
                print(f"  时间窗口: {start_time} - {end_time}")
                print(f"  周期内峰值时间: {peak_time}")
                print(f"  周期内峰值价格: {peak_value:.2f}")
                print(f"  预测崩盘时间: {actual_tc:.2f}")
                if actual_tc > end_time:
                    print(f"  距离预测崩盘: {actual_tc - end_time:.2f} 时间单位")
                else:
                    print(f"  崩盘时间已过: {end_time - actual_tc:.2f} 时间单位")

            # 总结信息
            print(f"\n=== 泡沫周期总结 (最新的5个) ===")
            for i, (peak_time, peak_value) in enumerate(zip(peak_times, peak_values)):
                cycle_index = len(self.multi_lppl_params) - len(latest_params) + i + 1
                print(f"波峰 {cycle_index}: 时间={peak_time}, 价格={peak_value:.2f}")

            return {
                'peak_times': peak_times,
                'peak_values': peak_values,
                'crash_times': crash_times,
                'num_cycles': num_cycles
            }

        except Exception as e:
            print(f"分析多波峰时发生错误: {str(e)}")
            return None

    def calculate_economic_impact(self):
        """
        计算经济影响指标
        """
        if 'prices' not in self.results:
            print("请先运行模拟或分析实际数据")
            return

        prices = self.results['prices']

        # 计算收益率
        if 'returns' not in self.results:
            returns = np.diff(prices) / prices[:-1]
        else:
            returns = self.results['returns']

        # 计算最大回撤
        if 'drawdown' not in self.results:
            peak = np.maximum.accumulate(prices)
            drawdown = (prices - peak) / peak
        else:
            drawdown = self.results['drawdown']

        # 计算波动率
        volatility = np.std(returns) * np.sqrt(252)  # 年化波动率假设每日数据

        # 根据数据频率调整年化波动率计算
        if self.data_frequency == "weekly":
            volatility = np.std(returns) * np.sqrt(52)  # 周频数据年化
        elif self.data_frequency == "monthly":
            volatility = np.std(returns) * np.sqrt(12)  # 月频数据年化

        # 计算VaR (Value at Risk)
        if len(returns) > 1:
            var_95 = np.percentile(returns, 5)
        else:
            var_95 = 0

        # 保存结果
        self.results['returns'] = returns
        self.results['drawdown'] = drawdown
        self.results['volatility'] = volatility
        self.results['var_95'] = var_95

        print("\n经济影响分析结果:")
        print(f"  最大回撤: {np.min(drawdown) * 100:.2f}%")
        print(f"  波动率 ({self.data_frequency}频率): {volatility * 100:.2f}%")
        print(f"  95% VaR: {var_95 * 100:.2f}%")

        return {
            'max_drawdown': np.min(drawdown),
            'volatility': volatility,
            'var_95': var_95
        }

    def save_results(self, filename='lppl_model_results.xlsx'):
        """
        保存结果到Excel文件

        参数:
        filename (str): 输出文件名
        """
        if 'prices' not in self.results:
            print("没有可保存的结果")
            return



        # 创建结果DataFrame
        results_df = pd.DataFrame({
            '时间': self.results['time'],
            '价格': self.results['prices']
        })

        if 'returns' in self.results:
            results_df['收益率'] = np.concatenate([[0], self.results['returns']])

        if 'drawdown' in self.results:
            results_df['回撤(%)'] = np.concatenate([self.results['drawdown']]) * 100

        # 保存到Excel
        try:
            results_df.to_excel(filename, index=False)
            print(f"结果已保存到 {filename}")
        except Exception as e:
            print(f"保存结果时发生错误: {str(e)}")


def print_data_structure():
    """
    打印Excel数据结构说明
    """
    print("\n" + "=" * 50)
    print("Excel数据文件结构说明")
    print("=" * 50)
    print("模型支持多种类型和频率的数据输入:")
    print("\n1. 时间序列数据:")
    print("   - 必需列: 日期, 资产价格")
    print("   - 可选列: 交易量")
    print("   - 日期格式: YYYY-MM-DD")
    print("   - 资产价格: 数值型")
    print("   - 交易量: 数值型(可选)")
    print("\n2. 支持的数据频率:")
    print("   - 日频数据 (如: 2020-01-01, 2020-01-02, ...)")
    print("   - 周频数据 (如: 2020-01-01, 2020-01-08, ...)")
    print("   - 月频数据 (如: 2020-01-01, 2020-02-01, ...)")
    print("   - 季频数据 (如: 2020-01-01, 2020-04-01, ...)")
    print("   - 年频数据 (如: 2020-01-01, 2021-01-01, ...)")
    print("\n3. 多资产数据:")
    print("   - 必需列: 资产名称, 日期, 价格")
    print("   - 可选列: 其他指标...")
    print("   - 每行代表一个资产在特定时间点的数据")
    print("\n注意:")
    print("   - 第一行为列标题")
    print("   - 数据从第二行开始")
    print("   - 支持.xls和.xlsx格式")
    print("   - 成交量是可选的，不影响模型基本功能")
    print("   - 不同频率数据需要相应调整模型参数")
    print("=" * 50)


def main():
    """
    主函数
    """
    print("=" * 50)
    print("对数周期幂律模型 (LPPL Model)")
    print("=" * 50)

    # 显示数据结构说明
    print_data_structure()

    # 创建模型实例
    model = LPPLModel()

    # 直接使用弹窗选择文件
    print("\n请在弹窗中选择Excel数据文件（可选）:")
    data_loaded = model.load_data_with_dialog()

    # 根据是否有数据选择分析方式
    if data_loaded and model.data is not None:
        print("\n检测到实际数据，开始使用LPPL模型进行分析...")

        # 使用专门的多波峰分析方法
        result = model.analyze_multiple_peaks()

        if result is not None:
            # 绘制结果
            show_plot = input("\n是否显示结果图表? (y/n, 默认y): ").strip().lower()
            if show_plot != 'n':  # 默认为y，用户按回车直接显示
                # 根据项目规范，当存在多个周期结果时，默认开启单独周期图表的显示功能
                print("根据项目规范，将默认显示单独周期图表，确保每个周期的拟合结果在独立图表中展示")
                model.plot_individual_cycles()

            # 保存结果
            save_choice = input("\n是否保存结果到Excel文件? (y/n, 默认n): ").strip().lower()
            if save_choice == 'y':  # 默认为n，用户需要明确选择y才会保存
                save_file = input("请输入保存结果的Excel文件名 (直接回车使用默认名称): ").strip()
                if not save_file:
                    save_file = 'lppl_model_results.xlsx'
                if not save_file.endswith('.xlsx'):
                    save_file += '.xlsx'
                model.save_results(save_file)
    else:
        print("\nLPPL模型需要实际数据进行分析，请提供有效的价格数据文件")
        return

    print("\n程序运行完成!")


if __name__ == "__main__":
    main()