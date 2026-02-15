#!/usr/bin/env python3
"""
检查数据库中文章的content字段
"""

import sqlite3
import os

db_path = 'data/db/wechat.db'

if not os.path.exists(db_path):
    print(f"数据库文件不存在: {db_path}")
    exit(1)

print("检查数据库中的文章内容...")
print("="*60)

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 首先检查articles表的结构
    print("Articles表结构:")
    cursor.execute("PRAGMA table_info(articles)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    print()
    
    # 查询丹湖渔翁的文章
    print("丹湖渔翁的文章:")
    print("文章标题 | content长度")
    print("-"*60)
    
    cursor.execute('''
        SELECT title, content 
        FROM articles 
        WHERE account_name = ? 
        LIMIT 5
    ''', ('丹湖渔翁',))
    
    rows = cursor.fetchall()
    
    if not rows:
        print("没有找到丹湖渔翁的文章")
    else:
        for row in rows:
            title = row['title']
            content = row['content']
            
            content_len = len(content) if content else 0
            
            print(f"{title[:20]}... | {content_len}")
            
            # 打印前100个字符的content内容
            if content:
                print(f"  内容预览: {content[:100]}...")
            else:
                print("  内容: 空")
            print()
    
    conn.close()
    
    print("="*60)
    print("检查完成")
    
except Exception as e:
    print(f"检查失败: {e}")
