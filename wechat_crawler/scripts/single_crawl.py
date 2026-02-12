#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单公众号爬取脚本

功能：
1. 从用户输入获取公众号名称
2. 爬取该公众号的所有历史文章
3. 保存到数据库
4. 可选导出为CSV/JSON/Excel
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

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/single_crawl.log'),
            logging.StreamHandler()
        ]
    )

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
            
            if export_path:
                logger.info(f"数据已导出到: {export_path}")
        
        # 显示统计信息
        stats = storage.get_statistics()
        logger.info(f"数据库统计: {stats}")
        
        return True
    except Exception as e:
        logger.error(f"爬取失败: {str(e)}")
        return False

def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='单公众号爬取脚本')
    parser.add_argument('--name', type=str, help='公众号名称')
    parser.add_argument('--export', choices=['csv', 'json', 'excel'], help='导出格式')
    args = parser.parse_args()
    
    # 获取公众号名称
    account_name = args.name
    if not account_name:
        account_name = input("请输入微信公众号名称: ").strip()
    
    if not account_name:
        logger.error("公众号名称不能为空")
        sys.exit(1)
    
    # 开始爬取
    logger.info(f"准备爬取公众号: {account_name}")
    success = crawl_single_account(account_name, args.export)
    
    if success:
        logger.info("爬取完成！")
        print(f"\n✅ 爬取成功！")
        print(f"公众号: {account_name}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        logger.error("爬取失败！")
        print(f"\n❌ 爬取失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
