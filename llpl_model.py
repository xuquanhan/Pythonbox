#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长期泡沫崩溃模型(Long-term泡沫崩溃模型)
用于分析资产价格泡沫及其崩溃对经济的长期影响
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class LLPLModel:
    """
    长期泡沫崩溃模型类
    """
    
    def __init__(self):
        self.data = None
        self.parameters = {}
        self.results = {}
        
    def load_data(self, excel_file):
        """
        加载Excel数据
        
        参数:
        excel_file (str): Excel文件路径
        """
        try:
            # 读取Excel文件
            self.data = pd.read_excel(excel_file)
            print(f"成功加载数据，共有 {len(self.data)} 行数据")
            print("数据列名:")
            for col in self.data.columns:
                print(f"  - {col}")
            return True
        except FileNotFoundError:
            print(f"错误: 找不到文件 '{excel_file}'")
            return False
        except Exception as e:
            print(f"加载数据时发生错误: {str(e)}")
            return False
    
    def input_parameters(self):
        """
        用户输入模型参数
        """
        print("\n请输入模型参数:")
        
        try:
            # 泡沫增长参数
            self.parameters['initial_price'] = float(input("初始资产价格 (默认100): ") or 100)
            self.parameters['growth_rate'] = float(input("泡沫增长率 (默认0.05): ") or 0.05)
            self.parameters['peak_time'] = int(input("泡沫峰值时间点 (默认50): ") or 50)
            
            # 崩溃参数
            self.parameters['crash_severity'] = float(input("崩溃严重程度 (0-1, 默认0.7): ") or 0.7)
            self.parameters['recovery_time'] = int(input("恢复时间 (默认30): ") or 30)
            
            # 经济影响参数
            self.parameters['impact_factor'] = float(input("经济影响因子 (默认0.3): ") or 0.3)
            self.parameters['volatility'] = float(input("市场波动性 (默认0.2): ") or 0.2)
            
            print("\n参数设置完成!")
            for key, value in self.parameters.items():
                print(f"  {key}: {value}")
                
        except ValueError:
            print("输入格式错误，使用默认参数")
            self._set_default_parameters()
    
    def _set_default_parameters(self):
        """
        设置默认参数
        """
        self.parameters = {
            'initial_price': 100,
            'growth_rate': 0.05,
            'peak_time': 50,
            'crash_severity': 0.7,
            'recovery_time': 30,
            'impact_factor': 0.3,
            'volatility': 0.2
        }
    
    def simulate_bubble_crash(self, time_periods=100):
        """
        模拟泡沫生成和崩溃过程
        
        参数:
        time_periods (int): 模拟时间周期数
        """
        if not self.parameters:
            print("请先设置模型参数")
            return None
            
        params = self.parameters
        t = np.arange(time_periods)
        
        # 初始化价格数组
        prices = np.zeros(time_periods)
        prices[0] = params['initial_price']
        
        # 泡沫增长阶段
        for i in range(1, min(params['peak_time'], time_periods)):
            growth = params['growth_rate'] * (1 + np.random.normal(0, params['volatility']))
            prices[i] = prices[i-1] * (1 + growth)
        
        # 泡沫峰值
        peak_price = prices[min(params['peak_time']-1, time_periods-1)]
        
        # 崩溃阶段
        crash_start = min(params['peak_time'], time_periods-1)
        for i in range(crash_start, min(crash_start + params['recovery_time'], time_periods)):
            # 线性下降到崩溃后的价格
            crash_progress = (i - crash_start) / params['recovery_time']
            crash_multiplier = 1 - params['crash_severity'] * (1 - crash_progress)
            prices[i] = peak_price * crash_multiplier
        
        # 恢复阶段
        recovery_start = min(crash_start + params['recovery_time'], time_periods)
        for i in range(recovery_start, time_periods):
            # 逐渐恢复到初始水平
            recovery_years = i - recovery_start
            recovery_factor = 1 + (params['growth_rate'] * recovery_years / 10)
            prices[i] = params['initial_price'] * recovery_factor
        
        # 添加随机波动
        noise = np.random.normal(1, params['volatility']/10, time_periods)
        prices = prices * noise
        prices = np.maximum(prices, params['initial_price'] * 0.5)  # 价格不会低于初始价格的一半
        
        self.results['prices'] = prices
        self.results['time'] = t
        print("泡沫崩溃模拟完成!")
        return prices
    
    def calculate_economic_impact(self):
        """
        计算经济影响指标
        """
        if 'prices' not in self.results:
            print("请先运行模拟")
            return
            
        prices = self.results['prices']
        params = self.parameters
        
        # 计算收益率
        returns = np.diff(prices) / prices[:-1]
        
        # 计算最大回撤
        peak = np.maximum.accumulate(prices)
        drawdown = (prices - peak) / peak
        
        # 计算波动率
        volatility = np.std(returns) * np.sqrt(252)  # 年化波动率假设每日数据
        
        # 计算VaR (Value at Risk)
        var_95 = np.percentile(returns, 5)
        
        self.results['returns'] = returns
        self.results['drawdown'] = drawdown
        self.results['volatility'] = volatility
        self.results['var_95'] = var_95
        
        print("\n经济影响分析结果:")
        print(f"  最大回撤: {np.min(drawdown)*100:.2f}%")
        print(f"  年化波动率: {volatility*100:.2f}%")
        print(f"  95% VaR: {var_95*100:.2f}%")
        
        return {
            'max_drawdown': np.min(drawdown),
            'volatility': volatility,
            'var_95': var_95
        }
    
    def plot_results(self):
        """
        绘制结果图表
        """
        if 'prices' not in self.results:
            print("请先运行模拟")
            return
            
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('长期泡沫崩溃模型分析结果', fontsize=16)
        
        # 价格走势图
        axes[0, 0].plot(self.results['time'], self.results['prices'], 'b-', linewidth=2)
        axes[0, 0].set_title('资产价格走势')
        axes[0, 0].set_xlabel('时间')
        axes[0, 0].set_ylabel('价格')
        axes[0, 0].grid(True)
        
        # 收益率
        if 'returns' in self.results:
            axes[0, 1].plot(self.results['time'][1:], self.results['returns'], 'g-', linewidth=1)
            axes[0, 1].set_title('收益率')
            axes[0, 1].set_xlabel('时间')
            axes[0, 1].set_ylabel('收益率')
            axes[0, 1].grid(True)
        
        # 回撤
        if 'drawdown' in self.results:
            axes[1, 0].plot(self.results['time'], self.results['drawdown']*100, 'r-', linewidth=2)
            axes[1, 0].set_title('回撤 (%)')
            axes[1, 0].set_xlabel('时间')
            axes[1, 0].set_ylabel('回撤 (%)')
            axes[1, 0].grid(True)
        
        # 价格分布直方图
        axes[1, 1].hist(self.results['prices'], bins=30, alpha=0.7, color='purple')
        axes[1, 1].set_title('价格分布')
        axes[1, 1].set_xlabel('价格')
        axes[1, 1].set_ylabel('频次')
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def save_results(self, filename='llpl_model_results.xlsx'):
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


