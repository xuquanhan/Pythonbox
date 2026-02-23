"""
交易分析工具

使用方法:
    python -m trade_analysis.main
    或直接在 IDE 中运行此文件

    程序会交互式询问用户需要进行什么操作
"""

import sys
from pathlib import Path
from typing import Dict

# 将项目根目录添加到 Python 路径，支持直接运行此文件
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
from datetime import datetime

import pandas as pd

from trade_analysis.db.database import DatabaseManager
from trade_analysis.services.analyzer import TradeAnalyzer, AnalysisConfig
from trade_analysis.services.price_fetcher import PriceFetcher
from trade_analysis.models.report_generator import ReportGenerator
from trade_analysis.models.data_cleaner import DataCleaner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = str(Path(__file__).parent / 'data' / 'trade_data.db')
DATA_RAW_PATH = str(Path(__file__).parent / 'data' / 'raw')
OUTPUT_PATH = str(Path(__file__).parent / 'output')


def get_user_input(prompt: str, options: list = None) -> str:
    if options:
        options_str = '/'.join(options)
        prompt = f"{prompt} ({options_str}): "

    while True:
        try:
            user_input = input(prompt).strip()
            if options:
                if user_input.lower() in [o.lower() for o in options]:
                    return user_input.lower()
                print(f"请输入: {options_str}")
            else:
                return user_input
        except EOFError:
            return ''


def select_file(directory: str = None) -> str:
    if directory is None:
        directory = DATA_RAW_PATH
    dir_path = Path(directory)
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"目录 {directory} 不存在，已创建")

    files = list(dir_path.glob('*.xls')) + list(dir_path.glob('*.xlsx')) + list(dir_path.glob('*.csv'))

    print(f"\n搜索目录: {directory}")
    print(f"找到 {len(files)} 个文件")

    if files:
        print("\n可用的清算文件:")
        for i, f in enumerate(files, 1):
            print(f"  {i}. {f.name}")
        print(f"  0. 手动输入文件路径")
        print(f"  r. 返回上级菜单")

        choice = get_user_input("\n请选择", [str(i) for i in range(0, len(files) + 1)] + ['r'])

        if choice == 'r':
            return ''

        if choice == '0':
            custom_path = get_user_input("请输入文件完整路径 (输入r返回): ")
            if custom_path.lower() == 'r':
                return ''
            if Path(custom_path).exists():
                return custom_path
            print("文件不存在")
            return ''

        try:
            return str(files[int(choice) - 1])
        except (ValueError, IndexError):
            return ''
    else:
        print("\n目录中没有清算文件")
        custom_path = get_user_input("请输入文件完整路径（输入r返回，回车跳过）: ")
        if custom_path.lower() == 'r':
            return ''
        if custom_path and Path(custom_path).exists():
            return custom_path
        return ''


def import_new_data(db: DatabaseManager) -> bool:
    print("\n" + "=" * 50)
    print("导入清算数据")
    print("=" * 50)

    db_last_date = db.get_last_date()
    db_record_count = db.get_record_count()

    if db_last_date:
        print(f"数据库已有 {db_record_count} 条记录")
        print(f"最新日期: {db_last_date}")
    else:
        print("数据库为空")

    print("\n提示: 在文件选择界面输入 0 可返回上级菜单")
    filepath = select_file()

    if not filepath:
        print("未选择文件，返回上级菜单")
        return False

    print(f"\n选择文件: {filepath}")

    try:
        cleaner = DataCleaner(filepath)
        df = cleaner.clean()

        print(f"\n文件解析成功:")
        print(f"  记录数: {len(df)}")
        print(f"  日期范围: {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")

        count = db.insert_trade_records(df)
        print(f"\n成功导入 {count} 条记录到数据库")
        return True

    except Exception as e:
        print(f"\n导入失败: {e}")
        return False


