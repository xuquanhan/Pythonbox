import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class PerformanceMetrics:
    win_rate: float
    profit_loss_ratio: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_profit: float
    avg_loss: float
    total_profit: float
    total_loss: float


@dataclass
class TradeResult:
    code: str
    name: str
    buy_date: datetime
    sell_date: datetime
    buy_price: float
    sell_price: float
    quantity: int
    profit: float
    profit_rate: float
    is_win: bool


class PerformanceCalculator:
    """
    交易绩效计算器
    
    计算以下指标：
    - 胜率
    - 盈亏比
    - 夏普比率
    - 最大回撤
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._trade_results: Optional[List[TradeResult]] = None
    
    def _calculate_daily_total_assets(self) -> pd.DataFrame:
        """
        计算每日总资产（现金 + 逆回购 + 持仓市值）
        
        Returns:
            DataFrame 包含日期和总资产
        """
        if self.df.empty:
            return pd.DataFrame(columns=['date', 'total_assets'])
        
        df = self.df.copy().sort_values('date')
        
        daily_data = []
        
        for date in sorted(df['date'].dt.date.unique()):
            date_df = df[df['date'].dt.date == date]
            
            # 当日现金余额（取最后一笔的余额）
            cash_balance = date_df['balance'].iloc[-1] if not date_df.empty else 0
            
            # 逆回购金额（当日发生的逆回购）
            repo_lend = date_df[date_df['trade_type'] == 'repo_lend']['amount'].sum()
            repo_return = date_df[date_df['trade_type'] == 'repo_return']['amount'].sum()
            
            # 累计逆回购余额（需要计算所有历史逆回购）
            prev_df = df[df['date'].dt.date <= date]
            total_repo_lend = prev_df[prev_df['trade_type'] == 'repo_lend']['amount'].sum()
            total_repo_return = prev_df[prev_df['trade_type'] == 'repo_return']['amount'].sum()
            repo_balance = total_repo_lend - total_repo_return
            
            # 计算当日持仓市值
            position_value = 0.0
            for code in prev_df['security_code'].unique():
                if not code or code in ['银行转证券', '证券转银行', '利息归本', '']:
                    continue
                
                code_df = prev_df[prev_df['security_code'] == code]
                buy_qty = code_df[code_df['trade_type'] == 'buy']['quantity'].sum()
                sell_qty = code_df[code_df['trade_type'] == 'sell']['quantity'].sum()
                position = buy_qty - sell_qty
                
                if position > 0:
                    # 使用当日该股票最后一笔交易价格作为当前价格
                    code_today = date_df[date_df['security_code'] == code]
                    if not code_today.empty:
                        price = code_today['price'].iloc[-1]
                    else:
                        # 如果没有当日交易，使用之前最后一次交易价格
                        price = code_df['price'].iloc[-1] if not code_df.empty else 0
                    position_value += position * price
            
            # 当日总资产 = 现金 + 逆回购余额 + 持仓市值
            total_assets = cash_balance + repo_balance + position_value
            
            daily_data.append({
                'date': pd.Timestamp(date),
                'cash': cash_balance,
                'repo_balance': repo_balance,
                'position_value': position_value,
                'total_assets': total_assets
            })
        
        return pd.DataFrame(daily_data)
    
    def calculate_all_metrics(self) -> PerformanceMetrics:
        """
        计算所有绩效指标
        
        Returns:
            PerformanceMetrics 对象
        """
        trade_results = self._calculate_trade_results()
        
        if not trade_results:
            return PerformanceMetrics(
                win_rate=0.0,
                profit_loss_ratio=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_profit=0.0,
                avg_loss=0.0,
                total_profit=0.0,
                total_loss=0.0
            )
        
        win_rate = self.calculate_win_rate(trade_results)
        pl_ratio = self.calculate_profit_loss_ratio(trade_results)
        sharpe = self.calculate_sharpe_ratio(trade_results)
        max_dd = self.calculate_max_drawdown(trade_results)
        
        profits = [t.profit for t in trade_results if t.is_win]
        losses = [abs(t.profit) for t in trade_results if not t.is_win]
        
        return PerformanceMetrics(
            win_rate=win_rate,
            profit_loss_ratio=pl_ratio,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            total_trades=len(trade_results),
            winning_trades=len(profits),
            losing_trades=len(losses),
            avg_profit=np.mean(profits) if profits else 0.0,
            avg_loss=np.mean(losses) if losses else 0.0,
            total_profit=sum(profits),
            total_loss=sum(losses)
        )
    
    def calculate_win_rate(self, trade_results: List[TradeResult] = None) -> float:
        """
        计算胜率
        
        胜率 = 盈利交易次数 / 总交易次数
        """
        if trade_results is None:
            trade_results = self._calculate_trade_results()
        
        if not trade_results:
            return 0.0
        
        wins = sum(1 for t in trade_results if t.is_win)
        return wins / len(trade_results) * 100
    
    def calculate_profit_loss_ratio(self, trade_results: List[TradeResult] = None) -> float:
        """
        计算盈亏比
        
        盈亏比 = 平均盈利金额 / 平均亏损金额
        """
        if trade_results is None:
            trade_results = self._calculate_trade_results()
        
        if not trade_results:
            return 0.0
        
        profits = [t.profit for t in trade_results if t.is_win and t.profit > 0]
        losses = [abs(t.profit) for t in trade_results if not t.is_win and t.profit < 0]
        
        if not profits or not losses:
            return 0.0
        
        avg_profit = np.mean(profits)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return float('inf') if avg_profit > 0 else 0.0
        
        return avg_profit / avg_loss
    
    def calculate_sharpe_ratio(
        self, 
        trade_results: List[TradeResult] = None,
        risk_free_rate: float = 0.03
    ) -> float:
        """
        计算夏普比率（基于每日总资产的日收益率序列）
        
        夏普比率 = (年化收益率 - 无风险利率) / 收益率标准差
        
        Args:
            trade_results: 交易结果列表（未使用，保留参数兼容性）
            risk_free_rate: 无风险利率，默认3%
        """
        daily_assets = self._calculate_daily_total_assets()
        
        if daily_assets.empty or len(daily_assets) < 2:
            return 0.0
        
        # 计算日收益率
        daily_assets['daily_return'] = daily_assets['total_assets'].pct_change()
        
        # 移除 NaN 和 inf
        returns = daily_assets['daily_return'].dropna()
        returns = returns[np.isfinite(returns)]
        
        if len(returns) < 2:
            return 0.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0 or np.isnan(std_return):
            return 0.0
        
        # 年化（假设一年252个交易日）
        annualized_return = avg_return * 252
        annualized_std = std_return * np.sqrt(252)
        
        sharpe = (annualized_return - risk_free_rate) / annualized_std
        
        return sharpe
    
    def calculate_max_drawdown(self, trade_results: List[TradeResult] = None) -> float:
        """
        计算最大回撤率（基于总资产 = 现金余额 + 逆回购余额 + 持仓市值）
        
        Args:
            trade_results: 交易结果列表（未使用，保留参数兼容性）
        """
        daily_assets = self._calculate_daily_total_assets()
        
        if daily_assets.empty:
            return 0.0
        
        total_assets = daily_assets['total_assets'].tolist()
        
        if not total_assets or len(total_assets) < 2:
            return 0.0
        
        # 计算最大回撤
        max_drawdown = 0.0
        peak = total_assets[0]
        
        for assets in total_assets:
            if assets > peak:
                peak = assets
            
            if peak > 0:
                drawdown = (peak - assets) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        return max_drawdown * 100
    
    def _calculate_trade_results(self) -> List[TradeResult]:
        """
        计算每笔交易的结果
        
        使用先进先出(FIFO)方法匹配买卖
        """
        if self._trade_results is not None:
            return self._trade_results
        
        trade_df = self.df[self.df['trade_type'].isin(['buy', 'sell'])].copy()
        
        if trade_df.empty:
            self._trade_results = []
            return self._trade_results
        
        trade_df = trade_df.sort_values('date')
        
        results = []
        
        for code in trade_df['security_code'].unique():
            code_df = trade_df[trade_df['security_code'] == code].copy()
            
            buy_queue = []
            
            for _, row in code_df.iterrows():
                if row['trade_type'] == 'buy':
                    buy_queue.append({
                        'date': row['date'],
                        'price': row['price'],
                        'quantity': row['quantity'],
                        'fee': row['total_fee']
                    })
                elif row['trade_type'] == 'sell':
                    sell_qty = row['quantity']
                    sell_price = row['price']
                    sell_date = row['date']
                    sell_fee = row['total_fee']
                    sec_name = row['security_name']
                    
                    remaining_qty = sell_qty
                    
                    while remaining_qty > 0 and buy_queue:
                        buy = buy_queue[0]
                        
                        matched_qty = min(remaining_qty, buy['quantity'])
                        
                        buy_amount = matched_qty * buy['price']
                        sell_amount = matched_qty * sell_price
                        
                        buy_fee_ratio = matched_qty / buy['quantity']
                        matched_buy_fee = buy['fee'] * buy_fee_ratio
                        matched_sell_fee = sell_fee * (matched_qty / sell_qty)
                        
                        profit = sell_amount - buy_amount - matched_buy_fee - matched_sell_fee
                        
                        if buy_amount > 0:
                            profit_rate = profit / buy_amount * 100
                        else:
                            profit_rate = 0
                        
                        results.append(TradeResult(
                            code=code,
                            name=sec_name,
                            buy_date=buy['date'],
                            sell_date=sell_date,
                            buy_price=buy['price'],
                            sell_price=sell_price,
                            quantity=matched_qty,
                            profit=profit,
                            profit_rate=profit_rate,
                            is_win=profit > 0
                        ))
                        
                        remaining_qty -= matched_qty
                        buy['quantity'] -= matched_qty
                        
                        if buy['quantity'] <= 0:
                            buy_queue.pop(0)
        
        self._trade_results = results
        return results
    
    def get_trade_results_df(self) -> pd.DataFrame:
        """
        获取交易结果 DataFrame
        """
        results = self._calculate_trade_results()
        
        if not results:
            return pd.DataFrame()
        
        data = []
        for t in results:
            data.append({
                '证券代码': t.code,
                '证券名称': t.name,
                '买入日期': t.buy_date,
                '卖出日期': t.sell_date,
                '买入价格': t.buy_price,
                '卖出价格': t.sell_price,
                '数量': t.quantity,
                '盈亏': t.profit,
                '盈亏率(%)': t.profit_rate,
                '是否盈利': '是' if t.is_win else '否'
            })
        
        return pd.DataFrame(data)
    
    def get_monthly_performance(self) -> pd.DataFrame:
        """
        获取月度绩效统计
        """
        results = self._calculate_trade_results()
        
        if not results:
            return pd.DataFrame()
        
        data = []
        for t in results:
            data.append({
                'date': t.sell_date,
                'profit': t.profit,
                'is_win': t.is_win
            })
        
        df = pd.DataFrame(data)
        df['month'] = df['date'].dt.to_period('M')
        
        monthly = df.groupby('month').agg({
            'profit': ['sum', 'count'],
            'is_win': 'sum'
        }).reset_index()
        
        monthly.columns = ['月份', '盈亏合计', '交易次数', '盈利次数']
        monthly['月份'] = monthly['月份'].astype(str)
        monthly['胜率(%)'] = monthly['盈利次数'] / monthly['交易次数'] * 100
        
        return monthly
    
    def get_stock_performance(self) -> pd.DataFrame:
        """
        获取各股票绩效统计
        """
        results = self._calculate_trade_results()
        
        if not results:
            return pd.DataFrame()
        
        data = []
        for t in results:
            data.append({
                'code': t.code,
                'name': t.name,
                'profit': t.profit,
                'profit_rate': t.profit_rate,
                'is_win': t.is_win
            })
        
        df = pd.DataFrame(data)
        
        stock_perf = df.groupby(['code', 'name']).agg({
            'profit': ['sum', 'mean'],
            'profit_rate': 'mean',
            'is_win': ['sum', 'count']
        }).reset_index()
        
        stock_perf.columns = ['证券代码', '证券名称', '总盈亏', '平均盈亏', '平均盈亏率(%)', '盈利次数', '交易次数']
        stock_perf['胜率(%)'] = stock_perf['盈利次数'] / stock_perf['交易次数'] * 100
        
        return stock_perf.sort_values('总盈亏', ascending=False)