def main():
    """
    主函数
    """
    print("=" * 50)
    print("长期泡沫崩溃模型 (LLPL Model)")
    print("=" * 50)
    
    # 创建模型实例
    model = LLPLModel()
    
    # 获取用户输入
    while True:
        excel_file = input("\n请输入Excel数据文件路径 (直接回车跳过数据加载): ").strip()
        if not excel_file:
            break
        if model.load_data(excel_file):
            break
        else:
            retry = input("是否重新输入文件路径? (y/n): ").strip().lower()
            if retry != 'y':
                break
    
    # 输入模型参数
    model.input_parameters()
    
    # 运行模拟
    print("\n开始运行泡沫崩溃模拟...")
    prices = model.simulate_bubble_crash()
    
    if prices is not None:
        # 计算经济影响
        model.calculate_economic_impact()
        
        # 绘制结果
        show_plot = input("\n是否显示结果图表? (y/n): ").strip().lower()
        if show_plot == 'y':
            model.plot_results()
        
        # 保存结果
        save_file = input("\n请输入保存结果的Excel文件名 (直接回车使用默认名称): ").strip()
        if not save_file:
            save_file = 'llpl_model_results.xlsx'
        if not save_file.endswith('.xlsx'):
            save_file += '.xlsx'
        model.save_results(save_file)
        
    print("\n程序运行完成!")


if __name__ == "__main__":
    main()