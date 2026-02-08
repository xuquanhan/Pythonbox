#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化对数周期幂律(LPPL)模型
基于Sornette教授的理论，用于检测金融市场中的泡沫并预测可能的崩盘时间
包含算法优化、特征指标提取和泡沫状态分类功能
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
import os
from scipy.optimize import minimize, differential_evolution
from scipy.stats import chi2
from sklearn.metrics import r2_score
from typing import Dict, Tuple, Optional, List

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


class OptimizedLPPLModel:
    """
    优化的对数周期幂律(LPPL)模型类
    基于Sornette教授的理论，用于检测金融市场中的泡沫并预测可能的崩盘时间
    包含算法优化、特征指标提取和泡沫状态分类功能
    """

    def __init__(self):
        self.data = None
        self.parameters = {}
        self.results = {}
        self.data_frequency = "daily"  # 默认为日频数据
        self.column_mapping = {}  # 列映射信息
        self.lppl_params = None  # LPPL模型参数
        self.fitted_models = []  # 存储多个拟合模型
        
        # 优化参数
        self.optimization_method = 'differential_evolution'  # 默认使用差分进化算法
        self.max_iterations = 1000
        self.population_size = 50

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

    def _calculate_jacobian(self, t, A, B, C, tc, m, omega, phi):
        """
        计算LPPL模型的雅可比矩阵（梯度）
        用于优化算法的梯度计算
        """
        dt = tc - t
        dt = np.where(dt > 0, dt, 1e-8)
        log_dt = np.log(dt)
        
        # 计算各个参数的偏导数
        dA = np.ones_like(t)
        dB = dt ** m
        dC = dt ** m * np.cos(omega * log_dt + phi)
        dphi = -C * dt ** m * np.sin(omega * log_dt + phi)
        domega = -C * dt ** m * log_dt * np.sin(omega * log_dt + phi)
        
        # 更复杂的偏导数计算（tc和m）
        d_tc = B * m * dt ** (m - 1) + \
               C * m * dt ** (m - 1) * np.cos(omega * log_dt + phi) - \
               C * dt ** (m - 1) * np.sin(omega * log_dt + phi) * omega
               
        dm = B * (dt ** m) * log_dt + \
             C * (dt ** m) * log_dt * np.cos(omega * log_dt + phi)
        
        return np.array([dA, dB, dC, d_tc, dm, domega, dphi]).T

    def _objective_function(self, params, times, prices):
        """
        目标函数（残差平方和）
        """
        A, B, C, tc, m, omega, phi = params
        
        # 对参数施加约束
        if tc <= times[-1] or tc >= times[-1] + len(times) * 2:  # tc必须在未来但不能太远
            return 1e10
        if m <= 0 or m >= 1:  # m应在(0, 1)范围内
            return 1e10
        if omega <= 0 or omega >= 50:  # omega应在合理范围内
            return 1e10
        if abs(B) < 0.001:  # B应为正值（表示趋势）
            return 1e10

        try:
            predicted = self.lppl_equation(times, A, B, C, tc, m, omega, phi)
            residuals = prices - predicted
            return np.sum(residuals ** 2)
        except:
            return 1e10

    def _robust_initial_guess(self, times, prices):
        """
        基于数据特征生成稳健的初始参数估计
        """
        A_guess = np.mean(prices)
        B_guess = (np.max(prices) - np.min(prices)) / 2
        C_guess = B_guess / 4  # C通常比B小
        tc_guess = len(times) * 1.2  # 预测在数据长度的1.2倍处
        m_guess = 0.5
        omega_guess = 5  # 初始频率较小
        phi_guess = 0

        return [A_guess, B_guess, C_guess, tc_guess, m_guess, omega_guess, phi_guess]

    def fit_lppl_model(self, max_attempts=10, use_differential_evolution=True):
        """
        优化的LPPL模型参数拟合

        参数:
        max_attempts : 最大尝试次数
        use_differential_evolution : 是否使用差分进化算法
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

            # 生成初始参数猜测
            initial_params = self._robust_initial_guess(times, prices)

            # 参数边界
            bounds = [
                (np.min(prices) * 0.5, np.max(prices) * 2),  # A
                (0, np.abs(initial_params[1]) * 3),  # B - 确保为正值
                (-np.abs(initial_params[2]) * 2, np.abs(initial_params[2]) * 2),  # C
                (len(times), len(times) * 3),  # tc
                (0.1, 0.9),  # m
                (0.5, 20),  # omega
                (0, 2 * np.pi)  # phi
            ]

            best_result = None
            best_error = np.inf

            if use_differential_evolution:
                # 使用差分进化算法
                try:
                    de_result = differential_evolution(
                        lambda p: self._objective_function(p, times, prices),
                        bounds,
                        seed=42,
                        maxiter=1000,
                        popsize=15,
                        disp=False
                    )
                    if de_result.success and de_result.fun < best_error:
                        best_result = de_result
                        best_error = de_result.fun
                except Exception as e:
                    print(f"差分进化算法失败: {e}")

            # 多次尝试不同的初始值以找到最佳拟合
            for attempt in range(max_attempts):
                # 添加一些随机扰动到初始猜测
                p0 = [
                    initial_params[0] * np.random.uniform(0.9, 1.1),
                    initial_params[1] * np.random.uniform(0.8, 1.2),
                    initial_params[2] * np.random.uniform(0.8, 1.2),
                    initial_params[3] * np.random.uniform(0.9, 1.1),
                    initial_params[4] * np.random.uniform(0.9, 1.1),
                    initial_params[5] * np.random.uniform(0.8, 1.2),
                    initial_params[6] + np.random.uniform(-0.5, 0.5)
                ]

                # 确保初始参数在边界内
                for i in range(len(p0)):
                    p0[i] = max(bounds[i][0], min(bounds[i][1], p0[i]))

                try:
                    result = minimize(
                        lambda p: self._objective_function(p, times, prices),
                        p0,
                        method='L-BFGS-B',
                        bounds=bounds,
                        options={'maxiter': 1000}
                    )

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

                # 计算模型评估指标
                r_squared = r2_score(prices, fitted_prices)
                mse = np.mean((prices - fitted_prices) ** 2)
                
                self.results['r_squared'] = r_squared
                self.results['mse'] = mse

                print(f"LPPL模型拟合完成!")
                print(f"预测临界时间(崩盘时间): {tc:.2f} (当前数据点: {len(times)})")
                print(f"参数 A: {A:.2f}, B: {B:.2f}, C: {C:.2f}")
                print(f"参数 m: {m:.2f}, ω: {omega:.2f}, φ: {phi:.2f}")
                print(f"拟合优度 R²: {r_squared:.4f}, MSE: {mse:.4f}")

                # 添加到拟合模型列表
                model_info = {
                    'params': self.lppl_params.copy(),
                    'fitted_prices': fitted_prices,
                    'times': times,
                    'r_squared': r_squared,
                    'mse': mse,
                    'start_time': 0,
                    'end_time': len(times)
                }
                self.fitted_models.append(model_info)

                return fitted_prices
            else:
                print("LPPL模型拟合失败，请检查数据质量")
                return None

        except Exception as e:
            print(f"拟合LPPL模型时发生错误: {str(e)}")
            return None

    def detect_bubble_regime(self):
        """
        检测泡沫状态类别
        识别传统上涨泡沫、负泡沫（下跌趋势）、反转泡沫和反转负泡沫
        """
        if self.lppl_params is None:
            print("模型尚未拟合，无法检测泡沫状态")
            return None

        # 获取参数
        B = self.lppl_params['B']
        m = self.lppl_params['m']
        omega = self.lppl_params['omega']
        C = self.lppl_params['C']

        # 判断泡沫类型
        bubble_type = ""
        if B > 0 and C > 0:
            bubble_type = "传统上涨泡沫"
        elif B > 0 and C < 0:
            bubble_type = "反转泡沫"
        elif B < 0 and C > 0:
            bubble_type = "负泡沫（下跌趋势）"
        elif B < 0 and C < 0:
            bubble_type = "反转负泡沫"
        else:
            bubble_type = "无明显泡沫特征"

        # 计算泡沫强度
        bubble_strength = abs(B) * abs(C) / (abs(B) + abs(C) + 1e-10)  # 避免除零

        print(f"检测到的泡沫类型: {bubble_type}")
        print(f"泡沫强度指标: {bubble_strength:.4f}")
        print(f"B参数: {B:.4f}, C参数: {C:.4f}")
        print(f"幂律指数m: {m:.4f}, 频率ω: {omega:.4f}")

        return {
            'type': bubble_type,
            'strength': bubble_strength,
            'B': B,
            'C': C,
            'm': m,
            'omega': omega
        }

    def calculate_feature_indices(self):
        """
        计算特征指标
        1. 概率残差指数：衡量价格偏离理想LPPL状态的程度
        2. 临界时间指数 (T)：预测泡沫可能破裂的时间上限
        3. 趋势发展频率指数 (ω)：反映泡沫演化的振荡频率
        """
        if 'residuals' not in self.results or self.lppl_params is None:
            print("模型尚未拟合，无法计算特征指标")
            return None

        residuals = self.results['residuals']
        fitted_prices = self.results['fitted_prices']
        prices = self.results['prices']

        # 1. 概率残差指数：标准化残差的累积平方和
        residual_sum_sq = np.sum(residuals ** 2)
        price_var = np.var(prices)
        prob_residual_index = residual_sum_sq / (len(residuals) * price_var + 1e-10) if price_var > 0 else residual_sum_sq / len(residuals)

        # 2. 临界时间指数 (T)：预测的临界时间与当前时间的距离
        tc = self.lppl_params['tc']
        current_time = len(prices)
        critical_time_index = tc - current_time

        # 3. 趋势发展频率指数 (ω)：从参数直接获取
        trend_freq_index = self.lppl_params['omega']

        # 4. 额外指标：泡沫破裂概率（基于剩余时间和参数稳定性）
        remaining_time_ratio = critical_time_index / (tc + 1e-10)
        bubble_crash_prob = max(0, min(1, 1 - remaining_time_ratio)) if remaining_time_ratio > 0 else 1

        print(f"特征指标计算结果:")
        print(f"  概率残差指数: {prob_residual_index:.4f} (越小越好)")
        print(f"  临界时间指数: {critical_time_index:.2f} (正值表示未来时间)")
        print(f"  趋势发展频率指数: {trend_freq_index:.4f}")
        print(f"  泡沫破裂概率: {bubble_crash_prob:.4f}")

        feature_indices = {
            'prob_residual_index': prob_residual_index,
            'critical_time_index': critical_time_index,
            'trend_freq_index': trend_freq_index,
            'bubble_crash_prob': bubble_crash_prob,
            'r_squared': self.results.get('r_squared', 0),
            'mse': self.results.get('mse', float('inf'))
        }

        return feature_indices

    def detect_bubble_phase(self):
        """
        检测泡沫发展阶段
        根据指标的动态特征判断泡沫所处的发展阶段、成熟阶段和破裂阶段
        """
        if 'residuals' not in self.results or self.lppl_params is None:
            print("模型尚未拟合，无法检测泡沫阶段")
            return None

        # 获取特征指标
        indices = self.calculate_feature_indices()
        if indices is None:
            return None

        # 分析参数稳定性
        prob_residual_index = indices['prob_residual_index']
        critical_time_index = indices['critical_time_index']
        trend_freq_index = indices['trend_freq_index']
        bubble_crash_prob = indices['bubble_crash_prob']

        # 根据指标判断阶段
        phase = ""
        if prob_residual_index < 0.1 and critical_time_index > 10:
            phase = "发展阶段 - 泡沫正在形成，拟合良好"
        elif 0.1 <= prob_residual_index <= 0.3 and 5 < critical_time_index <= 10:
            phase = "成熟阶段 - 泡沫接近临界点，振荡增加"
        elif prob_residual_index > 0.3 or critical_time_index <= 5:
            phase = "破裂阶段 - 泡沫即将或已经破裂"
        elif bubble_crash_prob > 0.8:
            phase = "破裂预警阶段 - 高破裂概率"
        else:
            phase = "稳定阶段 - 无明显泡沫特征"

        print(f"当前泡沫阶段: {phase}")
        print(f"阶段判断依据:")
        print(f"  拟合质量: {'优秀' if prob_residual_index < 0.1 else '良好' if prob_residual_index < 0.3 else '较差'}")
        print(f"  剩余时间: {'充足' if critical_time_index > 10 else '紧张' if critical_time_index > 0 else '超时'}")
        print(f"  破裂概率: {'高' if bubble_crash_prob > 0.7 else '中' if bubble_crash_prob > 0.3 else '低'}")

        return phase

    def timing_strategy_signals(self):
        """
        基于模型信号构建择时策略
        """
        if self.lppl_params is None:
            print("模型尚未拟合，无法生成择时信号")
            return None

        # 获取特征指标
        indices = self.calculate_feature_indices()
        if indices is None:
            return None

        signals = []

        # 买入信号条件
        if (indices['prob_residual_index'] < 0.2 and 
            indices['critical_time_index'] > 10 and 
            self.lppl_params['B'] > 0):
            signals.append("买入信号：泡沫正在形成，趋势向上")
        elif (indices['prob_residual_index'] < 0.15 and 
              5 < indices['critical_time_index'] <= 10 and 
              self.lppl_params['B'] > 0):
            signals.append("持有信号：泡沫成熟，继续观察")

        # 卖出信号条件
        if indices['bubble_crash_prob'] > 0.8:
            signals.append("卖出信号：高破裂概率")
        elif indices['critical_time_index'] <= 0:
            signals.append("卖出信号：已超过预测破裂时间")
        elif indices['prob_residual_index'] > 0.4:
            signals.append("卖出信号：拟合质量差")

        print("择时策略信号:")
        if signals:
            for signal in signals:
                print(f"  {signal}")
        else:
            print("  无明确交易信号")

        return signals

    def plot_results(self):
        """
        绘制结果图表
        """
        if 'prices' not in self.results:
            print("请先运行模型拟合")
            return

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'优化LPPL模型分析结果 ({self.data_frequency}频率数据)', fontsize=16, fontweight='bold')

        # 获取价格数据
        prices = self.results['prices']
        times = self.results['time']
        fitted_prices = self.results.get('fitted_prices', [])

        # 计算价格范围，仅基于实际价格数据，增加10%的边距
        price_min, price_max = np.min(prices), np.max(prices)
        margin = (price_max - price_min) * 0.1
        y_min, y_max = price_min - margin, price_max + margin

        # 价格走势图和拟合曲线 (主图)
        axes[0, 0].plot(times, prices, 'b-', linewidth=1.5, label='实际价格', alpha=0.7)
        if len(fitted_prices) > 0:
            axes[0, 0].plot(times, fitted_prices, 'r--', linewidth=2, label='LPPL拟合', alpha=0.8)

        # 标记临界时间
        if self.lppl_params:
            tc = self.lppl_params['tc']
            current_time = len(times)
            if tc > current_time:
                axes[0, 0].axvline(x=tc, color='red', linestyle='--', linewidth=1.5, alpha=0.8)
                axes[0, 0].scatter(tc, y_max - 0.05 * (y_max - y_min), color='red', marker='v', s=100)
                axes[0, 0].text(tc, y_max - 0.08 * (y_max - y_min), f'预测破裂\n时间: {tc:.0f}', 
                                color='red', fontsize=9, ha='center', va='top',
                                bbox=dict(boxstyle="round,pad=0.3", facecolor='red', alpha=0.2))

        axes[0, 0].set_ylim(y_min, y_max)
        axes[0, 0].legend(loc='upper left')
        axes[0, 0].set_title('资产价格走势和LPPL拟合')
        axes[0, 0].set_xlabel('时间')
        axes[0, 0].set_ylabel('价格')
        axes[0, 0].grid(True, alpha=0.3)

        # 残差图
        if 'residuals' in self.results:
            residuals = self.results['residuals']
            axes[0, 1].plot(times, residuals, 'g-', linewidth=1, alpha=0.7)
            axes[0, 1].set_title('拟合残差')
            axes[0, 1].set_xlabel('时间')
            axes[0, 1].set_ylabel('残差')
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].axhline(y=0, color='red', linestyle='--', alpha=0.7)

        # 收益率图
        if len(prices) > 1:
            returns = np.diff(prices) / prices[:-1]
            axes[1, 0].plot(range(1, len(returns) + 1), returns, 'g-', linewidth=1, alpha=0.7)
            axes[1, 0].set_title('收益率')
            axes[1, 0].set_xlabel('时间')
            axes[1, 0].set_ylabel('收益率')
            axes[1, 0].grid(True, alpha=0.3)
            # 添加均值线
            axes[1, 0].axhline(y=np.mean(returns), color='r', linestyle='--', alpha=0.7,
                               label=f'平均收益率: {np.mean(returns) * 100:.2f}%')
            axes[1, 0].legend()

        # 回撤
        if len(prices) > 1:
            peak = np.maximum.accumulate(prices)
            drawdown = (prices - peak) / peak
            axes[1, 1].fill_between(times, drawdown * 100, 0, alpha=0.3, color='red')
            axes[1, 1].plot(times, drawdown * 100, 'r-', linewidth=1.5)
            axes[1, 1].set_title('回撤 (%)')
            axes[1, 1].set_xlabel('时间')
            axes[1, 1].set_ylabel('回撤 (%)')
            axes[1, 1].grid(True, alpha=0.3)
            axes[1, 1].axhline(y=np.min(drawdown) * 100, color='darkred', linestyle=':',
                               label=f'最大回撤: {np.min(drawdown) * 100:.2f}%')
            axes[1, 1].legend()

        plt.tight_layout()
        plt.show()

    def plot_feature_indices(self):
        """
        绘制特征指标图表
        """
        if self.lppl_params is None:
            print("请先运行模型拟合")
            return

        indices = self.calculate_feature_indices()
        if indices is None:
            return

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle('LPPL模型特征指标分析', fontsize=14, fontweight='bold')

        # 概率残差指数
        axes[0].bar(['概率残差指数'], [indices['prob_residual_index']], color='skyblue', alpha=0.7)
        axes[0].set_title('概率残差指数\n(衡量价格偏离理想LPPL状态的程度)')
        axes[0].set_ylabel('指数值')
        axes[0].grid(True, alpha=0.3)
        axes[0].text(0, indices['prob_residual_index'], f'{indices["prob_residual_index"]:.4f}', 
                     ha='center', va='bottom')

        # 临界时间指数
        axes[1].bar(['临界时间指数'], [indices['critical_time_index']], color='lightgreen', alpha=0.7)
        axes[1].set_title('临界时间指数\n(预测泡沫破裂时间)')
        axes[1].set_ylabel('时间单位')
        axes[1].grid(True, alpha=0.3)
        axes[1].text(0, indices['critical_time_index'], f'{indices["critical_time_index"]:.2f}', 
                     ha='center', va='bottom')

        # 趋势发展频率指数
        axes[2].bar(['趋势频率指数'], [indices['trend_freq_index']], color='salmon', alpha=0.7)
        axes[2].set_title('趋势发展频率指数\n(反映泡沫演化振荡频率)')
        axes[2].set_ylabel('频率值')
        axes[2].grid(True, alpha=0.3)
        axes[2].text(0, indices['trend_freq_index'], f'{indices["trend_freq_index"]:.4f}', 
                     ha='center', va='bottom')

        plt.tight_layout()
        plt.show()

    def predict_critical_time(self):
        """        
        预测临界时间(崩盘时间)
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
        分析实际加载的数据（使用优化的LPPL模型拟合）
        """
        print("使用优化的LPPL模型分析实际数据...")
        
        # 首先进行标准LPPL拟合
        result = self.fit_lppl_model()

        if result is not None:
            # 检测泡沫状态
            print("\n检测泡沫状态...")
            self.detect_bubble_regime()

            # 计算特征指标
            print("\n计算特征指标...")
            self.calculate_feature_indices()

            # 检测泡沫阶段
            print("\n检测泡沫阶段...")
            self.detect_bubble_phase()

            # 生成择时策略信号
            print("\n生成择时策略信号...")
            self.timing_strategy_signals()

        return result

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

    def save_results(self, filename='lppl_optimized_results.xlsx'):
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

        if 'fitted_prices' in self.results:
            results_df['拟合价格'] = self.results['fitted_prices']

        if 'returns' in self.results:
            results_df['收益率'] = np.concatenate([[0], self.results['returns']])

        if 'drawdown' in self.results:
            results_df['回撤(%)'] = np.concatenate([[0], self.results['drawdown']]) * 100

        if 'residuals' in self.results:
            results_df['残差'] = self.results['residuals']

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
    print("优化对数周期幂律模型 (Optimized LPPL Model)")
    print("=" * 50)

    # 显示数据结构说明
    print_data_structure()

    # 创建模型实例
    model = OptimizedLPPLModel()

    # 直接使用弹窗选择文件
    print("\n请在弹窗中选择Excel数据文件（可选）:")
    data_loaded = model.load_data_with_dialog()

    # 根据是否有数据选择分析方式
    if data_loaded and model.data is not None:
        print("\n检测到实际数据，开始使用优化的LPPL模型进行分析...")

        # 使用优化的分析方法
        result = model.analyze_real_data()

        if result is not None:
            # 绘制结果
            show_plot = input("\n是否显示结果图表? (y/n, 默认y): ").strip().lower()
            if show_plot != 'n':  # 默认为y，用户按回车直接显示
                model.plot_results()
                
                # 显示特征指标图表
                show_features = input("\n是否显示特征指标图表? (y/n, 默认y): ").strip().lower()
                if show_features != 'n':
                    model.plot_feature_indices()

            # 保存结果
            save_choice = input("\n是否保存结果到Excel文件? (y/n, 默认n): ").strip().lower()
            if save_choice == 'y':  # 默认为n，用户需要明确选择y才会保存
                save_file = input("请输入保存结果的Excel文件名 (直接回车使用默认名称): ").strip()
                if not save_file:
                    save_file = 'lppl_optimized_results.xlsx'
                if not save_file.endswith('.xlsx'):
                    save_file += '.xlsx'
                model.save_results(save_file)
    else:
        print("\nLPPL模型需要实际数据进行分析，请提供有效的价格数据文件")
        return

    print("\n程序运行完成!")


if __name__ == "__main__":
    main()