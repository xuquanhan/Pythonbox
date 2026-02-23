#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.data_cleaner import DataCleaner
from models.profit_calculator import ProfitCalculator
from models.report_generator import ReportGenerator
from tools.visualization import Visualizer

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False


def get_close_prices(positions: dict, date_str: str = None) -> dict:
    if not HAS_AKSHARE:
        print("Warning: akshare not installed, cannot fetch close prices")
        return {}
    
    close_prices = {}
    for code in positions.keys():
        try:
            if code.startswith('688') or code.startswith('60'):
                df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=date_str.replace('-', '')[:8], end_date=date_str.replace('-', '')[:8], adjust="")
            elif code.startswith('159'):
                df = ak.fund_etf_hist_em(symbol=code, period='daily', start_date=date_str.replace('-', '')[:8], end_date=date_str.replace('-', '')[:8], adjust='')
            elif code.startswith('00') or code.startswith('30'):
                df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=date_str.replace('-', '')[:8], end_date=date_str.replace('-', '')[:8], adjust="")
            else:
                continue
            
            if not df.empty:
                close_prices[code] = df.iloc[-1]['收盘'] if '收盘' in df.columns else df.iloc[-1]['close']
        except Exception as e:
            print(f"Warning: Failed to get close price for {code}: {e}")
    
    return close_prices


def main():
    parser = argparse.ArgumentParser(description='股票交易分析工具')
    parser.add_argument('--input', '-i', type=str, required=True, help='输入CSV文件路径')
    parser.add_argument('--output', '-o', type=str, default='./output', help='输出目录')
    parser.add_argument('--format', '-f', type=str, choices=['console', 'excel', 'html', 'all'],
                        default='all', help='输出格式')
    parser.add_argument('--charts', '-c', action='store_true', help='生成图表')
    parser.add_argument('--fetch-prices', '-p', action='store_true', help='获取期末收盘价')

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误: 文件不存在 - {input_path}")
        sys.exit(1)

    print("=" * 60)
    print("股票交易分析工具")
    print("=" * 60)
    print(f"\n正在读取数据: {input_path}")

    cleaner = DataCleaner(str(input_path))
    cleaner.load_data()
    df = cleaner.clean()

    print(f"数据清洗完成，共 {len(df)} 条记录")

    summary = cleaner.get_summary()
    print(f"时间范围: {summary['date_range'][0].strftime('%Y-%m-%d')} 至 {summary['date_range'][1].strftime('%Y-%m-%d')}")

    print("\n正在计算账户盈亏...")
    calculator = ProfitCalculator(df)
    
    positions = calculator._calculate_positions()
    
    close_prices = {}
    if args.fetch_prices and positions:
        last_date = df['date'].max().strftime('%Y-%m-%d')
        print(f"\n正在获取 {last_date} 收盘价...")
        close_prices = get_close_prices(positions, last_date)
        for code, price in close_prices.items():
            print(f"  {code}: {price}")
    
    profit_summary = calculator.calculate_account_profit(close_prices)
    trade_stats = calculator.get_trade_statistics()

    print("\n" + "=" * 60)
    print("账户盈亏分析报告")
    print("=" * 60)
    
    print("\n【账户概况】")
    print(f"  账户净转入: {profit_summary.net_transfer:,.2f} 元")
    print(f"  现金余额: {profit_summary.cash_balance:,.2f} 元")
    print(f"  逆回购出借: {profit_summary.repo_amount:,.2f} 元")
    print(f"  持仓市值: {profit_summary.stock_market_value:,.2f} 元")
    print(f"  账户总资产: {profit_summary.total_assets:,.2f} 元")
    
    print("\n【盈亏汇总】")
    print(f"  账户总盈亏: {profit_summary.total_profit:,.2f} 元")
    print(f"  收益率: {profit_summary.profit_rate:.2f}%")
    
    print("\n【交易统计】")
    print(f"  总交易次数: {trade_stats['total_trades']} 次")
    print(f"  买入次数: {trade_stats['buy_count']} 次")
    print(f"  卖出次数: {trade_stats['sell_count']} 次")
    print(f"  买入金额: {trade_stats['total_buy_amount']:,.2f} 元")
    print(f"  卖出金额: {trade_stats['total_sell_amount']:,.2f} 元")
    print(f"  交易费用: {trade_stats['total_buy_fee'] + trade_stats['total_sell_fee']:,.2f} 元")
    print(f"  已实现盈亏: {trade_stats['realized_profit']:,.2f} 元")
    print(f"  股息收入: {trade_stats['dividend']:,.2f} 元")
    print(f"  红利税: {trade_stats['dividend_tax']:,.2f} 元")
    print(f"  利息收入: {trade_stats['interest']:,.2f} 元")
    print(f"  逆回购收益: {trade_stats['repo_profit']:,.2f} 元")
    
    if profit_summary.positions:
        print("\n【期末持仓】")
        for code, pos in profit_summary.positions.items():
            market_value = pos['quantity'] * pos.get('close_price', 0)
            print(f"  {code} {pos['name']}: {pos['quantity']}股, 成本价 {pos['cost_price']:.4f}, 收盘价 {pos.get('close_price', 0):.4f}, 市值 {market_value:,.2f}")

    report_data = {
        'summary': summary,
        'profit_summary': profit_summary,
        'trade_stats': trade_stats,
        'positions': profit_summary.positions,
        'monthly_summary': calculator.get_monthly_summary(),
        'yearly_summary': calculator.get_yearly_summary(),
    }

    report_gen = ReportGenerator(args.output)

    if args.format in ['excel', 'all']:
        print(f"\n正在生成Excel报告...")
        excel_path = report_gen.generate_excel_report(report_data)
        print(f"Excel报告已保存: {excel_path}")

    if args.format in ['html', 'all']:
        print(f"\n正在生成HTML报告...")
        html_path = report_gen.generate_html_report(report_data)
        print(f"HTML报告已保存: {html_path}")

    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
