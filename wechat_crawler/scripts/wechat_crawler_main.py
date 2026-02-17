#!/usr/bin/env python3
"""
微信公众号爬虫主程序（API版本）
支持多公众号监控，自动登录，批量爬取
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from typing import List, Dict

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.wechat_auto_login_simple import WeChatAutoLoginSimple
from modules.wechat_api_crawler import WeChatAPICrawler
from modules.storage import DataStorage as Storage
from modules.word_exporter import WordExporter

# 配置文件路径
CONFIG_DIR = 'config'
ACCOUNTS_FILE = os.path.join(CONFIG_DIR, 'wechat_accounts.json')
SESSION_FILE = os.path.join(CONFIG_DIR, 'wechat_session.json')


def setup_logging():
    """设置日志"""
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/wechat_crawler.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def load_accounts() -> List[Dict]:
    """加载监控的公众号列表"""
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('accounts', [])
        except Exception as e:
            logging.error(f"加载公众号列表失败: {e}")
    return []


def save_accounts(accounts: List[Dict]):
    """保存监控的公众号列表"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        data = {
            'accounts': accounts,
            'last_updated': datetime.now().isoformat()
        }
        with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info("公众号列表已保存")
    except Exception as e:
        logging.error(f"保存公众号列表失败: {e}")


def display_accounts(accounts: List[Dict]):
    """显示当前监控的公众号列表"""
    print("\n" + "="*60)
    print("当前监控的公众号列表")
    print("="*60)
    
    if not accounts:
        print("暂无监控的公众号")
    else:
        for i, account in enumerate(accounts, 1):
            name = account.get('name', 'Unknown')
            fakeid = account.get('fakeid', '未获取')
            status = "✓" if fakeid else "✗"
            print(f"{i}. {name} [{status}]")
    
    print("="*60 + "\n")


def add_accounts(accounts: List[Dict]) -> List[Dict]:
    """
    添加新的公众号到监控列表
    支持逗号分隔添加多个
    """
    print("\n请输入要添加的公众号名称")
    print("提示：可以输入多个，用逗号分隔（例如：人民日报,新华社,央视新闻）")
    print("输入空行结束添加")
    
    while True:
        user_input = input("\n公众号名称: ").strip()
        
        if not user_input:
            break
        
        # 分割多个公众号
        names = [name.strip() for name in user_input.split(',') if name.strip()]
        
        if not names:
            print("未输入有效的公众号名称")
            continue
        
        # 添加到列表
        for name in names:
            # 检查是否已存在
            exists = any(a.get('name') == name for a in accounts)
            if exists:
                print(f"  [!] {name} 已在监控列表中")
            else:
                accounts.append({
                    'name': name,
                    'fakeid': None,
                    'added_time': datetime.now().isoformat()
                })
                print(f"  [+] {name} 已添加到监控列表")
        
        print(f"\n当前监控 {len(accounts)} 个公众号")
        
        # 询问是否继续添加
        cont = input("是否继续添加? (y/n): ").strip().lower()
        if cont != 'y':
            break
    
    return accounts


def get_fakeid_for_accounts(auto_login: WeChatAutoLoginSimple, accounts: List[Dict]) -> List[Dict]:
    """
    为没有fakeid的公众号获取fakeid（全自动API方式）
    """
    updated_accounts = []
    
    for account in accounts:
        name = account.get('name')
        fakeid = account.get('fakeid')
        
        if fakeid:
            print(f"  [✓] {name} 已有fakeid")
            updated_accounts.append(account)
            continue
        
        print(f"\n正在获取 {name} 的fakeid...")
        try:
            # 使用API方式自动获取fakeid
            fakeid = auto_login.get_fakeid_by_api(name)
            if fakeid:
                account['fakeid'] = fakeid
                print(f"  [✓] {name} 获取成功: {fakeid}")
            else:
                print(f"  [✗] {name} 获取失败")
        except Exception as e:
            print(f"  [✗] {name} 获取失败: {e}")
        
        updated_accounts.append(account)
        
        # 添加延迟，避免请求过快
        time.sleep(2)
    
    return updated_accounts


