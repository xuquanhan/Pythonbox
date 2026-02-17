#!/usr/bin/env python3
"""
Wind服务号专属爬虫脚本
专门获取Wind服务号推送的定制新闻内容，便于后续操作
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 检查依赖
def check_dependencies():
    """检查必要的依赖"""
    try:
        from modules.wechat_auto_login_simple import WeChatAutoLoginSimple
        from modules.wechat_api_crawler import WeChatAPICrawler
        from modules.storage import DataStorage
        return True
    except ImportError as e:
        logger.error(f"导入依赖失败: {e}")
        return False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/wind_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 检查依赖
if not check_dependencies():
    logger.error("依赖检查失败，脚本可能无法正常运行")
    # 尝试继续运行，因为可能只是部分依赖缺失

# 导入模块
try:
    from modules.wechat_auto_login_simple import WeChatAutoLoginSimple
    from modules.wechat_api_crawler import WeChatAPICrawler
    from modules.storage import DataStorage
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    # 定义占位符类，确保脚本能够启动
    class Placeholder:
        def __init__(self, *args, **kwargs):
            pass
    
    WeChatAutoLoginSimple = Placeholder
    WeChatAPICrawler = Placeholder
    DataStorage = Placeholder

class WindServiceCrawler:
    """Wind服务号专属爬虫"""
    
    def __init__(self, config_file='config/wind_service_config.json'):
        """初始化Wind服务号爬虫"""
        self.config_file = config_file
        self.config = self._load_config()
        self.session_file = 'config/wechat_session.json'
        self.storage = DataStorage()
        self.auto_login = WeChatAutoLoginSimple(self.session_file)
        self.api_crawler = None
        
        # Wind服务号配置
        self.wind_service_name = self.config.get('wind_service_name', 'Wind万得')
        self.wind_fakeid = self.config.get('wind_fakeid', '')
        self.output_format = self.config.get('output_format', 'json')  # json, csv, txt
        self.output_dir = self.config.get('output_dir', 'data/wind')
        self.max_articles = self.config.get('max_articles', 10)
        self.auto_run = self.config.get('auto_run', False)
        self.run_interval = self.config.get('run_interval', 3600)  # 秒
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Wind服务号爬虫初始化完成，输出目录: {self.output_dir}")
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
        return {
            'wind_service_name': 'Wind万得',
            'wind_fakeid': '',
            'output_format': 'json',
            'output_dir': 'data/wind',
            'max_articles': 10,
            'auto_run': False,
            'run_interval': 3600
        }
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("配置文件已保存")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def login(self) -> bool:
        """登录微信公众号平台"""
        logger.info("开始登录微信公众号平台...")
        
        # 检查是否已登录
        session_data = self.auto_login.get_session()
        if session_data.get('token') and session_data.get('cookie'):
            # 检查登录是否过期
            login_time = session_data.get('login_time')
            if login_time:
                login_datetime = datetime.fromisoformat(login_time)
                if datetime.now() - login_datetime < timedelta(days=7):
                    logger.info("使用已保存的登录会话")
                    self.api_crawler = WeChatAPICrawler(session_data)
                    return True
        
        # 执行登录
        if self.auto_login.login():
            session_data = self.auto_login.get_session()
            self.api_crawler = WeChatAPICrawler(session_data)
            logger.info("登录成功")
            return True
        else:
            logger.error("登录失败")
            return False
    
    def get_wind_fakeid(self) -> Optional[str]:
        """获取Wind服务号的fakeid"""
        if self.wind_fakeid:
            logger.info(f"使用已保存的fakeid: {self.wind_fakeid}")
            return self.wind_fakeid
        
        logger.info(f"搜索Wind服务号: {self.wind_service_name}")
        fakeid = self.auto_login.get_fakeid_by_api(self.wind_service_name)
        
        if fakeid:
            logger.info(f"获取到Wind服务号fakeid: {fakeid}")
            self.wind_fakeid = fakeid
            self.config['wind_fakeid'] = fakeid
            self._save_config()
            return fakeid
        else:
            logger.error(f"未找到Wind服务号: {self.wind_service_name}")
            return None
    
    def get_service_account_messages(self) -> List[Dict]:
        """获取服务号推送的消息（使用微信网页版）"""
        try:
            logger.info("尝试获取服务号推送消息（微信网页版）")
            
            # 初始化浏览器
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            
            edge_options = EdgeOptions()
            edge_options.add_argument('--no-sandbox')
            edge_options.add_argument('--disable-dev-shm-usage')
            edge_options.add_argument('--disable-gpu')
            edge_options.add_argument('--disable-extensions')
            edge_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # 尝试使用自定义路径的 msedgedriver
            try:
                custom_driver_path = r"C:\msedgedriver\msedgedriver.exe"
                if os.path.exists(custom_driver_path):
                    from selenium.webdriver.edge.service import Service as EdgeService
                    edge_service = EdgeService(executable_path=custom_driver_path)
                    driver = webdriver.Edge(service=edge_service, options=edge_options)
                    logger.info(f"使用自定义路径msedgedriver: {custom_driver_path}")
                else:
                    # 使用 webdriver-manager 自动管理驱动
                    driver = webdriver.Edge(EdgeChromiumDriverManager().install(), options=edge_options)
                    logger.info("使用 webdriver-manager 安装的 msedgedriver")
            except Exception as e:
                logger.error(f"初始化浏览器失败: {e}")
                return []
            
            try:
                # 访问微信网页版
                driver.get("https://wx.qq.com/")
                logger.info("请使用微信扫码登录网页版微信")
                
                # 等待登录成功（等待聊天区域出现）
                try:
                    # 等待二维码出现
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".qrcode, .login_box"))
                    )
                    logger.info("二维码已显示，请扫码登录")
                    
                    # 等待登录成功（等待聊天列表出现）
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".chat_list, .main_left, #chatArea"))
                    )
                    logger.info("登录成功，正在查找Wind服务号...")
                except Exception as e:
                    logger.error(f"登录过程失败: {e}")
                    # 保存截图
                    screenshot_path = os.path.join(self.output_dir, "login_failed.png")
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"已保存登录失败截图: {screenshot_path}")
                    driver.quit()
                    return []
                
                # 等待聊天列表完全加载
                time.sleep(5)
                
                # 保存登录成功后的截图
                screenshot_path = os.path.join(self.output_dir, "login_success.png")
                driver.save_screenshot(screenshot_path)
                logger.info(f"已保存登录成功截图: {screenshot_path}")
                
                # 查找聊天列表中的Wind服务号
                wind_chat = None
                
                # 尝试多种选择器查找聊天列表
                chat_list_selectors = [
                    ".chat_list",
                    ".main_left",
                    "#chatArea",
                    ".chat_list_container"
                ]
                
                for selector in chat_list_selectors:
                    try:
                        chat_container = driver.find_element(By.CSS_SELECTOR, selector)
                        # 在聊天容器中查找所有聊天项
                        chat_items = chat_container.find_elements(By.CSS_SELECTOR, "*")
                        
                        logger.info(f"在 {selector} 中找到 {len(chat_items)} 个元素")
                        
                        # 遍历所有元素，查找包含服务号名称的聊天项
                        for item in chat_items:
                            try:
                                item_text = item.text
                                if self.wind_service_name in item_text:
                                    wind_chat = item
                                    logger.info(f"找到Wind服务号聊天: {item_text[:50]}...")
                                    break
                            except:
                                continue
                        
                        if wind_chat:
                            break
                    except:
                        continue
                
                # 如果特定选择器失败，尝试全局搜索
                if not wind_chat:
                    try:
                        all_elements = driver.find_elements(By.CSS_SELECTOR, "*")
                        logger.info(f"全局搜索: 找到 {len(all_elements)} 个元素")
                        
                        for element in all_elements[:200]:  # 限制搜索数量，避免超时
                            try:
                                element_text = element.text
                                if self.wind_service_name in element_text:
                                    wind_chat = element
                                    logger.info(f"全局搜索找到Wind服务号: {element_text[:50]}...")
                                    break
                            except:
                                continue
                    except:
                        pass
                
                if not wind_chat:
                    logger.error("未找到Wind服务号聊天")
                    # 保存截图
                    screenshot_path = os.path.join(self.output_dir, "service_not_found.png")
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"已保存未找到服务号截图: {screenshot_path}")
                    
                    # 保存页面源代码，以便分析
                    page_source_path = os.path.join(self.output_dir, "page_source.html")
                    with open(page_source_path, 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    logger.info(f"已保存页面源代码: {page_source_path}")
                    
                    driver.quit()
                    return []
                
                # 点击进入聊天窗口
                wind_chat.click()
                time.sleep(5)  # 等待聊天内容加载
                
                # 保存聊天窗口截图
                screenshot_path = os.path.join(self.output_dir, "chat_window.png")
                driver.save_screenshot(screenshot_path)
                logger.info(f"已保存聊天窗口截图: {screenshot_path}")
                
                # 提取聊天内容
                messages = []
                
                # 尝试多种选择器查找消息
                message_selectors = [
                    ".message",
                    ".chat_item",
                    ".rich_media",
                    ".msg"
                ]
                
                for selector in message_selectors:
                    try:
                        message_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        logger.info(f"使用 {selector} 找到 {len(message_elements)} 条消息")
                        
                        for msg in message_elements:
                            try:
                                # 提取消息内容
                                msg_content = msg.text.strip()
                                
                                if msg_content:
                                    # 尝试提取消息时间
                                    msg_time = ""
                                    try:
                                        time_elements = msg.find_elements(By.CSS_SELECTOR, ".time, .timestamp")
                                        if time_elements:
                                            msg_time = time_elements[0].text.strip()
                                    except:
                                        pass
                                    
                                    # 提取消息类型
                                    msg_type = 'text'
                                    if msg.find_elements(By.CSS_SELECTOR, "img"):
                                        msg_type = 'image'
                                    elif msg.find_elements(By.CSS_SELECTOR, "a"):
                                        msg_type = 'link'
                                    
                                    message = {
                                        'type': msg_type,
                                        'content': msg_content,
                                        'time': msg_time,
                                        'service_name': self.wind_service_name
                                    }
                                    messages.append(message)
                                    logger.info(f"找到消息: {msg_content[:50]}...")
                            except Exception as e:
                                logger.warning(f"解析消息失败: {e}")
                                continue
                        
                        if messages:
                            break
                    except:
                        continue
                
                logger.info(f"成功获取 {len(messages)} 条Wind服务号消息")
                return messages
                
            finally:
                # 确保关闭浏览器
                if 'driver' in locals():
                    driver.quit()
                    
        except Exception as e:
            logger.error(f"获取服务号推送消息失败: {e}")
            return []
    
    def get_wind_articles(self) -> List[Dict]:
        """获取Wind服务号的文章"""
        # 先尝试 API 方法
        fakeid = self.get_wind_fakeid()
        if fakeid:
            logger.info(f"获取Wind服务号文章，最多获取{self.max_articles}篇")
            articles = self.api_crawler.get_all_articles(fakeid, max_count=self.max_articles)
            
            if articles:
                logger.info(f"成功获取 {len(articles)} 篇Wind服务号文章")
                # 为每篇文章添加服务号信息
                for article in articles:
                    article['service_name'] = self.wind_service_name
                    article['crawl_time'] = datetime.now().isoformat()
                return articles
        
        # API 方法失败，尝试获取服务号推送消息
        logger.warning("API方法未获取到Wind服务号文章，尝试获取服务号推送消息")
        messages = self.get_service_account_messages()
        
        if messages:
            logger.info(f"成功获取 {len(messages)} 条Wind服务号推送消息")
            # 处理推送消息，转换为文章格式
            articles = []
            for message in messages[:self.max_articles]:
                # 尝试从消息中提取链接和标题
                title = message.get('content', '')[:100]  # 使用内容的前100个字符作为标题
                content = message.get('content', '')
                publish_time = message.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                
                article = {
                    'title': title,
                    'content': content,
                    'publish_time': publish_time,
                    'service_name': self.wind_service_name,
                    'crawl_time': datetime.now().isoformat(),
                    'message_type': message.get('type', 'text')
                }
                articles.append(article)
            return articles
        else:
            logger.warning("未获取到Wind服务号推送消息")
            return []
    
    def extract_article_content(self, article: Dict) -> Dict:
        """提取文章内容，便于后续操作"""
        logger.info(f"提取文章内容: {article.get('title', '无标题')}")
        
        # 获取文章详情
        url = article.get('url', '')
        if not url:
            logger.error("文章URL为空")
            return article
        
        detail = self.api_crawler.get_article_detail(url)
        if detail:
            # 更新文章内容
            article['content'] = detail.get('content', article.get('content', ''))
            article['content_images'] = detail.get('content_images', article.get('content_images', []))
            article['content_length'] = detail.get('content_length', len(article.get('content', '')))
            article['extraction_method'] = detail.get('extraction_method', 'unknown')
        
        return article
    
    def save_articles(self, articles: List[Dict]) -> List[str]:
        """保存文章内容为便于后续操作的格式"""
        saved_files = []
        
        for article in articles:
            try:
                # 提取文章信息
                title = article.get('title', '无标题')
                publish_time = article.get('publish_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                content = article.get('content', '')
                
                # 生成文件名
                safe_title = self._sanitize_filename(title)
                timestamp = publish_time.replace(':', '').replace(' ', '_').replace('-', '')
                filename = f"wind_{timestamp}_{safe_title}"
                filepath = os.path.join(self.output_dir, filename)
                
                # 根据输出格式保存
                if self.output_format == 'json':
                    filepath += '.json'
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(article, f, ensure_ascii=False, indent=2)
                elif self.output_format == 'txt':
                    filepath += '.txt'
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"标题: {title}\n")
                        f.write(f"发布时间: {publish_time}\n")
                        f.write(f"URL: {article.get('url', '')}\n")
                        f.write(f"服务号: {article.get('service_name', '')}\n")
                        f.write("\n" + "="*80 + "\n\n")
                        f.write(content)
                elif self.output_format == 'csv':
                    # CSV格式使用追加模式
                    csv_file = os.path.join(self.output_dir, 'wind_articles.csv')
                    if not os.path.exists(csv_file):
                        with open(csv_file, 'w', encoding='utf-8') as f:
                            f.write('标题,发布时间,URL,服务号,内容长度\n')
                    with open(csv_file, 'a', encoding='utf-8') as f:
                        content_length = article.get('content_length', len(content))
                        f.write(f"{title},{publish_time},{article.get('url', '')},{article.get('service_name', '')},{content_length}\n")
                    filepath = csv_file
                
                # 保存到数据库
                self.storage.save_article(article)
                
                saved_files.append(filepath)
                logger.info(f"文章保存成功: {filepath}")
                
            except Exception as e:
                logger.error(f"保存文章失败: {e}")
        
        return saved_files
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        # 限制文件名长度
        if len(filename) > 50:
            filename = filename[:50]
        return filename.strip()
    
    def run(self) -> List[str]:
        """运行Wind服务号爬虫"""
        logger.info("开始运行Wind服务号爬虫")
        
        # 登录
        if not self.login():
            logger.error("登录失败，无法继续")
            return []
        
        # 获取Wind服务号文章
        articles = self.get_wind_articles()
        if not articles:
            logger.error("未获取到文章，无法继续")
            return []
        
        # 提取文章内容
        processed_articles = []
        for article in articles:
            processed_article = self.extract_article_content(article)
            processed_articles.append(processed_article)
        
        # 保存文章
        saved_files = self.save_articles(processed_articles)
        
        logger.info(f"Wind服务号爬虫运行完成，保存了{len(saved_files)}个文件")
        return saved_files
    
    def run_auto(self):
        """自动运行模式，定时获取新文章"""
        logger.info("启动自动运行模式")
        
        while True:
            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"[{datetime.now()}] 开始自动获取Wind服务号文章")
                logger.info(f"{'='*80}")
                
                self.run()
                
                logger.info(f"\n{'='*80}")
                logger.info(f"[{datetime.now()}] 自动获取完成，等待下一次运行")
                logger.info(f"等待时间: {self.run_interval}秒")
                logger.info(f"{'='*80}")
                
                time.sleep(self.run_interval)
                
            except KeyboardInterrupt:
                logger.info("用户中断自动运行")
                break
            except Exception as e:
                logger.error(f"自动运行出错: {e}")
                # 出错后等待一段时间再重试
                time.sleep(600)  # 等待10分钟

    def show_config(self):
        """显示当前配置"""
        print(f"\n{'='*80}")
        print("Wind服务号爬虫配置")
        print(f"{'='*80}")
        print(f"Wind服务号名称: {self.wind_service_name}")
        print(f"Wind服务号fakeid: {self.wind_fakeid or '未设置'}")
        print(f"输出格式: {self.output_format}")
        print(f"输出目录: {self.output_dir}")
        print(f"最大文章数: {self.max_articles}")
        print(f"自动运行: {'是' if self.auto_run else '否'}")
        print(f"运行间隔: {self.run_interval}秒")
        print(f"{'='*80}")

    def update_config(self):
        """更新配置"""
        print(f"\n{'='*80}")
        print("更新Wind服务号爬虫配置")
        print(f"{'='*80}")
        
        # Wind服务号名称
        new_name = input(f"Wind服务号名称 [{self.wind_service_name}]: ").strip()
        if new_name:
            self.wind_service_name = new_name
            self.config['wind_service_name'] = new_name
        
        # 输出格式
        print("\n输出格式选项:")
        print("1. json (默认，完整信息)")
        print("2. txt (纯文本，便于阅读)")
        print("3. csv (表格格式，便于数据分析)")
        format_choice = input("请选择输出格式 (1-3) [1]: ").strip()
        format_map = {'1': 'json', '2': 'txt', '3': 'csv'}
        if format_choice in format_map:
            self.output_format = format_map[format_choice]
            self.config['output_format'] = self.output_format
        
        # 最大文章数
        max_articles = input(f"\n最大文章数 [{self.max_articles}]: ").strip()
        if max_articles.isdigit():
            self.max_articles = int(max_articles)
            self.config['max_articles'] = self.max_articles
        
        # 自动运行
        auto_run = input(f"\n自动运行 (y/n) [{ 'y' if self.auto_run else 'n' }]: ").strip().lower()
        if auto_run == 'y':
            self.auto_run = True
            self.config['auto_run'] = True
            # 运行间隔
            interval = input(f"运行间隔（秒）[{self.run_interval}]: ").strip()
            if interval.isdigit():
                self.run_interval = int(interval)
                self.config['run_interval'] = self.run_interval
        elif auto_run == 'n':
            self.auto_run = False
            self.config['auto_run'] = False
        
        # 保存配置
        self._save_config()
        print(f"\n{'='*80}")
        print("配置更新完成！")
        print(f"{'='*80}")


def main():
    """主函数"""
    crawler = WindServiceCrawler()
    
    # 显示帮助信息
    print(f"\n{'='*80}")
    print("Wind服务号专属爬虫脚本")
    print(f"{'='*80}")
    print("功能：")
    print("1. 自动登录微信公众号平台")
    print("2. 搜索并获取Wind服务号的fakeid")
    print("3. 获取Wind服务号推送的定制新闻")
    print("4. 提取文章内容并保存为便于后续操作的格式")
    print("5. 支持自动运行或手动触发")
    print(f"{'='*80}")
    
    # 显示当前配置
    crawler.show_config()
    
    # 询问操作
    print("\n操作选项:")
    print("1. 运行一次爬虫")
    print("2. 启动自动运行模式")
    print("3. 更新配置")
    print("4. 退出")
    
    while True:
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == '1':
            print("\n运行Wind服务号爬虫...")
            saved_files = crawler.run()
            if saved_files:
                print(f"\n成功保存以下文件:")
                for file in saved_files[:5]:  # 只显示前5个文件
                    print(f"  - {file}")
                if len(saved_files) > 5:
                    print(f"  ... 等{len(saved_files) - 5}个文件")
            else:
                print("\n未保存任何文件，请检查日志")
                
        elif choice == '2':
            print("\n启动自动运行模式...")
            print("按 Ctrl+C 退出自动运行")
            crawler.run_auto()
            
        elif choice == '3':
            crawler.update_config()
            crawler.show_config()
            
        elif choice == '4':
            print("\n退出程序...")
            break
        
        else:
            print("无效选项，请重新输入")


if __name__ == "__main__":
    main()
