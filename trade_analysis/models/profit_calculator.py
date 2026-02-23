import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import akshare as ak


@dataclass
class ProfitSummary:
    total_assets: float
    cash_balance: float
    repo_amount: float
    stock_market_value: float
    net_transfer: float
    total_profit: float
    profit_rate: float
    positions: Dict[str, Dict]


class ProfitCalculator:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def calculate_account_profit(self, close_prices: Dict[str, float] = None) -> ProfitSummary:
        net_transfer = self._calculate_net_transfer()
        
        cash_balance = self.df.iloc[-1]['balance']
        
        repo_amount = self._calculate_repo_amount()
        
        positions = self._calculate_positions()
        
        if close_prices:
            stock_market_value = self._calculate_market_value(positions, close_prices)
        else:
            stock_market_value = 0
            for code, pos in positions.items():
                stock_market_value += pos['quantity'] * pos.get('close_price', 0)
        
        total_assets = cash_balance + repo_amount + stock_market_value
        
        total_profit = total_assets - net_transfer
        profit_rate = (total_profit / net_transfer * 100) if net_transfer != 0 else 0
        
        return ProfitSummary(
            total_assets=total_assets,
            cash_balance=cash_balance,
            repo_amount=repo_amount,
            stock_market_value=stock_market_value,
            net_transfer=net_transfer,
            total_profit=total_profit,
            profit_rate=profit_rate,
            positions=positions
        )

    def _calculate_net_transfer(self) -> float:
        transfer_in = self.df[self.df['trade_type'] == 'transfer_in']['net_amount'].sum()
        transfer_out = abs(self.df[self.df['trade_type'] == 'transfer_out']['net_amount'].sum())
        return transfer_in - transfer_out

    def _calculate_repo_amount(self) -> float:
        last_date = self.df['date'].max()
        last_day_lend = self.df[(self.df['date'] == last_date) & (self.df['trade_type'] == 'repo_lend')]
        return last_day_lend['amount'].sum()

    def _calculate_positions(self) -> Dict[str, Dict]:
        # 包含买入、卖出和红股入账
        trade_df = self.df[self.df['trade_type'].isin(['buy', 'sell', 'stock_dividend'])].copy()

        positions = {}
        for code in trade_df['security_code'].unique():
            sec_df = trade_df[trade_df['security_code'] == code].sort_values('date')

            if len(sec_df) == 0:
                continue

            # 正确计算持仓：买入累计 + 红股累计 - 卖出累计
            buy_df = sec_df[sec_df['trade_type'] == 'buy']
            sell_df = sec_df[sec_df['trade_type'] == 'sell']
            dividend_df = sec_df[sec_df['trade_type'] == 'stock_dividend']

            total_buy_quantity = buy_df['quantity'].sum()
            total_sell_quantity = sell_df['quantity'].sum()
            total_dividend_quantity = dividend_df['quantity'].sum()
            current_position = total_buy_quantity + total_dividend_quantity - total_sell_quantity

            if current_position > 0:
                last_record = sec_df.iloc[-1]
                sec_name = last_record['security_name']

                total_buy_amount = buy_df['amount'].sum()
                total_sell_amount = sell_df['amount'].sum()
                total_buy_fee = buy_df['total_fee'].sum()
                total_sell_fee = sell_df['total_fee'].sum()

                # 成本计算：红股成本为0，不增加成本但增加股数
                cost_price = (total_buy_amount - total_sell_amount + total_buy_fee + total_sell_fee) / current_position

                positions[code] = {
                    'name': sec_name,
                    'quantity': int(current_position),
                    'cost_price': cost_price,
                    'close_price': 0
                }

        return positions

    def _calculate_market_value(self, positions: Dict[str, Dict], close_prices: Dict[str, float]) -> float:
        total_value = 0
        for code, pos in positions.items():
            close_price = close_prices.get(code, 0)
            pos['close_price'] = close_price
            total_value += pos['quantity'] * close_price
        return total_value

    def get_trade_statistics(self) -> Dict[str, Any]:
        trade_df = self.df[self.df['trade_type'].isin(['buy', 'sell'])].copy()
        
        buy_df = trade_df[trade_df['trade_type'] == 'buy']
        sell_df = trade_df[trade_df['trade_type'] == 'sell']
        
        total_buy_amount = buy_df['amount'].sum()
        total_sell_amount = sell_df['amount'].sum()
        total_buy_fee = buy_df['total_fee'].sum()
        total_sell_fee = sell_df['total_fee'].sum()
        
        realized_profit = total_sell_amount - total_buy_amount - total_buy_fee - total_sell_fee
        
        dividend = self.df[self.df['trade_type'] == 'dividend']['net_amount'].sum()
        dividend_tax = abs(self.df[self.df['trade_type'] == 'dividend_tax']['net_amount'].sum())
        interest = self.df[self.df['trade_type'] == 'interest']['net_amount'].sum()
        
        repo_profit = self._calculate_repo_profit()
        
        return {
            'total_buy_amount': total_buy_amount,
            'total_sell_amount': total_sell_amount,
            'total_buy_fee': total_buy_fee,
            'total_sell_fee': total_sell_fee,
            'realized_profit': realized_profit,
            'dividend': dividend,
            'dividend_tax': dividend_tax,
            'interest': interest,
            'repo_profit': repo_profit,
            'total_trades': len(buy_df) + len(sell_df),
            'buy_count': len(buy_df),
            'sell_count': len(sell_df),
        }

    def _calculate_repo_profit(self) -> float:
        lend_df = self.df[self.df['trade_type'] == 'repo_lend']
        return_df = self.df[self.df['trade_type'] == 'repo_return']
        
        lend_amount = lend_df['amount'].sum()
        return_amount = return_df['amount'].sum()
        lend_commission = lend_df['commission'].sum()
        
        unmatched = len(lend_df) - len(return_df)
        if unmatched > 0:
            lend_df_sorted = lend_df.sort_values('date')
            unmatched_amount = lend_df_sorted.tail(unmatched)['amount'].sum()
            matched_lend = lend_amount - unmatched_amount
        else:
            matched_lend = lend_amount
        
        return return_amount - matched_lend - lend_commission

    def get_monthly_summary(self) -> pd.DataFrame:
        df = self.df.copy()
        df['month'] = df['date'].dt.to_period('M')
        
        monthly = df.groupby('month').agg({
            'net_amount': 'sum',
        }).reset_index()
        
        monthly['month'] = monthly['month'].astype(str)
        monthly = monthly.rename(columns={'net_amount': '净发生额'})
        
        return monthly

    def get_yearly_summary(self) -> pd.DataFrame:
        df = self.df.copy()
        df['year'] = df['date'].dt.year
        
        yearly = df.groupby('year').agg({
            'net_amount': 'sum',
        }).reset_index()
        
        yearly = yearly.rename(columns={'net_amount': '净发生额'})
        
        return yearly
