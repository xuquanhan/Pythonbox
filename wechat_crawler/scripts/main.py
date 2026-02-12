#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号爬取工具主脚本

功能：
1. 单公众号爬取
2. 批量爬取
3. 公众号管理
4. 定时任务
5. 数据导出
"""

import sys
import os
import logging
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.crawler import WeChatCrawler
from modules.storage import DataStorage
from modules.scheduler import Scheduler

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/main.log'),
            logging.StreamHandler()
        ]
    )

def show_accounts(scheduler):
    """显示公众号列表"""
    accounts = scheduler.list_accounts()
    print("\n📋 公众号列表:")
    print("-" * 60)
    if not accounts:
        print("  暂无公众号")
    else:
        for i, account in enumerate(accounts, 1):
            name = account.get('name')
            account_id = account.get('id', 'N/A')
            last_update = account.get('last_update', '从未更新')
            print(f"{i}. {name}")
            print(f"   ID: {account_id}")
            print(f"   上次更新: {last_update}")
            print("-" * 60)

def add_account(scheduler):
    """添加公众号"""
    name = input("请输入要添加的公众号名称: ").strip()
    if name:
        success = scheduler.add_account(name)
        if success:
            print(f"✅ 添加成功！")
        else:
            print(f"❌ 添加失败，可能已存在")
    else:
        print("❌ 公众号名称不能为空")

def remove_account(scheduler):
    """删除公众号"""
    name = input("请输入要删除的公众号名称: ").strip()
    if name:
        success = scheduler.remove_account(name)
        if success:
            print(f"✅ 删除成功！")
        else:
            print(f"❌ 删除失败，公众号不存在")
    else:
        print("❌ 公众号名称不能为空")

def start_schedule(scheduler):
    """启动定时任务"""
    print("启动定时任务...")
    scheduler.start_schedule()
    print("✅ 定时任务已启动")
    print("按 Ctrl+C 退出...")
    
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop_schedule()
        print("\n✅ 定时任务已停止")

def batch_crawl(scheduler):
    """批量爬取所有公众号"""
    print("开始批量爬取...")
    scheduler.check_updates()
    print("✅ 批量爬取完成")

def show_statistics():
    """显示统计信息"""
    storage = DataStorage()
    stats = storage.get_statistics()
    print("\n📊 统计信息:")
    print("-" * 60)
    print(f"公众号数量: {stats.get('account_count', 0)}")
    print(f"文章数量: {stats.get('article_count', 0)}")
    print(f"最近更新: {stats.get('last_update', '从未更新')}")
    print(f"数据库路径: {stats.get('db_path', 'N/A')}")
    print("-" * 60)

def crawl_single_account(account_name, export_format=None):
    """爬取单个公众号"""
    logger = logging.getLogger(__name__)
    logger.info(f"开始爬取公众号: {account_name}")
    
    # 初始化爬虫和存储
    crawler = WeChatCrawler()
    storage = DataStorage()
    
    try:
        # 爬取公众号
        articles = crawler.crawl_account(account_name)
        
        if not articles:
            logger.warning(f"未获取到 {account_name} 的文章")
            return False
        
        logger.info(f"成功获取 {len(articles)} 篇文章")
        
        # 保存到数据库
        storage.save_articles(articles)
        
        # 导出数据
        if export_format:
            export_path = None
            if export_format == 'csv':
                export_path = storage.export_to_csv(account_name)
            elif export_format == 'json':
                export_path = storage.export_to_json(account_name)
            elif export_format == 'excel':
                export_path = storage.export_to_excel(account_name)
            elif export_format == 'word':
                export_path = storage.export_to_word(account_name)
            
            if export_path:
                logger.info(f"数据已导出到: {export_path}")
        
        # 显示统计信息
        stats = storage.get_statistics()
        logger.info(f"数据库统计: {stats}")
        
        return True
    except Exception as e:
        logger.error(f"爬取失败: {str(e)}")
        return False

def batch_add_accounts(scheduler):
    """批量添加公众号"""
    print("\n📋 批量添加公众号")
    print("-" * 60)
    print("请输入公众号名称，输入 'exit' 或留空退出")
    print("-" * 60)
    
    added_count = 0
    
    while True:
        name = input("公众号名称: ").strip()
        
        if not name or name.lower() == 'exit':
            break
        
        success = scheduler.add_account(name)
        if success:
            added_count += 1
            print(f"✅ 添加成功！")
        else:
            print(f"❌ 添加失败，可能已存在")
    
    if added_count > 0:
        print(f"\n✅ 批量添加完成，共添加了 {added_count} 个公众号")
    else:
        print("\nℹ️  未添加任何公众号")

def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='微信公众号爬取工具')
    parser.add_argument('--action', choices=['list', 'add', 'batch_add', 'remove', 'crawl', 'start', 'stats', 'single'], help='操作')
    parser.add_argument('--name', type=str, help='公众号名称')
    parser.add_argument('--export', choices=['csv', 'json', 'excel', 'word'], help='导出格式')
    args = parser.parse_args()
    
    # 根据命令行参数执行操作
    if args.action:
        if args.action == 'list':
            scheduler = Scheduler()
            show_accounts(scheduler)
        elif args.action == 'add':
            scheduler = Scheduler()
            add_account(scheduler)
        elif args.action == 'batch_add':
            scheduler = Scheduler()
            batch_add_accounts(scheduler)
        elif args.action == 'remove':
            scheduler = Scheduler()
            remove_account(scheduler)
        elif args.action == 'crawl':
            scheduler = Scheduler()
            batch_crawl(scheduler)
        elif args.action == 'start':
            scheduler = Scheduler()
            start_schedule(scheduler)
        elif args.action == 'stats':
            show_statistics()
        elif args.action == 'single':
            if args.name:
                success = crawl_single_account(args.name, args.export)
                if success:
                    print(f"\n✅ 爬取成功！")
                    print(f"公众号: {args.name}")
                    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print(f"\n❌ 爬取失败！")
                    sys.exit(1)
            else:
                print("❌ 请指定公众号名称: --name 公众号名称")
                sys.exit(1)
        return
    
    # 交互式菜单
    while True:
        print("\n=== 微信公众号爬取工具 ===")
        print("1. 单公众号爬取")
        print("2. 批量爬取所有公众号")
        print("3. 显示公众号列表")
        print("4. 添加公众号")
        print("5. 批量添加公众号")
        print("6. 删除公众号")
        print("7. 启动定时任务")
        print("8. 显示统计信息")
        print("9. 退出")
        
        choice = input("请输入操作序号: ").strip()
        
        if choice == '1':
            name = input("请输入公众号名称: ").strip()
            if name:
                export_choice = input("是否导出数据？(y/n): ").strip().lower()
                export_format = None
                if export_choice == 'y':
                    print("请选择导出格式:")
                    print("1. CSV")
                    print("2. JSON")
                    print("3. Excel")
                    print("4. Word")
                    format_choice = input("请输入格式序号: ").strip()
                    if format_choice == '1':
                        export_format = 'csv'
                    elif format_choice == '2':
                        export_format = 'json'
                    elif format_choice == '3':
                        export_format = 'excel'
                    elif format_choice == '4':
                        export_format = 'word'
                success = crawl_single_account(name, export_format)
                if success:
                    print(f"✅ 爬取成功！")
                else:
                    print(f"❌ 爬取失败！")
            else:
                print("❌ 公众号名称不能为空")
        elif choice == '2':
            scheduler = Scheduler()
            batch_crawl(scheduler)
        elif choice == '3':
            scheduler = Scheduler()
            show_accounts(scheduler)
        elif choice == '4':
            scheduler = Scheduler()
            add_account(scheduler)
        elif choice == '5':
            scheduler = Scheduler()
            batch_add_accounts(scheduler)
        elif choice == '6':
            scheduler = Scheduler()
            remove_account(scheduler)
        elif choice == '7':
            scheduler = Scheduler()
            start_schedule(scheduler)
        elif choice == '8':
            show_statistics()
        elif choice == '9':
            print("退出工具...")
            break
        else:
            print("❌ 无效的选择，请重新输入")

if __name__ == "__main__":
    main()