def check_and_prompt_data_sources(price_fetcher: PriceFetcher) -> bool:
    """
    检查数据源可用性，并提示用户启动软件
    
    Returns:
        True 如果至少有一个数据源可用，False 否则
    """
    print("\n" + "=" * 50)
    print("检查价格数据源...")
    print("=" * 50)
    
    # 按优先级检查数据源
    sources_to_check = [
        ('Wind', 'Wind 金融终端'),
        ('Bloomberg', 'Bloomberg 终端'),
        ('Refinitiv Workspace', 'Refinitiv Workspace')
    ]
    
    available_sources = price_fetcher.get_available_sources()
    
    for source_name, display_name in sources_to_check:
        if source_name in available_sources:
            print(f"\n正在测试 {display_name}...")
            # 尝试获取测试数据
            test_code = '000001'
            try:
                price = price_fetcher.get_latest_price(test_code)
                if price is not None and price > 0:
                    print(f"  ✅ {display_name} 连接成功 (获取到价格: {price})")
                    return True
                else:
                    print(f"  ❌ {display_name} 无法获取数据")
            except Exception as e:
                print(f"  ❌ {display_name} 连接失败: {e}")
            
            # 提示用户启动软件
            print(f"\n  请启动 {display_name} 软件")
            user_input = get_user_input(f"  是否已启动 {display_name}? (y/n)", ['y', 'n'])
            
            if user_input == 'y':
                # 重新初始化价格获取器
                print(f"  正在重新连接 {display_name}...")
                price_fetcher = PriceFetcher()
                try:
                    price = price_fetcher.get_latest_price(test_code)
                    if price is not None and price > 0:
                        print(f"  ✅ {display_name} 连接成功")
                        return True
                except:
                    pass
                print(f"  ❌ {display_name} 仍然无法连接，将尝试下一个数据源")
            else:
                print(f"  跳过 {display_name}，尝试下一个数据源")
    
    # 最后检查 AkShare
    if 'AkShare' in available_sources:
        print(f"\n正在测试 AkShare (免费数据源)...")
        try:
            price = price_fetcher.get_latest_price('000001')
            if price is not None and price > 0:
                print(f"  ✅ AkShare 可用 (获取到价格: {price})")
                return True
        except Exception as e:
            print(f"  ❌ AkShare 失败: {e}")
    
    print("\n⚠️ 警告: 所有数据源都不可用")
    print("  价格获取将失败，持仓市值计算可能不准确")
    return False


def get_all_traded_stocks(db: DatabaseManager) -> pd.DataFrame:
    """
    获取所有历史交易过的股票列表
    
    Returns:
        DataFrame 包含 security_code 和 security_name
    """
    try:
        df = db.get_all_trade_records()
        trade_df = df[df['trade_type'].isin(['buy', 'sell'])]
        unique_stocks = trade_df[['security_code', 'security_name']].drop_duplicates()
        unique_stocks = unique_stocks[unique_stocks['security_code'] != '']
        return unique_stocks.sort_values('security_code')
    except Exception as e:
        print(f"\n无法获取股票列表: {e}")
        return pd.DataFrame()


def check_price_completeness(db: DatabaseManager) -> tuple:
    """
    检查数据库中价格数据的完整性
    
    Returns:
        (is_complete, missing_stocks)
        is_complete: True 如果所有持仓股票都有价格数据
        missing_stocks: 缺失价格的股票代码列表
    """
    print("\n" + "=" * 50)
    print("检查价格数据完整性...")
    print("=" * 50)
    
    try:
        # 获取所有交易记录
        df = db.get_all_trade_records()
        
        # 获取数据库中已有的价格
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT security_code FROM daily_prices")
        stocks_with_prices = set(row[0] for row in cursor.fetchall())
        conn.close()
        
        # 获取所有交易过的股票
        trade_stocks = set(df[df['trade_type'].isin(['buy', 'sell'])]['security_code'].unique())
        
        # 找出缺失价格的股票
        missing_stocks = trade_stocks - stocks_with_prices
        
        print(f"\n交易过的股票: {len(trade_stocks)} 只")
        print(f"有价格数据的股票: {len(stocks_with_prices)} 只")
        print(f"缺失价格的股票: {len(missing_stocks)} 只")
        
        if missing_stocks:
            print(f"\n缺失价格的股票:")
            for code in sorted(missing_stocks):
                print(f"  - {code}")
            return False, list(missing_stocks)
        else:
            print(f"\n✅ 所有股票都有价格数据")
            return True, []
            
    except Exception as e:
        print(f"\n检查价格完整性失败: {e}")
        return False, []


