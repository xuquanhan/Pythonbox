#!/usr/bin/env python3
"""
测试获取文章详情的功能
"""

import os
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.wechat_auto_login_simple import WeChatAutoLoginSimple
from modules.wechat_api_crawler import WeChatAPICrawler

# 加载会话信息
session_file = 'config/wechat_session.json'

if not os.path.exists(session_file):
    print(f"会话文件不存在: {session_file}")
    print("请先运行主程序登录")
    exit(1)

print("测试获取文章详情...")
print("="*60)

# 加载会话信息
try:
    with open(session_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    print("成功加载会话信息")
except Exception as e:
    print(f"加载会话信息失败: {e}")
    exit(1)

# 创建API爬虫
api_crawler = WeChatAPICrawler(session_data)

# 测试文章链接
article_url = "http://mp.weixin.qq.com/s?__biz=MzAwNjAwNTc3Ng==&mid=2448834608&idx=1&sn=d6120fe3844501cb48a3325365da8c49&chksm=8f11154fb8669c59df5758f231a08f2f7b640cdf48c8cd3b4e20640195345b6d2d94ba798b73#rd"

print(f"测试文章: {article_url}")
print()

# 获取文章详情
try:
    detail = api_crawler.get_article_detail(article_url)
    print("获取文章详情成功")
    print(f"返回的字段: {list(detail.keys())}")
    print()
    
    if 'content' in detail:
        content = detail['content']
        print(f"Content长度: {len(content)}")
        if content:
            print(f"Content预览: {content[:200]}...")
        else:
            print("Content为空")
    else:
        print("返回结果中没有content字段")
        
    print()
    print("="*60)
    print("测试完成")
    
except Exception as e:
    print(f"获取文章详情失败: {e}")
    import traceback
    traceback.print_exc()
