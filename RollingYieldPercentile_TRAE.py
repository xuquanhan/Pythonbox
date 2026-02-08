import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import wmi  # pip install WMI
import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='stock_analyzer.log'
)

class WindStockAnalyzer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Wind股票分位数分析器")
        self.root.geometry("800x600")
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 股票代码输入
        ttk.Label(self.main_frame, text="股票代码:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.stock_code = ttk.Entry(self.main_frame, width=20)
        self.stock_code.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        # 添加回车键事件绑定
        self.stock_code.bind('<Return>', lambda event: self.analyze_stock())
        
        # 平均收益率窗口参数 (n)
        ttk.Label(self.main_frame, text="平均收益率窗口 (n):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.roll_window = ttk.Entry(self.main_frame, width=10)
        self.roll_window.insert(0, "20")  # 默认20天平均收益率
        self.roll_window.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        # 添加回车键事件绑定
        self.roll_window.bind('<Return>', lambda event: self.analyze_stock())
        
        # 分位数计算窗口参数 (m)
        ttk.Label(self.main_frame, text="分位数计算窗口 (m):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.percentile_window = ttk.Entry(self.main_frame, width=10)
        self.percentile_window.insert(0, "200")  # 默认200天分位数计算窗口
        self.percentile_window.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        # 添加回车键事件绑定
        self.percentile_window.bind('<Return>', lambda event: self.analyze_stock())
        
        # 分析按钮
        self.analyze_button = ttk.Button(self.main_frame, text="开始分析", 
                                        command=self.analyze_stock)
        self.analyze_button.grid(row=3, column=0, columnspan=2, pady=10)
        
        # 结果显示区域
        self.result_frame = ttk.LabelFrame(self.main_frame, text="分析结果", padding="10")
        self.result_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        
        # 文本结果
        self.result_text = tk.Text(self.result_frame, height=20, width=70)
        self.result_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        
        # 图表结果 - 分位数分布
        self.chart_frame = ttk.LabelFrame(self.main_frame, text="分位数分布", padding="10")
        self.chart_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        
        # 图表结果 - 收盘价和滚动收益率
        self.price_yield_frame = ttk.LabelFrame(self.main_frame, text="收盘价和滚动收益率", padding="10")
        self.price_yield_frame.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        
        # 配置网格权重
        self.main_frame.grid_rowconfigure(4, weight=1)
        self.main_frame.grid_rowconfigure(5, weight=1)
        self.main_frame.grid_rowconfigure(6, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        # 历史分析记录
        self.history = []
    
    def analyze_stock(self):
        stock_code = self.stock_code.get().strip()
        
        if not stock_code:
            messagebox.showerror("错误", "请输入股票代码！")
            return
            
        try:
            roll_window = int(self.roll_window.get())  # 滚动收益率窗口 (n)
            percentile_window = int(self.percentile_window.get())  # 分位数计算窗口 (m)
            
            if roll_window <= 0:
                messagebox.showerror("错误", "滚动收益率窗口必须大于0！")
                return
            
            if percentile_window <= 0:
                messagebox.showerror("错误", "分位数计算窗口必须大于0！")
                return
            
            if percentile_window < roll_window:
                messagebox.showerror("错误", "分位数计算窗口必须大于或等于滚动收益率窗口！")
                return
        except ValueError:
            messagebox.showerror("错误", "请输入有效的窗口数值！")
            return
            
        # 获取Wind数据并计算分位数
        try:
            self.analyze_button.config(state=tk.DISABLED)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "正在分析，请稍候...\n")
            self.result_text.insert(tk.END, "1. 连接Wind API...\n")
            self.root.update()
            
            # 导入并使用WindPy
            try:
                from WindPy import w
            except ImportError:
                raise Exception("WindPy模块未安装，请先安装Wind金融终端并确保Python接口已配置")
            
            # 启动Wind API
            try:
                w.start()
                if not w.isconnected():
                    raise Exception("Wind API连接失败，请确保Wind金融终端已启动并登录")
            except Exception as e:
                raise Exception(f"Wind API启动失败: {str(e)}")
            
            self.result_text.insert(tk.END, "2. 获取历史数据...\n")
            self.root.update()
            
            result = self.calculate_percentile(stock_code, roll_window, percentile_window)
            
            self.result_text.insert(tk.END, "3. 计算分位数...\n")
            self.root.update()
            
            self.result_text.insert(tk.END, "4. 生成图表...\n")
            self.root.update()
            
            self.plot_percentile_distribution(result)
            self.plot_price_and_yield(result)
            
            self.result_text.insert(tk.END, "\n分析完成！\n\n")
            self.result_text.insert(tk.END, "===== 分析结果 =====\n")
            self.display_result_without_clear(result, stock_code)
            self.root.update()
            
            # 保存到历史记录
            self.history.append({
                'stock_code': stock_code,
                'roll_window': roll_window,
                'percentile_window': percentile_window,
                'result': result,
                'timestamp': datetime.now()
            })
            
            logging.info(f"分析完成: {stock_code}, 滚动窗口: {roll_window}, 分位数窗口: {percentile_window}, 分位数: {result['percentile_rank']:.2%}")
        except Exception as e:
            error_msg = f"错误: {str(e)}"
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, error_msg)
            messagebox.showerror("分析错误", error_msg)
            logging.error(f"分析错误: {str(e)}")
        finally:
            self.analyze_button.config(state=tk.NORMAL)
    
    def calculate_percentile(self, code, roll_window, percentile_window):
        """计算滚动收益率分位数排名"""
        # 导入并使用WindPy
        from WindPy import w
        
        # 获取足够的历史数据（至少需要 percentile_window + roll_window 天）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=(percentile_window + roll_window) * 2)  # 多获取一些数据以确保充足
        
        hist_data = w.wsd(code, "close", 
                         f"{start_date.strftime('%Y-%m-%d')}",
                         f"{end_date.strftime('%Y-%m-%d')}", 
                         f"Days=1;Fill=Previous;PriceAdj=F")
        
        if hist_data.ErrorCode != 0:
            raise Exception(f"Wind API错误: {hist_data.ErrorCode}，请检查股票代码是否正确")
        
        if not hist_data.Data or len(hist_data.Data[0]) == 0:
            raise Exception("未获取到股票数据，请检查股票代码是否正确")
        
        # 转换为价格序列
        prices = pd.Series(hist_data.Data[0], index=hist_data.Times)
        
        # 获取实时数据并更新价格序列
        try:
            # 首先检查今天是否是交易日
            today = datetime.now().date()
            # 简单判断：周末不是交易日
            if today.weekday() >= 5:  # 5=周六, 6=周日
                print(f"今天是{today.strftime('%Y-%m-%d')}，是周末，不是交易日，跳过实时数据获取")
            else:
                # 使用w.wss获取最新实时数据
                # 注意：w.wss的第一个参数应该是一个列表
                real_time_data = w.wss([code], "rt_last")
                if real_time_data.ErrorCode == 0 and real_time_data.Data and len(real_time_data.Data[0]) > 0:
                    real_time_price = real_time_data.Data[0][0]
                    # 创建当前时间作为索引
                    real_time_date = datetime.now()
                    # 检查实时价格是否有效
                    if real_time_price > 0:
                        # 检查是否已经有今天的数据
                        has_today_data = False
                        today_dates = []
                        
                        for t in prices.index:
                            # 检查t是否已经是date对象
                            if hasattr(t, 'date'):
                                # t是datetime对象，调用date()方法
                                if t.date() == today:
                                    has_today_data = True
                                    today_dates.append(t)
                            else:
                                # t已经是date对象，直接比较
                                if t == today:
                                    has_today_data = True
                                    today_dates.append(t)
                        
                        # 检查实时价格是否与昨天的价格相同
                        if len(prices) > 0:
                            yesterday_price = prices.iloc[-1]
                            # 如果实时价格与昨天的价格不同，或者今天还没有数据
                            if real_time_price != yesterday_price or not has_today_data:
                                if has_today_data:
                                    # 更新今天的数据
                                    prices = prices.drop(today_dates)
                                    prices.loc[real_time_date] = real_time_price
                                else:
                                    # 添加今天的数据
                                    prices.loc[real_time_date] = real_time_price
                                
                                # 确保数据按照时间顺序排序
                                prices = prices.sort_index()
                            else:
                                print(f"实时价格与昨天的价格相同 ({real_time_price})，跳过更新")
                        else:
                            # 没有历史数据，直接添加
                            prices.loc[real_time_date] = real_time_price
        except Exception as e:
            print(f"实时数据获取失败: {str(e)}")
            # 实时数据获取失败，使用历史数据
            pass
        
        # 计算每日收益率（涨跌幅）
        daily_returns = prices.pct_change().dropna()
        
        if len(daily_returns) == 0:
            raise Exception("无法计算每日收益率，请检查数据是否充足")
        
        # 检查最后一天的收益率是否为0
        if len(daily_returns) > 0:
            last_return = daily_returns.iloc[-1]
            if last_return == 0:
                # 最后一天的收益率为0，检查是否是今天的数据
                last_date = daily_returns.index[-1]
                today = datetime.now().date()
                # 检查last_date是否已经是date对象
                if hasattr(last_date, 'date'):
                    # last_date是datetime对象，调用date()方法
                    if last_date.date() == today:
                        # 是今天的数据，且收益率为0，我们可以删除今天的数据，使用昨天的数据作为最新数据
                        print("最后一天的收益率为0，删除今天的数据")
                        prices = prices[:-1]
                        daily_returns = prices.pct_change().dropna()
                else:
                    # last_date已经是date对象，直接比较
                    if last_date == today:
                        # 是今天的数据，且收益率为0，我们可以删除今天的数据，使用昨天的数据作为最新数据
                        print("最后一天的收益率为0，删除今天的数据")
                        prices = prices[:-1]
                        daily_returns = prices.pct_change().dropna()
        
        # 调试信息：打印最后几个价格和收益率
        print("\n--- 调试信息 ---")
        print(f"价格数据长度: {len(prices)}")
        print(f"收益率数据长度: {len(daily_returns)}")
        print("\n最后5个价格:")
        print(prices.tail())
        print("\n最后5个收益率:")
        print(daily_returns.tail())
        
        # 检查数据是否充足
        if len(daily_returns) < roll_window:
            raise Exception(f"每日收益率数据不足，当前只有{len(daily_returns)}个数据点，需要至少{roll_window}个")
        
        if len(daily_returns) < percentile_window:
            raise Exception(f"每日收益率数据不足，当前只有{len(daily_returns)}个数据点，需要至少{percentile_window}个")
        
        # 计算过去n天的平均收益率（滚动窗口）
        # 使用min_periods=1确保即使数据不足roll_window天也能计算
        rolling_averages = daily_returns.rolling(window=roll_window, min_periods=1).mean()
        
        # 获取过去m天的每日收益率和对应的平均收益率
        recent_daily_returns = daily_returns.tail(percentile_window)
        recent_rolling_averages = rolling_averages.tail(percentile_window)
        
        # 计算每一天的分位数
        percentile_ranks = []
        for i, avg_return in enumerate(recent_rolling_averages):
            # 对于每一天，获取其对应的过去m天的每日收益率
            # 注意：这里的逻辑是，对于第i天，其分位数是基于前m天的每日收益率计算的
            # 但为了与用户需求一致，我们使用整个recent_daily_returns窗口来计算
            # 这样可以确保每一天的分位数都是基于相同的m天窗口计算的
            rank = (recent_daily_returns <= avg_return).sum() / len(recent_daily_returns)
            percentile_ranks.append(rank)
        
        # 转换为Series
        percentile_ranks_series = pd.Series(percentile_ranks, index=recent_rolling_averages.index)
        
        # 获取过去m天的收盘价
        recent_prices = prices.tail(percentile_window)
        
        # 计算当前最新的分位数
        current_return = recent_rolling_averages.iloc[-1]
        current_percentile = percentile_ranks_series.iloc[-1]
        
        return {
            'current_return': current_return,
            'percentile_rank': current_percentile,
            'rolling_returns': recent_daily_returns,  # 这里存储的是每日收益率
            'recent_prices': recent_prices,
            'percentile_ranks': percentile_ranks_series,  # 这里存储的是每一天的分位数
            'stock_code': code,
            'data_source': 'Wind',
            'roll_window': roll_window,
            'percentile_window': percentile_window
        }
    
    def display_result(self, result, code):
        self.result_text.delete(1.0, tk.END)
        output = f"股票代码: {code}\n"
        output += f"数据来源: {result['data_source']}\n"
        n = result.get('roll_window', 'N/A')
        output += f"平均收益率窗口 (n): {n}天\n"
        output += f"分位数计算窗口 (m): {result.get('percentile_window', 'N/A')}天\n"
        output += f"当前{n}天平均收益率: {result['current_return']:.4f}\n"
        output += f"分位数 (Percentile): {result['percentile_rank']:.2%}\n"
        output += f"可用每日收益率数据点: {len(result['rolling_returns'])}个\n\n"

        output += "最近10个每日收益率数据:\n"
        output += str(result['rolling_returns'].tail(10))
        
        self.result_text.insert(tk.END, output)
    
    def display_result_without_clear(self, result, code):
        """显示结果但不清除文本框内容"""
        output = f"股票代码: {code}\n"
        output += f"数据来源: {result['data_source']}\n"
        n = result.get('roll_window', 'N/A')
        output += f"平均收益率窗口 (n): {n}天\n"
        output += f"分位数计算窗口 (m): {result.get('percentile_window', 'N/A')}天\n"
        output += f"当前{n}天平均收益率: {result['current_return']:.4f}\n"
        output += f"分位数 (Percentile): {result['percentile_rank']:.2%}\n"
        output += f"可用每日收益率数据点: {len(result['rolling_returns'])}个\n\n"

        output += "最近10个每日收益率数据:\n"
        output += str(result['rolling_returns'].tail(10))
        
        self.result_text.insert(tk.END, output)
    
    def plot_percentile_distribution(self, result):
        """绘制分位数分布图"""
        # 清空图表框架
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(7, 4))
        
        # 绘制每日收益率分布
        returns = result['rolling_returns']
        ax.hist(returns, bins=10, alpha=0.7, color='blue', edgecolor='black')
        
        # 标记当前n天平均收益率位置
        current_return = result['current_return']
        roll_window = result.get('roll_window', 20)
        percentile_rank = result.get('percentile_rank', 0)
        ax.axvline(x=current_return, color='red', linestyle='--', 
                   label=f'{roll_window}天平均收益率: {current_return:.4f}\n分位数 (Percentile): {percentile_rank:.2%}')
        
        # 添加标签和标题
        ax.set_xlabel('每日收益率')
        ax.set_ylabel('频数')
        roll_window = result.get('roll_window', 20)
        percentile_window = result.get('percentile_window', 200)
        ax.set_title(f'{result["stock_code"]} {roll_window}日平均收益率在{percentile_window}天的分布')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 将图表嵌入到Tkinter窗口
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 关闭图表以释放内存
        plt.close(fig)
    
    def plot_price_and_yield(self, result):
        """绘制收盘价和分位数折线图"""
        # 清空图表框架
        for widget in self.price_yield_frame.winfo_children():
            widget.destroy()
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        # 获取数据
        recent_prices = result.get('recent_prices', pd.Series())
        percentile_ranks = result.get('percentile_ranks', pd.Series())
        percentile_window = result.get('percentile_window', 200)
        
        # 创建图表
        fig, ax1 = plt.subplots(figsize=(7, 4))
        
        # 绘制收盘价（左侧y轴）
        if not recent_prices.empty:
            ax1.plot(recent_prices.index, recent_prices, 'b-', label='收盘价')
            ax1.set_xlabel('日期')
            ax1.set_ylabel('收盘价', color='b')
            ax1.tick_params('y', colors='b')
            ax1.grid(True, alpha=0.3)
        
        # 创建右侧y轴用于显示分位数
        ax2 = ax1.twinx()
        if not percentile_ranks.empty:
            ax2.plot(percentile_ranks.index, percentile_ranks, 'r--', label='分位数')
            ax2.set_ylabel('分位数', color='r')
            ax2.tick_params('y', colors='r')
            # 设置分位数的y轴范围为0-1
            ax2.set_ylim(0, 1)
            # 添加0.2和0.8的红色直线作为标识
            ax2.axhline(y=0.2, color='red', linestyle='-', linewidth=1, alpha=0.7)
            ax2.axhline(y=0.8, color='red', linestyle='-', linewidth=1, alpha=0.7)
        
        # 添加标题和图例
        title = f'{result["stock_code"]} 收盘价和分位数 ({percentile_window}天数据)'
        ax1.set_title(title)
        
        # 合并图例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # 旋转日期标签以避免重叠
        plt.xticks(rotation=45)
        fig.tight_layout()
        
        # 将图表嵌入到Tkinter窗口
        canvas = FigureCanvasTkAgg(fig, master=self.price_yield_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 关闭图表以释放内存
        plt.close(fig)
    
    def run(self):
        self.root.mainloop()

# 使用示例
if __name__ == "__main__":
    app = WindStockAnalyzer()
    app.run()