import schedule
import time
import threading
import logging
import yaml
import os
from datetime import datetime
from typing import List, Dict, Optional

from modules.crawler import WeChatCrawler
from modules.storage import DataStorage

class Scheduler:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'check_interval': '1h',
            'max_workers': 3,
            'notify': False
        }
        
        self.crawler = WeChatCrawler()
        self.storage = DataStorage()
        self.logger = logging.getLogger(__name__)
        self.schedule_thread = None
        self.running = False
        self.accounts_config = self._load_accounts_config()
    
    def _load_accounts_config(self) -> Dict:
        """加载公众号配置"""
        config_path = 'config/accounts.yaml'
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                self.logger.error(f"加载配置失败: {str(e)}")
        return {'accounts': []}
    
    def _save_accounts_config(self):
        """保存公众号配置"""
        config_path = 'config/accounts.yaml'
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.accounts_config, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            self.logger.error(f"保存配置失败: {str(e)}")
    
    def check_updates(self):
        """检查所有公众号的更新"""
        try:
            self.logger.info("开始检查公众号更新...")
            
            # 从配置文件获取公众号列表
            accounts = self.accounts_config.get('accounts', [])
            if not accounts:
                self.logger.warning("没有公众号需要检查")
                return
            
            # 检查每个公众号
            for account in accounts:
                account_name = account.get('name')
                account_id = account.get('id')
                last_update = account.get('last_update', '')
                
                if not account_name:
                    continue
                
                self.logger.info(f"检查公众号: {account_name}")
                
                # 搜索公众号获取ID
                if not account_id:
                    account_info = self.crawler.search_account(account_name)
                    if account_info:
                        account_id = account_info.get('id')
                        account['id'] = account_id
                        self.logger.info(f"获取到公众号ID: {account_id}")
                
                # 检查新文章
                if account_id:
                    new_articles = self.crawler.check_new_articles(account_id, last_update)
                    
                    if new_articles:
                        self.logger.info(f"发现 {len(new_articles)} 篇新文章")
                        
                        # 爬取新文章内容
                        for article in new_articles:
                            if article.get('url'):
                                content_info = self.crawler.extract_article_content(article['url'])
                                if content_info:
                                    article.update(content_info)
                                    article['account_name'] = account_name
                                    article['account_id'] = account_id
                                    article['crawl_time'] = datetime.now().isoformat()
                        
                        # 保存新文章
                        self.storage.save_articles(new_articles)
                        
                        # 更新上次更新时间
                        account['last_update'] = datetime.now().isoformat()
                        self.storage.update_last_update(account_id)
                        self.storage.save_account({'name': account_name, 'id': account_id})
                    else:
                        self.logger.info(f"没有发现新文章")
                
                # 避免请求过快
                time.sleep(2)
            
            # 保存配置更新
            self._save_accounts_config()
            self.logger.info("公众号更新检查完成")
            
        except Exception as e:
            self.logger.error(f"检查更新失败: {str(e)}")
    
    def create_schedule(self):
        """创建定时任务"""
        interval = self.config['check_interval']
        
        if interval.endswith('h'):
            hours = int(interval[:-1])
            schedule.every(hours).hours.do(self.check_updates)
        elif interval.endswith('m'):
            minutes = int(interval[:-1])
            schedule.every(minutes).minutes.do(self.check_updates)
        elif interval.endswith('d'):
            days = int(interval[:-1])
            schedule.every(days).days.do(self.check_updates)
        else:
            self.logger.warning(f"无效的时间间隔: {interval}")
            schedule.every(1).hours.do(self.check_updates)
        
        self.logger.info(f"创建定时任务成功，每 {interval} 检查一次")
    
    def _run_schedule(self):
        """运行定时任务"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)
    
    def start_schedule(self):
        """启动定时任务"""
        if not self.running:
            self.running = True
            self.create_schedule()
            
            # 立即执行一次检查
            self.check_updates()
            
            # 启动线程
            self.schedule_thread = threading.Thread(target=self._run_schedule, daemon=True)
            self.schedule_thread.start()
            self.logger.info("定时任务已启动")
        else:
            self.logger.warning("定时任务已经在运行")
    
    def stop_schedule(self):
        """停止定时任务"""
        if self.running:
            self.running = False
            if self.schedule_thread:
                self.schedule_thread.join(timeout=5)
            self.logger.info("定时任务已停止")
        else:
            self.logger.warning("定时任务未运行")
    
    def add_account(self, name: str):
        """添加公众号"""
        accounts = self.accounts_config.get('accounts', [])
        
        # 检查是否已存在
        for account in accounts:
            if account.get('name') == name:
                self.logger.warning(f"公众号已存在: {name}")
                return False
        
        # 添加新公众号
        new_account = {
            'name': name,
            'id': '',
            'last_update': ''
        }
        accounts.append(new_account)
        self.accounts_config['accounts'] = accounts
        self._save_accounts_config()
        
        self.logger.info(f"添加公众号成功: {name}")
        return True
    
    def remove_account(self, name: str):
        """删除公众号"""
        accounts = self.accounts_config.get('accounts', [])
        
        new_accounts = [account for account in accounts if account.get('name') != name]
        
        if len(new_accounts) != len(accounts):
            self.accounts_config['accounts'] = new_accounts
            self._save_accounts_config()
            self.logger.info(f"删除公众号成功: {name}")
            return True
        else:
            self.logger.warning(f"公众号不存在: {name}")
            return False
    
    def list_accounts(self) -> List[Dict]:
        """列出所有公众号"""
        return self.accounts_config.get('accounts', [])
    
    def get_schedule_status(self) -> Dict:
        """获取调度器状态"""
        return {
            'running': self.running,
            'interval': self.config['check_interval'],
            'account_count': len(self.accounts_config.get('accounts', [])),
            'next_run': schedule.next_run().isoformat() if schedule.jobs else None
        }

# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    scheduler = Scheduler()
    
    # 测试添加公众号
    scheduler.add_account('人民日报')
    scheduler.add_account('新华社')
    
    # 测试检查更新
    scheduler.check_updates()
    
    # 测试启动定时任务
    print("启动定时任务，按Ctrl+C退出")
    scheduler.start_schedule()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop_schedule()
        print("定时任务已停止")