def crawl_accounts(api_crawler: WeChatAPICrawler, accounts: List[Dict], storage: Storage):
    """
    爬取所有公众号的文章（支持增量爬取）
    """
    all_articles = []
    
    for account in accounts:
        name = account.get('name')
        fakeid = account.get('fakeid')
        
        if not fakeid:
            print(f"\n[!] {name} 没有fakeid，跳过")
            continue
        
        print(f"\n{'='*60}")
        print(f"正在爬取: {name}")
        print(f"{'='*60}")
        
        try:
            # 获取该公众号的最新文章时间（用于增量爬取）
            latest_article = storage.get_latest_article_by_account(name)
            latest_time = latest_article.get('publish_time', '') if latest_article else ''
            
            if latest_time:
                print(f"[INFO] 数据库中最新的文章时间: {latest_time}")
                print(f"[INFO] 将只获取更新的文章...")
            
            # 获取文章
            articles = api_crawler.get_all_articles(fakeid, max_count=20)
            
            if articles:
                # 过滤已存在的文章（增量爬取）
                new_articles = []
                updated_articles = []
                
                for i, article in enumerate(articles):
                    url = article.get('url', '')
                    article['account_name'] = name
                    article['crawl_time'] = datetime.now().isoformat()
                    
                    # 检查是否已存在
                    existing_article = storage.get_article_by_url(url)
                    
                    # 总是获取文章详情，确保能更新图片信息
                    # 即使文章已有内容，也要重新获取以确保图片信息完整
                    should_fetch_detail = True
                    
                    if should_fetch_detail:
                        max_retries = 3
                        retry_count = 0
                        detail = None
                        
                        while retry_count < max_retries:
                            try:
                                if retry_count == 0:
                                    print(f"  正在获取第 {i+1}/{len(articles)} 篇文章详情...", end=' ')
                                else:
                                    print(f"  重试 ({retry_count+1}/{max_retries})...", end=' ')
                                    
                                detail = api_crawler.get_article_detail(url)
                                if detail:
                                    # 即使内容很短也保存，确保完整性
                                    if detail.get('content'):
                                        article['content'] = detail['content']
                                        # 保存正文中的图片列表
                                        if detail.get('content_images'):
                                            article['content_images'] = detail['content_images']
                                        print(f"✓ (内容长度: {len(detail['content'])})" )
                                        break
                                    else:
                                        retry_count += 1
                                        if retry_count >= max_retries:
                                            print("✗ (未能获取内容)")
                                        else:
                                            time.sleep(2)  # 等待2秒后重试
                                else:
                                    retry_count += 1
                                    if retry_count >= max_retries:
                                        print("✗ (未能获取详情)")
                                    else:
                                        time.sleep(2)  # 等待2秒后重试
                            except Exception as e:
                                retry_count += 1
                                if retry_count >= max_retries:
                                    print(f"✗ ({str(e)[:50]})")
                                    logging.warning(f"获取文章详情失败: {e}")
                                else:
                                    time.sleep(2)  # 等待2秒后重试
                    else:
                        # 使用数据库中已有的content
                        article['content'] = existing_article.get('content', '')
                        article['content_images'] = existing_article.get('content_images', [])
                        article['summary'] = existing_article.get('summary', '')
                    
                    # 检查是否已存在
                    if not storage.article_exists(article.get('url', '')):
                        new_articles.append(article)
                    else:
                        # 对已存在的文章也调用save_article，以便更新content字段
                        updated_articles.append(article)
                
                # 保存新文章
                if new_articles:
                    print(f"[✓] 成功获取 {len(articles)} 篇文章，其中 {len(new_articles)} 篇是新文章")
                    
                    all_articles.extend(new_articles)
                    
                    # 保存到数据库
                    for article in new_articles:
                        storage.save_article(article)
                    
                    print(f"[✓] 已保存 {len(new_articles)} 篇新文章到数据库")
                else:
                    print(f"[✓] 成功获取 {len(articles)} 篇文章，但没有新文章")
                
                # 更新已存在文章的content字段
                if updated_articles:
                    print(f"[INFO] 正在更新 {len(updated_articles)} 篇已存在文章的内容...")
                    for article in updated_articles:
                        storage.save_article(article)
                    print(f"[✓] 已更新 {len(updated_articles)} 篇文章的内容")
            else:
                print(f"[!] 未获取到文章")
                
        except Exception as e:
            print(f"[✗] 爬取失败: {e}")
            logging.error(f"爬取 {name} 失败: {e}")
    
    return all_articles


