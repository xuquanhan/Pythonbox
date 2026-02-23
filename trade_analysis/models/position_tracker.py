import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class PositionLot:
    buy_date: datetime
    buy_price: float
    quantity: int
    remaining: int = field(init=False)

    def __post_init__(self):
        self.remaining = self.quantity


@dataclass
class TradeResult:
    security_code: str
    security_name: str
    buy_date: datetime
    sell_date: datetime
    buy_price: float
    sell_price: float
    quantity: int
    buy_amount: float
    sell_amount: float
    buy_fee: float
    sell_fee: float
    profit: float
    profit_rate: float
    holding_days: int


class PositionTracker:
    def __init__(self):
        self.positions: Dict[str, List[PositionLot]] = defaultdict(list)
        self.trades: List[TradeResult] = []
        self.stock_dividends: Dict[str, List[Tuple[datetime, int]]] = defaultdict(list)

    def process_trades(self, df: pd.DataFrame) -> List[TradeResult]:
        trade_df = df[df['trade_type'].isin(['buy', 'sell'])].copy()
        trade_df = trade_df.sort_values('date').reset_index(drop=True)

        for _, row in trade_df.iterrows():
            if row['trade_type'] == 'buy':
                self._process_buy(row)
            elif row['trade_type'] == 'sell':
                self._process_sell(row)

        return self.trades

    def process_stock_dividends(self, df: pd.DataFrame):
        dividend_df = df[df['trade_type'] == 'stock_dividend'].copy()

        for _, row in dividend_df.iterrows():
            code = row['security_code']
            quantity = int(row['quantity'])
            date = row['date']

            if code in self.positions and self.positions[code]:
                total_shares = sum(lot.remaining for lot in self.positions[code])
                if total_shares > 0:
                    bonus_ratio = quantity / total_shares
                    for lot in self.positions[code]:
                        bonus = int(lot.remaining * bonus_ratio)
                        lot.quantity += bonus
                        lot.remaining += bonus

            self.stock_dividends[code].append((date, quantity))

    def _process_buy(self, row: pd.Series):
        code = row['security_code']
        lot = PositionLot(
            buy_date=row['date'],
            buy_price=row['price'],
            quantity=int(row['quantity'])
        )
        self.positions[code].append(lot)

    def _process_sell(self, row: pd.Series):
        code = row['security_code']
        sell_quantity = int(row['quantity'])
        sell_price = row['price']
        sell_date = row['date']
        sell_amount = row['amount']
        sell_fee = row['total_fee']
        security_name = row['security_name']

        if code not in self.positions or not self.positions[code]:
            print(f"Warning: No position found for {code} on {sell_date}")
            return

        remaining_to_sell = sell_quantity
        total_buy_amount = 0.0
        total_buy_fee = 0.0
        earliest_buy_date = None

        while remaining_to_sell > 0 and self.positions[code]:
            lot = self.positions[code][0]

            if lot.remaining <= remaining_to_sell:
                sell_from_lot = lot.remaining
                total_buy_amount += sell_from_lot * lot.buy_price
                remaining_to_sell -= sell_from_lot

                if earliest_buy_date is None:
                    earliest_buy_date = lot.buy_date

                self.positions[code].pop(0)
            else:
                sell_from_lot = remaining_to_sell
                total_buy_amount += sell_from_lot * lot.buy_price
                lot.remaining -= sell_from_lot
                remaining_to_sell = 0

                if earliest_buy_date is None:
                    earliest_buy_date = lot.buy_date

        buy_fee = total_buy_amount * 0.0003
        buy_fee = max(buy_fee, 5.0)

        profit = sell_amount - total_buy_amount - sell_fee - buy_fee
        profit_rate = profit / total_buy_amount * 100 if total_buy_amount > 0 else 0

        holding_days = (sell_date - earliest_buy_date).days if earliest_buy_date else 0

        trade_result = TradeResult(
            security_code=code,
            security_name=security_name,
            buy_date=earliest_buy_date,
            sell_date=sell_date,
            buy_price=total_buy_amount / sell_quantity if sell_quantity > 0 else 0,
            sell_price=sell_price,
            quantity=sell_quantity,
            buy_amount=total_buy_amount,
            sell_amount=sell_amount,
            buy_fee=buy_fee,
            sell_fee=sell_fee,
            profit=profit,
            profit_rate=profit_rate,
            holding_days=holding_days
        )

        self.trades.append(trade_result)

    def get_current_positions(self) -> Dict[str, Dict[str, Any]]:
        result = {}
        for code, lots in self.positions.items():
            if lots:
                total_quantity = sum(lot.remaining for lot in lots)
                if total_quantity > 0:
                    weighted_cost = sum(lot.remaining * lot.buy_price for lot in lots) / total_quantity
                    earliest_date = min(lot.buy_date for lot in lots)
                    result[code] = {
                        'quantity': total_quantity,
                        'weighted_cost': weighted_cost,
                        'earliest_buy_date': earliest_date,
                        'lot_count': len([lot for lot in lots if lot.remaining > 0])
                    }
        return result

    def get_trade_summary(self) -> pd.DataFrame:
        if not self.trades:
            return pd.DataFrame()

        data = []
        for trade in self.trades:
            data.append({
                '证券代码': trade.security_code,
                '证券名称': trade.security_name,
                '买入日期': trade.buy_date.strftime('%Y-%m-%d'),
                '卖出日期': trade.sell_date.strftime('%Y-%m-%d'),
                '买入价格': round(trade.buy_price, 4),
                '卖出价格': round(trade.sell_price, 4),
                '数量': trade.quantity,
                '买入金额': round(trade.buy_amount, 2),
                '卖出金额': round(trade.sell_amount, 2),
                '买入费用': round(trade.buy_fee, 2),
                '卖出费用': round(trade.sell_fee, 2),
                '盈亏': round(trade.profit, 2),
                '盈亏率(%)': round(trade.profit_rate, 2),
                '持仓天数': trade.holding_days
            })

        return pd.DataFrame(data)

    def get_profit_by_security(self) -> pd.DataFrame:
        if not self.trades:
            return pd.DataFrame()

        summary = {}
        for trade in self.trades:
            code = trade.security_code
            if code not in summary:
                summary[code] = {
                    '证券代码': code,
                    '证券名称': trade.security_name,
                    '交易次数': 0,
                    '总买入金额': 0.0,
                    '总卖出金额': 0.0,
                    '总费用': 0.0,
                    '总盈亏': 0.0,
                    '盈利次数': 0,
                    '亏损次数': 0,
                    '最大盈利': 0.0,
                    '最大亏损': 0.0,
                }

            summary[code]['交易次数'] += 1
            summary[code]['总买入金额'] += trade.buy_amount
            summary[code]['总卖出金额'] += trade.sell_amount
            summary[code]['总费用'] += trade.buy_fee + trade.sell_fee
            summary[code]['总盈亏'] += trade.profit

            if trade.profit > 0:
                summary[code]['盈利次数'] += 1
                summary[code]['最大盈利'] = max(summary[code]['最大盈利'], trade.profit)
            else:
                summary[code]['亏损次数'] += 1
                summary[code]['最大亏损'] = min(summary[code]['最大亏损'], trade.profit)

        df = pd.DataFrame(list(summary.values()))
        if not df.empty:
            df['盈亏率(%)'] = round(df['总盈亏'] / df['总买入金额'] * 100, 2)
            df['胜率(%)'] = round(df['盈利次数'] / df['交易次数'] * 100, 2)
            df = df.sort_values('总盈亏', ascending=False)

        return df
