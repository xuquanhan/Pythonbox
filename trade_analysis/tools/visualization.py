import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
import warnings

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


class Visualizer:
    def __init__(self, output_dir: str = './output'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_balance_curve(self, balance_df: pd.DataFrame, save_path: Optional[str] = None) -> Optional[str]:
        if not HAS_MATPLOTLIB:
            print("Warning: matplotlib is required for visualization")
            return None

        if balance_df.empty:
            return None

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(balance_df['日期'], balance_df['账户余额'], linewidth=1.5, color='#4472C4')
        ax.fill_between(balance_df['日期'], balance_df['账户余额'], alpha=0.3, color='#4472C4')

        ax.set_title('账户余额变化曲线', fontsize=14, fontweight='bold')
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('余额 (元)', fontsize=12)

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=45)

        ax.grid(True, alpha=0.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        plt.tight_layout()

        if save_path:
            filepath = self.output_dir / save_path
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            plt.close()
            return None

    def plot_profit_distribution(self, trades: List, save_path: Optional[str] = None) -> Optional[str]:
        if not HAS_MATPLOTLIB:
            print("Warning: matplotlib is required for visualization")
            return None

        if not trades:
            return None

        profits = [t.profit for t in trades]

        fig, ax = plt.subplots(figsize=(10, 6))

        colors = ['#28a745' if p >= 0 else '#dc3545' for p in profits]
        bars = ax.bar(range(len(profits)), sorted(profits, reverse=True), color=colors, alpha=0.7)

        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title('交易盈亏分布', fontsize=14, fontweight='bold')
        ax.set_xlabel('交易序号（按盈亏排序）', fontsize=12)
        ax.set_ylabel('盈亏金额 (元)', fontsize=12)

        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        win_count = sum(1 for p in profits if p >= 0)
        loss_count = len(profits) - win_count
        ax.text(0.02, 0.98, f'盈利: {win_count}笔\n亏损: {loss_count}笔',
                transform=ax.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        if save_path:
            filepath = self.output_dir / save_path
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            plt.close()
            return None

    def plot_profit_by_security(self, df: pd.DataFrame, save_path: Optional[str] = None) -> Optional[str]:
        if not HAS_MATPLOTLIB:
            print("Warning: matplotlib is required for visualization")
            return None

        if df.empty:
            return None

        df = df.head(15)
        df = df.sort_values('总盈亏')

        fig, ax = plt.subplots(figsize=(10, 8))

        colors = ['#28a745' if p >= 0 else '#dc3545' for p in df['总盈亏']]
        bars = ax.barh(df['证券名称'], df['总盈亏'], color=colors, alpha=0.7)

        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title('股票盈亏排行（前15）', fontsize=14, fontweight='bold')
        ax.set_xlabel('盈亏金额 (元)', fontsize=12)

        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        plt.tight_layout()

        if save_path:
            filepath = self.output_dir / save_path
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            plt.close()
            return None

    def plot_monthly_profit(self, monthly_df: pd.DataFrame, save_path: Optional[str] = None) -> Optional[str]:
        if not HAS_MATPLOTLIB:
            print("Warning: matplotlib is required for visualization")
            return None

        if monthly_df.empty:
            return None

        fig, ax = plt.subplots(figsize=(14, 6))

        x = range(len(monthly_df))
        colors = ['#28a745' if p >= 0 else '#dc3545' for p in monthly_df['净发生额']]
        bars = ax.bar(x, monthly_df['净发生额'], color=colors, alpha=0.7)

        ax.set_xticks(x)
        ax.set_xticklabels(monthly_df['month'], rotation=45, ha='right')

        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title('月度盈亏统计', fontsize=14, fontweight='bold')
        ax.set_xlabel('月份', fontsize=12)
        ax.set_ylabel('净发生额 (元)', fontsize=12)

        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        plt.tight_layout()

        if save_path:
            filepath = self.output_dir / save_path
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            plt.close()
            return None

    def plot_trade_heatmap(self, df: pd.DataFrame, save_path: Optional[str] = None) -> Optional[str]:
        if not HAS_MATPLOTLIB or not HAS_SEABORN:
            print("Warning: matplotlib and seaborn are required for heatmap")
            return None

        trade_df = df[df['trade_type'].isin(['buy', 'sell'])].copy()
        if trade_df.empty:
            return None

        trade_df['weekday'] = trade_df['date'].dt.dayofweek
        trade_df['hour'] = 0
        trade_df['month'] = trade_df['date'].dt.month

        heatmap_data = trade_df.groupby(['weekday', 'month']).size().unstack(fill_value=0)

        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        heatmap_data.index = weekday_names[:len(heatmap_data)]

        fig, ax = plt.subplots(figsize=(12, 6))

        sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='YlOrRd', ax=ax)

        ax.set_title('交易频率热力图（星期×月份）', fontsize=14, fontweight='bold')
        ax.set_xlabel('月份', fontsize=12)
        ax.set_ylabel('星期', fontsize=12)

        plt.tight_layout()

        if save_path:
            filepath = self.output_dir / save_path
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            return str(filepath)
        else:
            plt.show()
            plt.close()
            return None