def export_data(storage: Storage, format_type: str = 'json'):
    """导出数据"""
    print(f"\n正在导出数据为 {format_type.upper()} 格式...")
    
    try:
        # 从数据库获取所有文章
        articles = storage.get_all_articles()
        
        if not articles:
            print("[!] 数据库中没有文章")
            return
        
        # 导出
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"wechat_articles_{timestamp}"
        
        if format_type == 'json':
            storage.export_to_json(articles, filename)
        elif format_type == 'csv':
            storage.export_to_csv(articles, filename)
        elif format_type == 'excel':
            storage.export_to_excel(articles, filename)
        
        print(f"[✓] 导出成功: data/processed/{filename}.{format_type}")
        
    except Exception as e:
        print(f"[✗] 导出失败: {e}")
        logging.error(f"导出数据失败: {e}")


def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("微信公众号爬虫（API版本）")
    print("="*60)
    
    # 1. 加载监控列表
    accounts = load_accounts()
    print(f"\n已加载 {len(accounts)} 个监控公众号")
    
    # 2. 显示当前列表
    display_accounts(accounts)
    
    # 3. 询问是否添加新公众号
    if accounts:
        choice = input("是否添加新的公众号? (y/n): ").strip().lower()
    else:
        choice = 'y'
    
    if choice == 'y':
        accounts = add_accounts(accounts)
        save_accounts(accounts)
        display_accounts(accounts)
    
    if not accounts:
        print("\n[!] 没有监控的公众号，程序退出")
        return
    
    # 4. 自动登录
    print("\n" + "="*60)
    print("开始自动登录")
    print("="*60)
    
    auto_login = WeChatAutoLoginSimple(SESSION_FILE)
    
    if not auto_login.login():
        print("\n[✗] 登录失败，程序退出")
        return
    
    print("\n[✓] 登录成功！")
    
    # 5. 获取fakeid
    print("\n" + "="*60)
    print("获取公众号fakeid")
    print("="*60)
    
    accounts = get_fakeid_for_accounts(auto_login, accounts)
    save_accounts(accounts)
    
    # 6. 创建API爬虫
    session_data = auto_login.get_session()
    api_crawler = WeChatAPICrawler(session_data)
    storage = Storage()
    
    # 7. 爬取文章
    print("\n" + "="*60)
    print("开始爬取文章")
    print("="*60)
    
    all_articles = crawl_accounts(api_crawler, accounts, storage)
    
    print(f"\n{'='*60}")
    print(f"爬取完成！共获取 {len(all_articles)} 篇文章")
    print(f"{'='*60}")
    
    # 8. 导出数据
    print("\n" + "="*60)
    print("数据导出")
    print("="*60)
    
    print("\n选择导出格式:")
    print("1. JSON")
    print("2. CSV")
    print("3. Excel")
    print("4. Word文档（按公众号分类）- 仅新文章")
    print("5. Word文档（按公众号分类）- 所有文章")
    print("6. 不导出")
    
    export_choice = input("\n请输入选项 (1-6): ").strip()
    
    if export_choice == '1':
        export_data(storage, 'json')
    elif export_choice == '2':
        export_data(storage, 'csv')
    elif export_choice == '3':
        export_data(storage, 'excel')
    elif export_choice == '4':
        # Word导出 - 仅新文章
        if all_articles:
            word_exporter = WordExporter()
            word_exporter.export_all_to_word(all_articles)
        else:
            print("[!] 没有新文章需要导出为Word")
    elif export_choice == '5':
        # Word导出 - 所有文章
        print("\n[INFO] 正在从数据库加载所有文章...")
        all_saved_articles = storage.get_all_articles()
        if all_saved_articles:
            print(f"[INFO] 共加载 {len(all_saved_articles)} 篇文章")
            word_exporter = WordExporter()
            word_exporter.export_all_to_word(all_saved_articles)
        else:
            print("[!] 数据库中没有文章")
    else:
        print("跳过导出")
    
    # 9. 关闭浏览器
    auto_login.close()
    
    print("\n" + "="*60)
    print("程序执行完成！")
    print("="*60)
    print(f"\n监控的公众号: {len(accounts)} 个")
    print(f"获取的文章数: {len(all_articles)} 篇")
    print(f"数据保存位置: data/db/wechat.db")
    print("\n提示：下次运行时会自动使用已保存的登录信息")
    print("      如果登录过期，程序会提示重新扫码登录")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
