import requests
import time
import random
import logging
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

class WeChatCrawler:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'timeout': 30,
            'retry_times': 3,
            'sleep_interval': 2,
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            'selenium': {
                'headless': False,
                'implicit_wait': 10,
                'page_load_timeout': 30
            }
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.config['headers'])
        self.logger = logging.getLogger(__name__)
        self.driver = None
    
    def _init_driver(self):
        """初始化Selenium浏览器"""
        if self.driver is None:
            try:
                # 优先使用Edge浏览器，因为用户已安装msedgedriver
                try:
                    edge_options = EdgeOptions()
                    if self.config['selenium']['headless']:
                        edge_options.add_argument('--headless')
                    edge_options.add_argument('--no-sandbox')
                    edge_options.add_argument('--disable-dev-shm-usage')
                    edge_options.add_argument('--disable-gpu')
                    edge_options.add_argument('--disable-extensions')
                    edge_options.add_argument('--disable-blink-features=AutomationControlled')
                    
                    # 添加随机User-Agent
                    from fake_useragent import UserAgent
                    ua = UserAgent()
                    user_agent = ua.random
                    edge_options.add_argument(f'user-agent={user_agent}')
                    
                    # 禁用自动化控制检测
                    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    edge_options.add_experimental_option('useAutomationExtension', False)
                    
                    # 尝试使用系统已安装的msedgedriver
                    try:
                        # 首先尝试用户指定的路径 C:\msedgedriver
                        import os
                        from selenium.webdriver.edge.service import Service as EdgeService
                        custom_driver_path = r"C:\msedgedriver\msedgedriver.exe"
                        if os.path.exists(custom_driver_path):
                            edge_service = EdgeService(executable_path=custom_driver_path)
                            self.driver = webdriver.Edge(service=edge_service, options=edge_options)
                            self.logger.info(f"使用自定义路径msedgedriver成功: {custom_driver_path}")
                        else:
                            # 尝试系统默认路径
                            self.driver = webdriver.Edge(options=edge_options)
                            self.logger.info("使用系统默认msedgedriver成功")
                    except Exception as e:
                        self.logger.warning(f"本地msedgedriver启动失败: {str(e)}")
                        # 尝试使用EdgeChromiumDriverManager安装驱动（仅在网络可用时）
                        try:
                            # 检查网络连接
                            import urllib.request
                            try:
                                urllib.request.urlopen('https://www.google.com', timeout=3)
                                network_available = True
                            except:
                                network_available = False
                            
                            if network_available:
                                edge_service = EdgeService(executable_path=EdgeChromiumDriverManager().install())
                                self.driver = webdriver.Edge(service=edge_service, options=edge_options)
                                self.logger.info("使用EdgeChromiumDriverManager安装驱动成功")
                            else:
                                self.logger.error("网络不可用，无法下载Edge驱动")
                                raise Exception("网络不可用，且本地未找到msedgedriver")
                        except Exception as e2:
                            self.logger.error(f"EdgeChromiumDriverManager安装失败: {str(e2)}")
                            # 回退到Chrome
                            raise
                except Exception as e:
                    self.logger.warning(f"Edge浏览器初始化失败: {str(e)}")
                    # 回退到Chrome浏览器
                    chrome_options = ChromeOptions()
                    if self.config['selenium']['headless']:
                        chrome_options.add_argument('--headless')
                    chrome_options.add_argument('--no-sandbox')
                    chrome_options.add_argument('--disable-dev-shm-usage')
                    chrome_options.add_argument('--disable-gpu')
                    chrome_options.add_argument('--disable-extensions')
                    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                    
                    # 添加随机User-Agent
                    from fake_useragent import UserAgent
                    ua = UserAgent()
                    user_agent = ua.random
                    chrome_options.add_argument(f'user-agent={user_agent}')
                    
                    # 禁用自动化控制检测
                    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    chrome_options.add_experimental_option('useAutomationExtension', False)
                    
                    # 尝试使用系统已安装的ChromeDriver
                    try:
                        self.driver = webdriver.Chrome(options=chrome_options)
                        self.logger.info("使用系统已安装的ChromeDriver成功")
                    except Exception as e2:
                        self.logger.warning(f"系统ChromeDriver启动失败: {str(e2)}")
                        # 尝试使用ChromeDriverManager安装驱动
                        try:
                            self.driver = webdriver.Chrome(
                                executable_path=ChromeDriverManager().install(),
                                options=chrome_options
                            )
                            self.logger.info("使用ChromeDriverManager安装驱动成功")
                        except Exception as e3:
                            self.logger.error(f"ChromeDriverManager安装失败: {str(e3)}")
                            raise
                
                # 执行JS代码，进一步隐藏自动化特征
                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': '''
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    '''
                })
                
                self.driver.implicitly_wait(self.config['selenium']['implicit_wait'])
                self.driver.set_page_load_timeout(self.config['selenium']['page_load_timeout'])
                self.logger.info("Selenium浏览器初始化成功")
            except Exception as e:
                self.logger.error(f"Selenium浏览器初始化失败: {str(e)}")
                self.driver = None
        return self.driver
    
    def _close_driver(self):
        """关闭Selenium浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.logger.info("Selenium浏览器已关闭")
            except Exception as e:
                self.logger.error(f"关闭Selenium浏览器失败: {str(e)}")
    
    def _request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """带重试机制的HTTP请求"""
        retry_count = 0
        while retry_count < self.config['retry_times']:
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=self.config['timeout'], **kwargs)
                else:
                    response = self.session.post(url, timeout=self.config['timeout'], **kwargs)
                
                response.raise_for_status()
                return response
            except Exception as e:
                self.logger.warning(f"请求失败 {retry_count+1}/{self.config['retry_times']}: {str(e)}")
                retry_count += 1
                time.sleep(self.config['sleep_interval'] * (retry_count + 1))
        return None
    
    def search_account(self, name: str) -> Optional[Dict]:
        """搜索微信公众号"""
        try:
            self.logger.info(f"搜索公众号: {name}")
            
            # 使用搜狗微信搜索
            import urllib.parse
            encoded_name = urllib.parse.quote(name)
            search_url = f"https://weixin.sogou.com/weixin?type=1&query={encoded_name}"
            
            driver = self._init_driver()
            if not driver:
                self.logger.error("无法初始化浏览器，搜索失败")
                return None
            
            # 添加随机延迟，模拟人类操作
            time.sleep(random.uniform(2, 4))
            
            driver.get(search_url)
            # 等待页面加载
            time.sleep(random.uniform(3, 5))
            
            # 检查是否有验证码
            try:
                captcha_elem = driver.find_element(By.CSS_SELECTOR, '#verify_img')
                if captcha_elem:
                    self.logger.warning("检测到验证码，需要手动处理")
                    # 这里可以添加验证码处理逻辑
                    time.sleep(10)  # 给用户时间手动处理
            except Exception as e:
                self.logger.info("未检测到验证码")
            
            # 查找公众号信息
            account_info = None
            try:
                # 尝试多种选择器查找公众号列表
                selectors = [
                    '.news-box .wx-rb',
                    '.news-list .news-item',
                    '.weixin-search-result .result-item'
                ]
                
                account_items = []
                for selector in selectors:
                    try:
                        items = driver.find_elements(By.CSS_SELECTOR, selector)
                        if items:
                            account_items = items
                            break
                    except Exception as e:
                        self.logger.warning(f"尝试选择器 {selector} 失败: {str(e)}")
                        continue
                
                for item in account_items:
                    try:
                        # 提取公众号名称
                        name_selectors = ['.wx-name', '.account-name', '.name']
                        account_name = ""
                        for sel in name_selectors:
                            try:
                                elem = item.find_element(By.CSS_SELECTOR, sel)
                                account_name = elem.text.strip()
                                break
                            except:
                                continue
                        
                        # 提取公众号ID
                        id_selectors = ['.info', '.account-id', '.id']
                        account_id_text = ""
                        for sel in id_selectors:
                            try:
                                elem = item.find_element(By.CSS_SELECTOR, sel)
                                account_id_text = elem.text.strip()
                                break
                            except:
                                continue
                        
                        # 提取描述
                        desc_selectors = ['.sp-txt', '.description', '.desc']
                        description = ""
                        for sel in desc_selectors:
                            try:
                                elem = item.find_element(By.CSS_SELECTOR, sel)
                                description = elem.text.strip()
                                break
                            except:
                                continue
                        
                        # 提取链接
                        link_selectors = ['.wx-name > a', 'a', '.link']
                        account_url = ""
                        for sel in link_selectors:
                            try:
                                elem = item.find_element(By.CSS_SELECTOR, sel)
                                account_url = elem.get_attribute('href')
                                if account_url:
                                    break
                            except:
                                continue
                        
                        if account_name and (account_name == name or name in account_name):
                            account_info = {
                                'name': account_name,
                                'id': account_id_text or f"gh_{hash(account_name) % 100000000}",
                                'description': description,
                                'url': account_url or f"https://mp.weixin.qq.com/"
                            }
                            self.logger.info(f"找到公众号: {account_name}")
                            break
                    except Exception as e:
                        self.logger.warning(f"解析公众号项失败: {str(e)}")
                        continue
            except Exception as e:
                self.logger.warning(f"查找公众号列表失败: {str(e)}")
            
            # 如果没有找到，返回基于输入的信息
            if not account_info:
                account_info = {
                    'name': name,
                    'id': f"gh_{hash(name) % 100000000}",
                    'description': f"{name} 公众号",
                    'url': f"https://mp.weixin.qq.com/"
                }
                self.logger.warning(f"未找到精确匹配的公众号，使用默认信息")
            
            return account_info
        except Exception as e:
            self.logger.error(f"搜索公众号失败: {str(e)}")
            return None
    
    def get_history_articles(self, account_id: str) -> List[Dict]:
        """获取公众号历史文章"""
        articles = []
        try:
            self.logger.info(f"获取公众号历史文章: {account_id}")
            
            # 注意：微信公众号历史文章需要登录才能获取更多内容
            # 这里使用Selenium访问公众号主页并滚动加载
            
            driver = self._init_driver()
            if not driver:
                self.logger.error("无法初始化浏览器，获取文章失败")
                return articles
            
            # 访问微信公众号主页（这里使用一个示例URL，实际需要从搜索结果获取）
            # 注意：实际使用时需要替换为真实的公众号主页URL
            account_url = f"https://mp.weixin.qq.com/profile?src=3&timestamp=1700000000&ver=1&signature=ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            
            # 这里我们使用搜狗微信搜索结果中的文章链接来获取文章列表
            # 实际使用时，需要先搜索到公众号，然后访问其历史文章页面
            
            # 使用搜狗微信搜索该公众号的文章
            search_url = f"https://weixin.sogou.com/weixin?type=2&query={account_id}"
            driver.get(search_url)
            time.sleep(3)
            
            # 滚动页面加载更多文章
            for i in range(3):  # 滚动3次，加载更多文章
                try:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                except Exception as e:
                    self.logger.warning(f"滚动页面失败: {str(e)}")
                    break
            
            # 提取文章信息 - 使用调试中找到的正确选择器
            # 文章列表在 .news-list li 中
            article_items = driver.find_elements(By.CSS_SELECTOR, '.news-list li')
            
            if not article_items:
                self.logger.warning("未找到文章列表，尝试其他选择器")
                # 尝试其他可能的选择器
                article_items = driver.find_elements(By.CSS_SELECTOR, '.txt-box h3')
                self.logger.info(f"使用备选选择器找到 {len(article_items)} 个标题")
            
            for item in article_items:
                try:
                    # 提取标题
                    title = ""
                    url = ""
                    try:
                        title_elem = item.find_element(By.CSS_SELECTOR, 'h3')
                        title = title_elem.text.strip()
                        # 提取链接
                        link_elem = title_elem.find_element(By.TAG_NAME, 'a')
                        url = link_elem.get_attribute('href')
                    except:
                        # 如果item本身就是标题元素
                        title = item.text.strip()
                        try:
                            url = item.find_element(By.XPATH, '..').get_attribute('href')
                        except:
                            pass
                    
                    if not title:
                        continue
                    
                    # 提取发布时间 - 在 .s-p 中
                    publish_time = ""
                    try:
                        time_elem = item.find_element(By.CSS_SELECTOR, '.s-p')
                        publish_time = time_elem.text.strip()
                    except:
                        pass
                    
                    # 提取摘要
                    summary = ""
                    try:
                        summary_elem = item.find_element(By.CSS_SELECTOR, 'p')
                        summary = summary_elem.text.strip()
                    except:
                        pass
                    
                    # 提取封面图片
                    cover_image = None
                    try:
                        img_elem = item.find_element(By.CSS_SELECTOR, 'img')
                        cover_image = img_elem.get_attribute('src')
                    except:
                        pass
                    
                    article = {
                        'title': title,
                        'url': url,
                        'publish_time': publish_time,
                        'summary': summary,
                        'cover_image': cover_image
                    }
                    articles.append(article)
                    self.logger.info(f"找到文章: {title[:50]}...")
                    
                except Exception as e:
                    self.logger.warning(f"解析文章项失败: {str(e)}")
                    continue
            
            self.logger.info(f"获取到 {len(articles)} 篇文章")
        except Exception as e:
            self.logger.error(f"获取历史文章失败: {str(e)}")
        
        return articles
    
    def extract_article_content(self, url: str) -> Optional[Dict]:
        """提取文章内容"""
        try:
            self.logger.info(f"提取文章内容: {url}")
            
            # 使用Selenium访问文章链接并提取内容
            driver = self._init_driver()
            if not driver:
                self.logger.error("无法初始化浏览器，提取内容失败")
                return None
            
            driver.get(url)
            time.sleep(3)  # 等待页面加载
            
            # 提取文章标题
            title = ""
            try:
                title_elem = driver.find_element(By.CSS_SELECTOR, '#activity-name')
                title = title_elem.text.strip()
            except Exception as e:
                self.logger.warning(f"提取标题失败: {str(e)}")
                # 尝试其他选择器
                try:
                    title_elem = driver.find_element(By.CSS_SELECTOR, 'h1')
                    title = title_elem.text.strip()
                except:
                    pass
            
            # 提取发布时间
            publish_time = ""
            try:
                time_elem = driver.find_element(By.CSS_SELECTOR, '#post-date')
                publish_time = time_elem.text.strip()
            except Exception as e:
                self.logger.warning(f"提取发布时间失败: {str(e)}")
                # 尝试其他选择器
                try:
                    time_elem = driver.find_element(By.CSS_SELECTOR, '.publish_time')
                    publish_time = time_elem.text.strip()
                except:
                    pass
            
            # 提取作者
            author = ""
            try:
                author_elem = driver.find_element(By.CSS_SELECTOR, '#js_name')
                author = author_elem.text.strip()
            except Exception as e:
                self.logger.warning(f"提取作者失败: {str(e)}")
                # 尝试其他选择器
                try:
                    author_elem = driver.find_element(By.CSS_SELECTOR, '.author')
                    author = author_elem.text.strip()
                except:
                    pass
            
            # 提取文章内容
            content = ""
            try:
                content_elem = driver.find_element(By.CSS_SELECTOR, '#js_content')
                content = content_elem.text.strip()
            except Exception as e:
                self.logger.warning(f"提取内容失败: {str(e)}")
                # 尝试其他选择器
                try:
                    content_elem = driver.find_element(By.CSS_SELECTOR, '.rich_media_content')
                    content = content_elem.text.strip()
                except:
                    pass
            
            # 提取阅读数和点赞数（注意：这些需要登录才能看到完整数据）
            reading_count = 0
            like_count = 0
            try:
                # 尝试提取阅读数
                read_elem = driver.find_element(By.CSS_SELECTOR, '.read_num')
                read_text = read_elem.text.strip()
                match = re.search(r'\d+', read_text)
                if match:
                    reading_count = int(match.group())
            except Exception as e:
                self.logger.warning(f"提取阅读数失败: {str(e)}")
            
            try:
                # 尝试提取点赞数
                like_elem = driver.find_element(By.CSS_SELECTOR, '.like_num')
                like_text = like_elem.text.strip()
                match = re.search(r'\d+', like_text)
                if match:
                    like_count = int(match.group())
            except Exception as e:
                self.logger.warning(f"提取点赞数失败: {str(e)}")
            
            # 构建文章信息
            article_info = {
                'title': title or f'未命名文章',
                'publish_time': publish_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'author': author or '未知作者',
                'content': content or '无内容',
                'reading_count': reading_count,
                'like_count': like_count,
                'url': url
            }
            
            self.logger.info(f"提取文章内容成功: {article_info['title']}")
            return article_info
        except Exception as e:
            self.logger.error(f"提取文章内容失败: {str(e)}")
            return None
    
    def crawl_account(self, account_name: str) -> List[Dict]:
        """完整爬取公众号"""
        articles = []
        try:
            # 搜索公众号
            account_info = self.search_account(account_name)
            if not account_info:
                return articles
            
            # 获取历史文章
            history_articles = self.get_history_articles(account_info.get('id', account_name))
            
            # 提取每篇文章的详细内容
            for article in history_articles:
                if article.get('url'):
                    content_info = self.extract_article_content(article['url'])
                    if content_info:
                        # 合并信息
                        article.update(content_info)
                        article['account_name'] = account_info['name']
                        article['account_id'] = account_info.get('id', '')
                        article['crawl_time'] = datetime.now().isoformat()
                        articles.append(article)
                    
                    # 避免请求过快
                    time.sleep(self.config['sleep_interval'])
            
            self.logger.info(f"爬取完成，共获取 {len(articles)} 篇文章")
        except Exception as e:
            self.logger.error(f"爬取公众号失败: {str(e)}")
        finally:
            # 确保关闭浏览器
            self._close_driver()
        
        return articles
    
    def check_new_articles(self, account_id: str, last_update: str) -> List[Dict]:
        """检查新文章"""
        try:
            all_articles = self.get_history_articles(account_id)
            
            if not last_update:
                return all_articles
            
            # 解析上次更新时间
            last_update_time = datetime.fromisoformat(last_update)
            
            # 筛选新文章
            new_articles = []
            for article in all_articles:
                publish_time_str = article.get('publish_time', '')
                if publish_time_str:
                    try:
                        # 尝试解析发布时间
                        publish_time = datetime.strptime(publish_time_str, '%Y-%m-%d %H:%M:%S')
                        if publish_time > last_update_time:
                            new_articles.append(article)
                    except:
                        pass
            
            self.logger.info(f"发现 {len(new_articles)} 篇新文章")
            return new_articles
        except Exception as e:
            self.logger.error(f"检查新文章失败: {str(e)}")
            return []
    
    def batch_crawl(self, accounts: List[Dict]) -> Dict[str, List[Dict]]:
        """批量爬取多个公众号"""
        results = {}
        
        for account in accounts:
            account_name = account.get('name')
            if account_name:
                articles = self.crawl_account(account_name)
                results[account_name] = articles
                
                # 避免请求过快
                time.sleep(self.config['sleep_interval'] * 2)
        
        return results

# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    crawler = WeChatCrawler()
    
    # 测试搜索公众号
    account = crawler.search_account('人民日报')
    print(f"搜索结果: {account}")
    
    # 测试爬取公众号
    if account:
        articles = crawler.crawl_account(account['name'])
        print(f"爬取文章数: {len(articles)}")
        if articles:
            print(f"第一篇文章标题: {articles[0].get('title')}")