def get_stock_code_with_suggestions(db: DatabaseManager) -> str:
    """
    获取股票代码，并显示数据库中已有的股票列表
    如果输入的代码没有历史交易，提示重新输入
    
    Returns:
        6位股票代码，如果用户取消返回 None
    """
    # 获取数据库中已有的股票列表
    unique_stocks = get_all_traded_stocks(db)
    
    if len(unique_stocks) > 0:
        print(f"\n数据库中已有的股票 ({len(unique_stocks)} 只):")
        # 完整显示所有股票
        for _, row in unique_stocks.iterrows():
            print(f"  {row['security_code']} {row['security_name']}")
    else:
        print("\n数据库中没有交易记录")
    
    # 要求用户输入6位完整代码
    while True:
        code = get_user_input("\n请输入6位股票代码 (如 002050，输入0返回): ")
        code = code.strip()
        
        # 检查是否返回
        if code == '0':
            return None
        
        # 验证是否为6位数字
        if len(code) != 6 or not code.isdigit():
            print(f"  ❌ 代码格式错误: '{code}' 不是6位数字")
            print(f"  提示: 请输入6位数字代码，如 002050、600519 等")
            continue
        
        # 检查该代码是否有历史交易
        if code not in unique_stocks['security_code'].values:
            print(f"  ❌ 代码 {code} 没有历史交易记录")
            print(f"  提示: 请从上面的列表中选择有交易记录的股票")
            continue
        
        return code


