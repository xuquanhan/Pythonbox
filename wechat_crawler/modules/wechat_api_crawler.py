#!/usr/bin/env python3
"""
微信公众号API爬虫模块
使用微信公众号后台API获取文章列表和内容
"""

import requests
import time
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WeChatAPICrawler:
    """微信公众号API爬虫类"""
    
    def __init__(self, session_data: dict):
        """
        初始化API爬虫
        session_data: 包含token、cookie等会话信息
        """
        self.session_data = session_data
        self.token = session_data.get('token')
        self.cookie = session_data.get('cookie')
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=list&type=10&isMul=1&isNew=1&lang=zh_CN",
            "Cookie": self.cookie,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        
    def get_articles(self, fakeid: str, begin: int = 0, count: int = 5) -> List[Dict]:
        """
        获取公众号文章列表
        
        Args:
            fakeid: 公众号的fakeid
            begin: 起始位置（分页用）
            count: 获取数量
            
        Returns:
            文章列表
        """
        url = "https://mp.weixin.qq.com/cgi-bin/appmsg"
        
        params = {
            "token": self.token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1",
            "action": "list_ex",
            "begin": str(begin),
            "count": str(count),
            "query": "",
            "fakeid": fakeid,
            "type": "9",  # 使用默认类型
        }
        
        try:
            logger.info(f"获取文章列表: begin={begin}, count={count}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"请求失败: {response.status_code}")
                return []
            
            data = response.json()
            
            # 检查是否登录过期
            if data.get('base_resp', {}).get('ret') == 200003:
                logger.error("登录已过期，需要重新登录")
                return []
            
            # 检查是否有错误
            if data.get('base_resp', {}).get('ret') != 0:
                logger.error(f"API返回错误: {data.get('base_resp', {})}")
                return []
            
            # 解析文章列表
            articles = []
            app_msg_list = data.get('app_msg_list', [])
            
            for item in app_msg_list:
                article = {
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'publish_time': datetime.fromtimestamp(item.get('create_time', 0)).strftime('%Y-%m-%d %H:%M:%S') if item.get('create_time') else '',
                    'summary': item.get('digest', ''),
                    'cover_image': item.get('cover', ''),
                    'article_id': item.get('aid', ''),
                    'create_time': item.get('create_time', 0)
                }
                articles.append(article)
                logger.info(f"找到文章: {article['title'][:50]}...")
            
            logger.info(f"成功获取 {len(articles)} 篇文章")
            return articles
            
        except Exception as e:
            logger.error(f"获取文章列表失败: {e}")
            return []
    
    def get_all_articles(self, fakeid: str, max_count: int = 100) -> List[Dict]:
        """
        获取公众号所有文章（支持翻页）
        
        Args:
            fakeid: 公众号的fakeid
            max_count: 最大获取数量
            
        Returns:
            所有文章列表
        """
        all_articles = []
        begin = 0
        count = 5  # 每页5篇
        
        while len(all_articles) < max_count:
            logger.info(f"获取第 {begin//count + 1} 页文章...")
            articles = self.get_articles(fakeid, begin, count)
            
            if not articles:
                logger.info("没有更多文章了")
                break
            
            all_articles.extend(articles)
            
            # 检查是否获取完毕
            if len(articles) < count:
                logger.info("已获取全部文章")
                break
            
            begin += count
            
            # 添加随机延迟，避免被封
            delay = 2 + (begin % 3)
            logger.info(f"等待 {delay} 秒后继续...")
            time.sleep(delay)
        
        logger.info(f"总共获取 {len(all_articles)} 篇文章")
        return all_articles[:max_count]
    
    def get_article_detail(self, article_url: str) -> Optional[Dict]:
        """
        获取文章详情（使用API方式/requests）
        
        Args:
            article_url: 文章链接
            
        Returns:
            文章详情字典
        """
        try:
            logger.info(f"获取文章详情: {article_url}")
            
            # 使用requests获取文章页面
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Cookie": self.cookie,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Referer": "https://mp.weixin.qq.com/"
            }
            
            # 使用适当的超时时间
            response = requests.get(article_url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"获取文章详情失败: {response.status_code}")
                return None
            
            # 从页面中提取文章内容
            html_content = response.text
            
            text_content = ""
            content_images = []
            extraction_method = "none"
            
            # 尝试使用BeautifulSoup解析HTML
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 方法1: 查找 #js_content
                js_content = soup.find('div', id='js_content')
                if js_content:
                    extraction_method = "js_content"
                    logger.info("使用方法1: 查找 #js_content")
                
                # 方法2: 查找 rich_media_content
                if not js_content:
                    rich_media_content = soup.find('div', class_='rich_media_content')
                    if rich_media_content:
                        js_content = rich_media_content
                        extraction_method = "rich_media_content"
                        logger.info("使用方法2: 查找 .rich_media_content")
                
                # 方法3: 查找 article 标签
                if not js_content:
                    article_tag = soup.find('article')
                    if article_tag:
                        js_content = article_tag
                        extraction_method = "article_tag"
                        logger.info("使用方法3: 查找 <article> 标签")
                
                # 方法4: 查找 main 标签
                if not js_content:
                    main_tag = soup.find('main')
                    if main_tag:
                        js_content = main_tag
                        extraction_method = "main_tag"
                        logger.info("使用方法4: 查找 <main> 标签")
                
                # 方法5: 查找 content 相关的标签
                if not js_content:
                    content_tags = soup.find_all(['div', 'section'], class_=lambda x: x and ('content' in x.lower() or 'article' in x.lower()))
                    for tag in content_tags:
                        if tag and len(tag.get_text(strip=True)) > 100:
                            js_content = tag
                            extraction_method = "content_related"
                            logger.info("使用方法5: 查找 content 相关标签")
                            break
                
                if js_content:
                    # 提取正文中的图片
                    img_tags = js_content.find_all('img')
                    logger.info(f"找到 {len(img_tags)} 个图片标签")
                    
                    for img in img_tags:
                        # 尝试多种图片URL属性
                        img_url = img.get('data-src')
                        if not img_url:
                            img_url = img.get('src')
                        if not img_url:
                            img_url = img.get('data-srcset')
                        if not img_url:
                            img_url = img.get('srcset')
                        
                        if img_url:
                            # 处理多个图片URL的情况
                            if ',' in img_url:
                                img_url = img_url.split(',')[0].strip()
                            # 处理URL中的大小参数
                            if '?' in img_url:
                                img_url = img_url.split('?')[0]
                            
                            # 处理相对路径
                            if not img_url.startswith(('http://', 'https://')):
                                if img_url.startswith('//'):
                                    img_url = 'https:' + img_url
                                elif img_url.startswith('/'):
                                    img_url = 'https://mp.weixin.qq.com' + img_url
                            
                            # 验证图片URL
                            if img_url.startswith(('http://', 'https://')):
                                # 去重
                                if img_url not in content_images:
                                    content_images.append(img_url)
                    
                    # 移除HTML标签获取纯文本
                    text_content = js_content.get_text(separator='\n', strip=True)
                    # 清理空白字符
                    import re
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                    # 移除多余的空白行
                    text_content = re.sub(r'\n+', '\n', text_content)
                    # 不限制内容长度，确保完整提取
                    logger.info(f"提取到内容长度: {len(text_content)} 字符")
                else:
                    # 方法6: 尝试获取整个body内容作为备选
                    body = soup.find('body')
                    if body:
                        extraction_method = "body_fallback"
                        logger.info("使用方法6: 获取整个 <body> 内容")
                        text_content = body.get_text(separator='\n', strip=True)
                        text_content = re.sub(r'\s+', ' ', text_content).strip()
                        text_content = re.sub(r'\n+', '\n', text_content)
                        logger.info(f"备选方法提取到内容长度: {len(text_content)} 字符")
            except ImportError:
                logger.warning("缺少BeautifulSoup库，使用正则表达式方法提取内容")
                # 直接使用正则表达式方法
                pass
            
            # 内容验证和增强
            if not text_content or len(text_content) < 200:
                logger.warning(f"提取的内容过短: {len(text_content)} 字符，方法: {extraction_method}")
                # 尝试使用正则表达式作为最后手段
                import re
                
                # 尝试多种正则表达式模式
                patterns = [
                    r'<div[^>]*id=["\']js_content["\'][^>]*>(.*?)</div>',
                    r'<div[^>]*class=["\']rich_media_content[^"\']*["\'][^>]*>(.*?)</div>',
                    r'<article[^>]*>(.*?)</article>',
                    r'<main[^>]*>(.*?)</main>',
                    r'<div[^>]*class=["\']content[^"\']*["\'][^>]*>(.*?)</div>'
                ]
                
                for pattern in patterns:
                    content_match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                    if content_match:
                        content_html = content_match.group(1)
                        
                        # 提取图片
                        img_urls = re.findall(r'<img[^>]+(?:data-src|src)=["\']([^"\']+)["\']', content_html, re.IGNORECASE)
                        for img_url in img_urls:
                            if img_url.startswith(('http://', 'https://')):
                                if img_url not in content_images:
                                    content_images.append(img_url)
                            elif img_url.startswith('//'):
                                full_img_url = 'https:' + img_url
                                if full_img_url not in content_images:
                                    content_images.append(full_img_url)
                        
                        # 提取文本
                        temp_content = re.sub(r'<[^>]+>', '', content_html)
                        temp_content = re.sub(r'\s+', ' ', temp_content).strip()
                        temp_content = re.sub(r'\n+', '\n', temp_content)
                        
                        if len(temp_content) > len(text_content):
                            text_content = temp_content
                            extraction_method = "regex_fallback"
                            logger.info(f"使用正则表达式回退方法，提取到内容长度: {len(text_content)} 字符")
                            break
            
            # 最终内容验证
            if not text_content:
                text_content = "[无法提取文章内容]"
                logger.error("无法提取文章内容")
            
            detail = {
                'url': article_url,
                'content': text_content,
                'content_images': content_images,
                'content_length': len(text_content),
                'image_count': len(content_images),
                'extraction_method': extraction_method
            }
            
            logger.info(f"获取文章详情成功: 文字长度 {len(text_content)}, 图片数量 {len(content_images)}, 提取方法: {extraction_method}")
            return detail
            
        except requests.exceptions.Timeout:
            logger.warning(f"获取文章详情超时: {article_url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"获取文章详情请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取文章详情失败: {e}")
            # 回退到正则表达式方法
            return self._get_article_detail_fallback(article_url)
    
    def _get_article_detail_fallback(self, article_url: str) -> Optional[Dict]:
        """
        回退方法：使用正则表达式获取文章详情
        """
        try:
            logger.info(f"使用回退方法获取文章详情: {article_url}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Cookie": self.cookie,
                "Referer": "https://mp.weixin.qq.com/"
            }
            
            response = requests.get(article_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"回退方法获取失败: {response.status_code}")
                return None
            
            html_content = response.text
            import re
            
            text_content = ""
            content_images = []
            
            # 尝试多种提取方法
            extraction_methods = [
                r'<div[^>]*id=["\']js_content["\'][^>]*>(.*?)</div>',
                r'<div[^>]*class=["\']rich_media_content[^"\']*["\'][^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
                r'<main[^>]*>(.*?)</main>'
            ]
            
            for pattern in extraction_methods:
                content_match = re.search(pattern, html_content, re.DOTALL | re.IGNORECASE)
                if content_match:
                    content_html = content_match.group(1)
                    
                    # 提取图片
                    img_tags = re.findall(r'<img[^>]+(?:data-src|src)=["\']([^"\']+)["\']', content_html, re.IGNORECASE)
                    for img_url in img_tags:
                        if img_url.startswith(('http://', 'https://')):
                            content_images.append(img_url)
                        elif img_url.startswith('//'):
                            content_images.append('https:' + img_url)
                    
                    # 提取文本
                    text_content = re.sub(r'<[^>]+>', '', content_html)
                    text_content = re.sub(r'\s+', ' ', text_content).strip()
                    text_content = text_content[:10000]
                    
                    if text_content and len(text_content) > 100:
                        break
            
            detail = {
                'url': article_url,
                'content': text_content,
                'content_images': content_images,
                'content_length': len(text_content),
                'image_count': len(content_images),
                'method': 'regex_fallback'
            }
            
            logger.info(f"回退方法获取成功: 文字长度 {len(text_content)}, 图片数量 {len(content_images)}")
            return detail
            
        except Exception as e:
            logger.error(f"回退方法也失败: {e}")
            return None


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 示例：使用保存的session数据
    session_data = {
        'token': 'your_token_here',
        'cookie': 'your_cookie_here'
    }
    
    crawler = WeChatAPICrawler(session_data)
    
    # 示例fakeid
    fakeid = 'your_fakeid_here'
    
    # 获取文章
    articles = crawler.get_all_articles(fakeid, max_count=10)
    
    print(f"\n获取到 {len(articles)} 篇文章:")
    for i, article in enumerate(articles, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   发布时间: {article['publish_time']}")
        print(f"   链接: {article['url']}")
