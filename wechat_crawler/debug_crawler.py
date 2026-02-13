#!/usr/bin/env python3
"""
调试脚本：检查搜狗微信搜索页面结构
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.crawler import WeChatCrawler
import time

def debug_search():
    """调试搜索功能"""
    print("=" * 60)
    print("调试微信爬虫 - 检查页面结构")
    print("=" * 60)
    
    crawler = WeChatCrawler()
    
    # 初始化浏览器
    driver = crawler._init_driver()
    if not driver:
        print("[ERROR] 无法初始化浏览器")
        return
    
    try:
        # 访问搜狗微信搜索
        import urllib.parse
        search_name = "人民日报"
        encoded_name = urllib.parse.quote(search_name)
        search_url = f"https://weixin.sogou.com/weixin?type=1&query={encoded_name}"
        
        print(f"\n[INFO] 访问搜索页面: {search_url}")
        driver.get(search_url)
        time.sleep(5)  # 等待页面加载
        
        # 保存页面源码
        page_source = driver.page_source
        with open("debug_page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("[INFO] 页面源码已保存到 debug_page_source.html")
        
        # 尝试多种选择器
        print("\n[INFO] 检查页面元素...")
        
        # 检查公众号列表
        selectors_to_try = [
            '.news-box .wx-rb',
            '.news-list .news-item',
            '.weixin-search-result .result-item',
            '.snbg .wx-rb',
            '.results .result',
            '.result-list .result-item',
            '[class*="account"]',
            '[class*="wx-"]',
        ]
        
        print("\n尝试查找公众号元素:")
        for selector in selectors_to_try:
            try:
                elements = driver.find_elements("css selector", selector)
                print(f"  {selector}: 找到 {len(elements)} 个元素")
                if elements:
                    print(f"    第一个元素文本: {elements[0].text[:100] if elements[0].text else '空'}")
            except Exception as e:
                print(f"  {selector}: 失败 - {str(e)}")
        
        # 检查文章列表（type=2）
        print("\n[INFO] 检查文章搜索结果...")
        article_search_url = f"https://weixin.sogou.com/weixin?type=2&query={encoded_name}"
        driver.get(article_search_url)
        time.sleep(5)
        
        # 保存文章页面源码
        article_page_source = driver.page_source
        with open("debug_article_page.html", "w", encoding="utf-8") as f:
            f.write(article_page_source)
        print("[INFO] 文章页面源码已保存到 debug_article_page.html")
        
        # 尝试查找文章
        article_selectors = [
            '.news-box .wx-rb',
            '.news-list li',
            '.result-list .result',
            '.txt-box h3',
            '.snbg .wx-rb',
        ]
        
        print("\n尝试查找文章元素:")
        for selector in article_selectors:
            try:
                elements = driver.find_elements("css selector", selector)
                print(f"  {selector}: 找到 {len(elements)} 个元素")
                if elements:
                    print(f"    第一个元素文本: {elements[0].text[:100] if elements[0].text else '空'}")
            except Exception as e:
                print(f"  {selector}: 失败 - {str(e)}")
        
        print("\n" + "=" * 60)
        print("调试完成，请检查生成的HTML文件")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] 调试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        crawler._close_driver()

if __name__ == "__main__":
    debug_search()
