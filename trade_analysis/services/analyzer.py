import pandas as pd
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import logging

from ..models.data_cleaner import DataCleaner
from ..models.profit_calculator import ProfitCalculator, ProfitSummary
from ..models.performance import PerformanceCalculator, PerformanceMetrics
from ..services.price_fetcher import PriceFetcher
from ..utils.code_formatter import normalize_user_code

logger = logging.getLogger(__name__)


@dataclass
class AnalysisConfig:
    """
    分析配置
    """
    mode: str = 'full'
    stock_code: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    include_repo: bool = True
    include_dividend: bool = True
    price_source: str = 'akshare'
    manual_prices: Dict[str, float] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """
    分析结果
    """
    config: AnalysisConfig
    summary: Dict[str, Any]
    profit_summary: Optional[ProfitSummary] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    positions: Dict[str, Dict] = field(default_factory=dict)
    trade_results: Optional[pd.DataFrame] = None
    monthly_performance: Optional[pd.DataFrame] = None
    stock_performance: Optional[pd.DataFrame] = None


class TradeAnalyzer:
    """
    交易分析器
    """
    
    def __init__(self, filepath: str, config: AnalysisConfig = None):
        self.filepath = filepath
        self.config = config or AnalysisConfig()

        self.cleaner = DataCleaner(filepath)
        self.price_fetcher = PriceFetcher()

        self._df: Optional[pd.DataFrame] = None
        self._result: Optional[AnalysisResult] = None
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, config: AnalysisConfig = None) -> 'TradeAnalyzer':
        """
        从 DataFrame 创建分析器
        
        Args:
            df: 已清洗的数据
            config: 分析配置
            
        Returns:
            TradeAnalyzer 实例
        """
        instance = cls.__new__(cls)
        instance.filepath = None
        instance.config = config or AnalysisConfig()
        instance.cleaner = None
        instance.price_fetcher = PriceFetcher()

        instance._df = df.copy()
        instance._result = None

        return instance
    
    def run_analysis(self) -> AnalysisResult:
        logger.info(f"开始分析，模式: {self.config.mode}")
        
        if self._df is None:
            self._df = self.cleaner.clean()
        
        df = self._apply_filters()
        
        summary = self._get_summary(df)
        
        profit_calculator = ProfitCalculator(df)
        
        positions = profit_calculator._calculate_positions()
        close_prices = self._fetch_prices(positions)
        
        for code, pos in positions.items():
            if code in close_prices:
                pos['close_price'] = close_prices[code]
        
        profit_summary = profit_calculator.calculate_account_profit(close_prices)
        
        perf_calculator = PerformanceCalculator(df)
        performance_metrics = perf_calculator.calculate_all_metrics()
        
        trade_results = perf_calculator.get_trade_results_df()
        monthly_perf = perf_calculator.get_monthly_performance()
        stock_perf = perf_calculator.get_stock_performance()
        
        self._result = AnalysisResult(
            config=self.config,
            summary=summary,
            profit_summary=profit_summary,
            performance_metrics=performance_metrics,
            positions=positions,
            trade_results=trade_results,
            monthly_performance=monthly_perf,
            stock_performance=stock_perf
        )
        
        logger.info("分析完成")
        return self._result
    
    def _apply_filters(self) -> pd.DataFrame:
        df = self._df.copy()
        
        if self.config.start_date or self.config.end_date:
            if self.cleaner:
                df = self.cleaner.filter_by_date(
                    self.config.start_date, 
                    self.config.end_date
                )
            else:
                if self.config.start_date:
                    start_dt = pd.to_datetime(self.config.start_date, format='%Y%m%d')
                    df = df[df['date'] >= start_dt]
                if self.config.end_date:
                    end_dt = pd.to_datetime(self.config.end_date, format='%Y%m%d')
                    df = df[df['date'] <= end_dt]
        
        if self.config.stock_code:
            normalized_code = normalize_user_code(self.config.stock_code)
            df = df[df['security_code'] == normalized_code].copy()
        
        if not self.config.include_repo:
            df = df[~df['trade_type'].isin(['repo_lend', 'repo_return'])].copy()
        
        if not self.config.include_dividend:
            df = df[~df['trade_type'].isin(['dividend', 'dividend_tax', 'stock_dividend'])].copy()
        
        return df
    
    def _get_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        summary = {
            'total_records': len(df),
            'date_range': (df['date'].min(), df['date'].max()) if len(df) > 0 else (None, None),
            'trade_count': len(df[df['trade_type'].isin(['buy', 'sell'])]),
            'buy_count': len(df[df['trade_type'] == 'buy']),
            'sell_count': len(df[df['trade_type'] == 'sell']),
            'unique_securities': df[df['security_code'] != '']['security_code'].nunique(),
            'mode': self.config.mode,
            'stock_code': self.config.stock_code,
            'start_date': self.config.start_date,
            'end_date': self.config.end_date,
        }
        
        # 如果是个股分析，添加个股专用统计
        if self.config.mode == 'stock' and self.config.stock_code:
            stock_stats = self._calculate_stock_stats(df)
            summary['stock_stats'] = stock_stats
        
        return summary
    
    def _calculate_stock_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        计算个股交易统计
        
        Returns:
            个股交易统计信息
        """
        # 包含买入、卖出和红股入账
        trade_df = df[df['trade_type'].isin(['buy', 'sell', 'stock_dividend'])].copy()
        
        if len(trade_df) == 0:
            return {}
        
        # 买入统计
        buy_df = trade_df[trade_df['trade_type'] == 'buy']
        total_buy_quantity = buy_df['quantity'].sum()
        total_buy_amount = buy_df['amount'].sum()
        
        # 卖出统计
        sell_df = trade_df[trade_df['trade_type'] == 'sell']
        total_sell_quantity = sell_df['quantity'].sum()
        total_sell_amount = sell_df['amount'].sum()
        
        # 红股入账统计
        dividend_df = trade_df[trade_df['trade_type'] == 'stock_dividend']
        total_dividend_quantity = dividend_df['quantity'].sum()
        
        # 当前持仓（包含红股）
        current_position = total_buy_quantity + total_dividend_quantity - total_sell_quantity
        
        # 盈亏计算（红股成本为0）
        realized_profit = total_sell_amount - total_buy_amount
        
        # 收益率（基于已实现盈亏）
        profit_rate = (realized_profit / total_buy_amount * 100) if total_buy_amount > 0 else 0
        
        # 获取股票名称
        stock_name = ''
        if len(trade_df) > 0:
            stock_name = trade_df.iloc[0]['security_name']
        
        # 检查是否有卖超情况
        has_short_selling = total_sell_quantity > (total_buy_quantity + total_dividend_quantity)
        
        # 计算持股平均时长
        avg_holding_days = self._calculate_avg_holding_days(trade_df)
        
        return {
            'stock_code': self.config.stock_code,
            'stock_name': stock_name,
            'total_buy_quantity': int(total_buy_quantity),
            'total_sell_quantity': int(total_sell_quantity),
            'total_dividend_quantity': int(total_dividend_quantity),
            'current_position': int(current_position),
            'total_buy_amount': float(total_buy_amount),
            'total_sell_amount': float(total_sell_amount),
            'realized_profit': float(realized_profit),
            'profit_rate': float(profit_rate),
            'buy_count': len(buy_df),
            'sell_count': len(sell_df),
            'dividend_count': len(dividend_df),
            'has_short_selling': has_short_selling,
            'short_selling_quantity': int(total_sell_quantity - total_buy_quantity - total_dividend_quantity) if has_short_selling else 0,
            'avg_holding_days': avg_holding_days,
            'trade_records': self._get_trade_records(trade_df),
        }
    
    def _get_trade_records(self, df: pd.DataFrame) -> List[Dict]:
        """
        获取交易记录列表（用于显示）
        """
        records = []
        for _, row in df.iterrows():
            record = {
                'date': row['date'],
                'trade_type': row['trade_type'],
                'quantity': int(row['quantity']),
                'price': float(row['price']),
                'amount': float(row['amount']),
            }
            records.append(record)
        return records
    
    def _calculate_avg_holding_days(self, df: pd.DataFrame) -> float:
        """
        计算持股平均时长（简化计算：从首次买入到最后卖出/现在的天数）
        """
        buy_df = df[df['trade_type'] == 'buy']
        sell_df = df[df['trade_type'] == 'sell']
        
        if len(buy_df) == 0:
            return 0
        
        first_buy_date = buy_df['date'].min()
        
        # 如果有卖出，用最后卖出日期；否则用当前日期
        if len(sell_df) > 0:
            last_date = sell_df['date'].max()
        else:
            last_date = pd.Timestamp.now()
        
        holding_days = (last_date - first_buy_date).days
        return max(0, holding_days)
    
    def _fetch_prices(self, positions: Dict[str, Dict]) -> Dict[str, float]:
        close_prices = {}

        for code in positions.keys():
            # 优先使用手动设置的价格
            if code in self.config.manual_prices:
                close_prices[code] = self.config.manual_prices[code]
                logger.info(f"使用手动价格 {code}: {close_prices[code]}")
                continue

            price = self.price_fetcher.get_latest_price(code)
            if price is not None:
                close_prices[code] = price
            else:
                close_prices[code] = 0
                logger.warning(f"无法获取股票 {code} 的价格")

        return close_prices
    
    def get_result(self) -> Optional[AnalysisResult]:
        return self._result
    
    def get_filtered_data(self) -> pd.DataFrame:
        if self._df is None:
            self._df = self.cleaner.clean()
        return self._apply_filters()
    
    def print_summary(self):
        if self._result is None:
            self.run_analysis()
        
        result = self._result
        
        print("\n" + "=" * 60)
        print("交易分析报告")
        print("=" * 60)
        
        print(f"\n分析模式: {result.config.mode}")
        if result.config.stock_code:
            print(f"股票代码: {result.config.stock_code}")
        if result.config.start_date:
            print(f"开始日期: {result.config.start_date}")
        if result.config.end_date:
            print(f"结束日期: {result.config.end_date}")
        
        print(f"\n数据概览:")
        print(f"  总记录数: {result.summary['total_records']}")
        if result.summary['date_range'][0]:
            print(f"  日期范围: {result.summary['date_range'][0].strftime('%Y-%m-%d')} ~ {result.summary['date_range'][1].strftime('%Y-%m-%d')}")
        print(f"  交易次数: {result.summary['trade_count']} (买入: {result.summary['buy_count']}, 卖出: {result.summary['sell_count']})")
        print(f"  涉及股票: {result.summary['unique_securities']} 只")
        
        if result.profit_summary:
            print(f"\n盈亏汇总:")
            print(f"  账户净转入: {result.profit_summary.net_transfer:,.2f} 元")
            print(f"  账户总资产: {result.profit_summary.total_assets:,.2f} 元")
            print(f"  总盈亏: {result.profit_summary.total_profit:,.2f} 元")
            print(f"  收益率: {result.profit_summary.profit_rate:.2f}%")
        
        if result.performance_metrics:
            print(f"\n绩效指标:")
            print(f"  总交易次数: {result.performance_metrics.total_trades}")
            print(f"  胜率: {result.performance_metrics.win_rate:.2f}%")
            print(f"  盈亏比: {result.performance_metrics.profit_loss_ratio:.2f}")
            print(f"  夏普比率: {result.performance_metrics.sharpe_ratio:.2f}")
            print(f"  最大回撤: {result.performance_metrics.max_drawdown:.2f}%")
        
        if result.positions:
            print(f"\n当前持仓:")
            for code, pos in result.positions.items():
                print(f"  {code} {pos['name']}: {pos['quantity']}股, 成本价: {pos['cost_price']:.2f}, 现价: {pos.get('close_price', 0):.2f}")
        
        print("\n" + "=" * 60)


def analyze(
    filepath: str,
    mode: str = 'full',
    stock_code: str = None,
    start_date: str = None,
    end_date: str = None,
    include_repo: bool = True,
    include_dividend: bool = True,
    manual_prices: Dict[str, float] = None,
) -> AnalysisResult:
    config = AnalysisConfig(
        mode=mode,
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        include_repo=include_repo,
        include_dividend=include_dividend,
        manual_prices=manual_prices or {}
    )
    
    analyzer = TradeAnalyzer(filepath, config)
    return analyzer.run_analysis()