def run_analysis_from_file(config: AnalysisConfig, price_fetcher: PriceFetcher):
    """从文件进行分析"""
    filepath = select_file()

    if not filepath:
        print("未选择文件")
        return False

    print(f"\n选择文件: {filepath}")

    try:
        analyzer = TradeAnalyzer(filepath, config)
        result = analyzer.run_analysis()
        return result
    except Exception as e:
        print(f"\n分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_analysis_from_db(db: DatabaseManager, config: AnalysisConfig, price_fetcher: PriceFetcher):
    """从数据库进行分析"""
    record_count = db.get_record_count()
    if record_count == 0:
        print("\n数据库为空，请先导入数据")
        return False

    print(f"\n数据库记录数: {record_count}")
    last_date = db.get_last_date()
    print(f"最新日期: {last_date}")

    try:
        df = db.get_all_trade_records()
        print(f"数据日期范围: {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")

        analyzer = TradeAnalyzer.from_dataframe(df, config)
        result = analyzer.run_analysis()
        return result
    except Exception as e:
        print(f"\n分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_analysis(db: DatabaseManager):
    print("\n" + "=" * 50)
    print("交易分析")
    print("=" * 50)

    print("\n选择数据源:")
    print("  1. 分析清算文件")
    print("  2. 分析数据库中的数据")
    print("  0. 返回上级菜单")

    source_choice = get_user_input("\n请选择", ['0', '1', '2'])
    
    if source_choice == '0':
        return

    print("\n选择分析模式:")
    print("  1. 全量分析")
    print("  2. 个股分析")
    print("  3. 时间段分析")
    print("  4. 组合分析（个股+时间段）")
    print("  0. 返回上级菜单")

    mode_choice = get_user_input("\n请选择", ['0', '1', '2', '3', '4'])
    
    if mode_choice == '0':
        return

    mode_map = {'1': 'full', '2': 'stock', '3': 'period', '4': 'combined'}
    mode = mode_map.get(mode_choice, 'full')

    stock_code = None
    start_date = None
    end_date = None

    if mode in ['stock', 'combined']:
        stock_code = get_stock_code_with_suggestions(db)
        if stock_code is None:  # 用户取消
            return

    if mode in ['period', 'combined']:
        start_date = get_user_input("请输入开始日期 (YYYYMMDD，或输入0返回): ")
        if start_date == '0':
            return
        end_date = get_user_input("请输入结束日期 (YYYYMMDD，或输入0返回): ")
        if end_date == '0':
            return

    manual_prices = {}
    print("\n是否手动设置股票价格? (用于计算持仓市值)")
    print("  y. 是")
    print("  n. 否")
    print("  0. 返回上级菜单")
    
    price_choice = get_user_input("请选择", ['0', 'y', 'n'])
    if price_choice == '0':
        return
    elif price_choice == 'y':
        while True:
            price_input = get_user_input("输入格式: 代码=价格 (如 002050=52.39)，回车结束，输入0返回: ")
            if price_input == '0':
                return
            if not price_input:
                break
            if '=' in price_input:
                try:
                    code, price = price_input.split('=')
                    manual_prices[code.strip()] = float(price.strip())
                except ValueError:
                    print("  ❌ 格式错误，请使用: 代码=价格")

    config = AnalysisConfig(
        mode=mode,
        stock_code=stock_code,
        start_date=start_date,
        end_date=end_date,
        manual_prices=manual_prices
    )

    # 初始化价格获取器（无论是否需要获取价格，都需要初始化）
    print("\n初始化价格获取器...")
    price_fetcher = PriceFetcher()
    
    # 检查价格数据完整性
    is_complete, missing_stocks = check_price_completeness(db)
    
    # 如果价格数据完整，直接使用数据库价格进行分析
    if is_complete:
        print("\n✅ 价格数据完整，将使用数据库中的历史价格进行分析")
    else:
        # 价格数据不完整，需要获取
        print(f"\n⚠️ 数据库中缺少 {len(missing_stocks)} 只股票的价格数据")
        print("\n是否获取缺失的价格数据?")
        print("  y. 是，启动数据源获取")
        print("  n. 否，继续分析（缺失的价格将按0计算）")
        print("  0. 返回上级菜单")
        
        get_price_choice = get_user_input("请选择", ['0', 'y', 'n'])
        if get_price_choice == '0':
            return
        elif get_price_choice == 'y':
            # 定义用户提示回调函数
            def user_prompt_callback(source_name, error):
                print(f"\n{'='*60}")
                print(f"⚠️ {source_name} 获取价格失败")
                print(f"错误: {error}")
                print(f"{'='*60}")
                print(f"\n请启动 {source_name} 终端软件")
                print("启动完成后请输入:")
                print("  y - 已启动，继续尝试")
                print("  n - 跳过，尝试下一个数据源")
                
                while True:
                    user_input = input(f"\n是否已启动 {source_name}? (y/n): ").strip().lower()
                    if user_input in ['y', 'n']:
                        return user_input == 'y'
                    print("请输入 y 或 n")
            
            # 先确定哪个数据源可用
            print(f"\n正在确定可用数据源...")
            print("  优先级: Wind → Bloomberg → Workspace\n")
            
            selected_source = None
            sources = [
                ('Wind', price_fetcher._wind_available, price_fetcher._init_wind),
                ('Bloomberg', price_fetcher._bloomberg_available, price_fetcher._init_bloomberg),
                ('Refinitiv Workspace', price_fetcher._workspace_available, price_fetcher._init_workspace),
            ]
            
            for source_name, is_available, init_func in sources:
                if is_available:
                    selected_source = source_name
                    print(f"✅ {source_name} 已可用")
                    break
                else:
                    # 尝试提示用户启动
                    print(f"\n⚠️ {source_name} 未连接")
                    retry = user_prompt_callback(source_name, f"{source_name} 未启动")
                    if retry:
                        init_func()
                        # 重新检查是否可用
                        if source_name == 'Wind' and price_fetcher._wind_available:
                            selected_source = source_name
                            print(f"✅ {source_name} 现在可用")
                            break
                        elif source_name == 'Bloomberg' and price_fetcher._bloomberg_available:
                            selected_source = source_name
                            print(f"✅ {source_name} 现在可用")
                            break
                        elif source_name == 'Refinitiv Workspace' and price_fetcher._workspace_available:
                            selected_source = source_name
                            print(f"✅ {source_name} 现在可用")
                            break
                    else:
                        print(f"  跳过 {source_name}，尝试下一个数据源")
            
            if not selected_source:
                print("\n❌ 没有可用的数据源")
                print("  将使用数据库中的历史价格或按0计算")
            else:
                print(f"\n使用 {selected_source} 获取 {len(missing_stocks)} 只股票的价格...")
                
                fetched_prices = {}
                failed_stocks = []
                
                for code in missing_stocks:
                    print(f"\n获取 {code} 的价格...")
                    # 使用已确定的数据源获取价格，不再重复询问
                    price = price_fetcher.get_price_with_fallback(
                        code, 
                        user_prompt_callback,
                        preferred_source=selected_source
                    )
                    
                    if price is not None and price > 0:
                        fetched_prices[code] = price
                        print(f"  ✅ 成功获取: {price:.2f}元")
                    else:
                        failed_stocks.append(code)
                        print(f"  ❌ 无法获取")
                
                # 保存获取到的价格到数据库
                if fetched_prices:
                    print(f"\n💾 保存 {len(fetched_prices)} 只股票的价格到数据库...")
                    from datetime import datetime
                    prices_to_save = []
                    for code, price in fetched_prices.items():
                        prices_to_save.append({
                            'date': datetime.now().strftime('%Y%m%d'),
                            'security_code': code,
                            'close_price': price
                        })
                    
                    # 调用保存方法
                    try:
                        saved_count = db.save_daily_prices(prices_to_save)
                        print(f"  ✅ 成功保存 {saved_count} 条价格记录")
                    except Exception as e:
                        print(f"  ❌ 保存失败: {e}")
                
                if failed_stocks:
                    print(f"\n⚠️ 以下 {len(failed_stocks)} 只股票无法获取价格:")
                    for code in failed_stocks:
                        print(f"  - {code}")
                    print("\n这些股票将使用数据库中的历史价格或按0计算")

    # 根据数据源选择进行分析
    if source_choice == '1':
        result = run_analysis_from_file(config, price_fetcher)
    else:
        result = run_analysis_from_db(db, config, price_fetcher)

    if result is None or result is False:
        return

    # 打印分析结果
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

    # 如果是个股分析，显示专门的统计
    if result.config.mode == 'stock' and 'stock_stats' in result.summary:
        stats = result.summary['stock_stats']
        print(f"\n{'='*60}")
        print("个股交易统计")
        print(f"{'='*60}")
        print(f"  股票名称: {stats.get('stock_name', '')}")
        print(f"\n  交易股数统计:")
        print(f"    历史总买入: {stats['total_buy_quantity']:,}股 ({stats['buy_count']}次)")
        if stats['total_dividend_quantity'] > 0:
            print(f"    红股入账:   {stats['total_dividend_quantity']:,}股 ({stats['dividend_count']}次)")
        print(f"    历史总卖出: {stats['total_sell_quantity']:,}股 ({stats['sell_count']}次)")
        
        # 检查是否有卖超情况
        if stats.get('has_short_selling'):
            print(f"    当前持仓:   {stats['current_position']:,}股 ⚠️ 数据异常")
            print(f"\n  ⚠️ 警告: 卖出数量超过买入数量 {stats['short_selling_quantity']}股")
            print(f"     可能原因: 历史数据不完整或之前已有持仓未导入")
        else:
            print(f"    当前持仓:   {stats['current_position']:,}股")
        
        print(f"\n  持股时长:")
        print(f"    平均持股天数: {stats['avg_holding_days']:.0f}天")
        
        print(f"\n  交易金额统计:")
        print(f"    总买入金额: {stats['total_buy_amount']:,.2f}元")
        print(f"    总卖出金额: {stats['total_sell_amount']:,.2f}元")
        print(f"\n  盈亏统计:")
        profit = stats['realized_profit']
        profit_rate = stats['profit_rate']
        status = "盈利" if profit > 0 else "亏损" if profit < 0 else "持平"
        print(f"    已实现盈亏: {profit:,.2f}元 ({status})")
        print(f"    收益率: {profit_rate:+.2f}%")
        
        # 显示详细交易记录
        if 'trade_records' in stats and stats['trade_records']:
            print(f"\n{'='*70}")
            print("详细交易记录")
            print(f"{'='*70}")
            # 使用 str.format 来确保对齐
            header = "{:<12} {:<10} {:>10} {:>12} {:>14}".format(
                "日期", "类型", "数量(股)", "价格(元)", "金额(元)"
            )
            print(header)
            print("-" * 70)
            
            for record in stats['trade_records']:
                date_str = record['date'].strftime('%Y-%m-%d') if hasattr(record['date'], 'strftime') else str(record['date'])[:10]
                trade_type_map = {
                    'buy': '买入',
                    'sell': '卖出',
                    'stock_dividend': '红股入账'
                }
                type_str = trade_type_map.get(record['trade_type'], record['trade_type'])
                
                # 使用 str.format 确保对齐
                line = "{:<12} {:<10} {:>10,} {:>12.2f} {:>14.2f}".format(
                    date_str,
                    type_str,
                    record['quantity'],
                    record['price'],
                    record['amount']
                )
                print(line)
    else:
        # 全量分析显示原有统计
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

        # 显示详细持仓
        if result.positions:
            print(f"\n{'='*60}")
            print("持仓详情")
            print(f"{'='*60}")
            for code, pos in result.positions.items():
                market_value = pos['quantity'] * pos.get('close_price', 0)
                print(f"  {code} {pos['name']}: {pos['quantity']}股")
                print(f"    成本价: {pos['cost_price']:.2f}元, 现价: {pos.get('close_price', 0):.2f}元")
                print(f"    市值: {market_value:,.2f}元")

    print("\n" + "=" * 60)

    # 生成报告
    print("\n生成报告...")
    report_gen = ReportGenerator(OUTPUT_PATH)
    output_files = report_gen.generate_from_result(result, formats=['excel', 'html'])

    if output_files.get('excel'):
        print(f"Excel报告: {output_files['excel']}")
    if output_files.get('html'):
        print(f"HTML报告: {output_files['html']}")


def view_data_summary(db: DatabaseManager):
    print("\n" + "=" * 50)
    print("数据摘要")
    print("=" * 50)

    record_count = db.get_record_count()
    last_date = db.get_last_date()

    print(f"\n数据库信息:")
    print(f"  总记录数: {record_count}")
    print(f"  最新日期: {last_date if last_date else '无数据'}")

    if record_count > 0:
        df = db.get_all_trade_records()
        print(f"\n数据详情:")
        print(f"  日期范围: {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
        print(f"  买入记录: {len(df[df['trade_type'] == 'buy'])}")
        print(f"  卖出记录: {len(df[df['trade_type'] == 'sell'])}")
        print(f"  涉及股票: {df[df['security_code'] != '']['security_code'].nunique()} 只")


def clear_database(db: DatabaseManager):
    print("\n  y. 是")
    print("  n. 否")
    confirm = get_user_input("确认清空数据库?", ['y', 'n'])
    if confirm == 'y':
        db.clear_all_data()
        print("数据库已清空")


def main():
    print("\n" + "=" * 50)
    print("交易分析工具")
    print("=" * 50)

    db = DatabaseManager(DB_PATH)

    while True:
        print("\n请选择操作:")
        print("  1. 导入清算数据到数据库")
        print("  2. 进行交易分析")
        print("  3. 查看数据库摘要")
        print("  4. 清空数据库")
        print("  0. 退出")

        choice = get_user_input("\n请选择", ['0', '1', '2', '3', '4'])

        if choice == '0':
            print("\n再见!")
            break
        elif choice == '1':
            import_new_data(db)
        elif choice == '2':
            run_analysis(db)
        elif choice == '3':
            view_data_summary(db)
        elif choice == '4':
            clear_database(db)


if __name__ == '__main__':
    main()
