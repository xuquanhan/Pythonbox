#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量爬取脚本

功能：
1. 从配置文件读取公众号列表
2. 批量爬取所有公众号
3. 启动定时任务检查更新
4. 管理公众号列表
"""

import sys
import os
import logging
import argparse
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.scheduler import Scheduler
from modules.storage import DataStorage

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/batch_crawl.log'),
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

def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 初始化调度器
    scheduler = Scheduler()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='批量爬取脚本')
    parser.add_argument('--action', choices=['list', 'add', 'remove', 'crawl', 'start', 'stats'], help='操作')
    args = parser.parse_args()
    
    # 根据命令行参数执行操作
    if args.action:
        if args.action == 'list':
            show_accounts(scheduler)
        elif args.action == 'add':
            add_account(scheduler)
        elif args.action == 'remove':
            remove_account(scheduler)
        elif args.action == 'crawl':
            batch_crawl(scheduler)
        elif args.action == 'start':
            start_schedule(scheduler)
        elif args.action == 'stats':
            show_statistics()
        return
    
    # 交互式菜单
    while True:
        print("\n=== 微信公众号爬取工具 ===")
        print("1. 显示公众号列表")
        print("2. 添加公众号")
        print("3. 删除公众号")
        print("4. 批量爬取所有公众号")
        print("5. 启动定时任务")
        print("6. 显示统计信息")
        print("7. 退出")
        
        choice = input("请输入操作序号: ").strip()
        
        if choice == '1':
            show_accounts(scheduler)
        elif choice == '2':
            add_account(scheduler)
        elif choice == '3':
            remove_account(scheduler)
        elif choice == '4':
            batch_crawl(scheduler)
        elif choice == '5':
            start_schedule(scheduler)
        elif choice == '6':
            show_statistics()
        elif choice == '7':
            print("退出工具...")
            break
        else:
            print("❌ 无效的选择，请重新输入")

if __name__ == "__main__":
    main()
