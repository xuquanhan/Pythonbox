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
            "type": "9",
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
            response = requests.get(article_url, headers=headers, timeout=20)
            
            if response.status_code != 200:
                logger.error(f"获取文章详情失败: {response.status_code}")
                return None
            
            # 从页面中提取文章内容
            html_content = response.text
            
            # 尝试从HTML中提取文章正文
            import re
            
            text_content = ""
            content_images = []
            
            # 方法1: 查找 #js_content
            content_match = re.search(r'<div[^>]*id=["\']js_content["\'][^>]*>(.*?)</div>\s*(?:<script|</div>|</body>)', html_content, re.DOTALL | re.IGNORECASE)
            
            if not content_match:
                # 方法2: 查找 rich_media_content
                content_match = re.search(r'<div[^>]*class=["\']rich_media_content[^"\']*["\'][^>]*>(.*?)</div>\s*(?:<script|</div>|</body>)', html_content, re.DOTALL | re.IGNORECASE)
            
            if content_match:
                content_html = content_match.group(1)
                
                # 提取正文中的图片
                img_tags = re.findall(r'<img[^>]+data-src=["\']([^"\']+)["\']', content_html, re.IGNORECASE)
                if not img_tags:
                    img_tags = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content_html, re.IGNORECASE)
                
                for img_url in img_tags:
                    if img_url.startswith('http'):
                        content_images.append(img_url)
                
                # 移除HTML标签获取纯文本
                text_content = re.sub(r'<[^>]+>', '', content_html)
                # 清理空白字符
                text_content = re.sub(r'\s+', ' ', text_content).strip()
                # 限制内容长度
                text_content = text_content[:10000]
            
            detail = {
                'url': article_url,
                'content': text_content,
                'content_images': content_images
            }
            
            logger.info(f"获取文章详情成功: 文字长度 {len(text_content)}, 图片数量 {len(content_images)}")
            return detail
            
        except requests.exceptions.Timeout:
            logger.warning(f"获取文章详情超时: {article_url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"获取文章详情请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取文章详情失败: {e}")
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
