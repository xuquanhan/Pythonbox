#!/usr/bin/env python3
"""检查当前数据库内容"""
import sqlite3
import os

os.chdir('C:\\Dev\\PythonBox\\wechat_crawler')

if not os.path.exists('data/db/wechat.db'):
    print("数据库不存在")
    exit()

conn = sqlite3.connect('data/db/wechat.db')
cursor = conn.cursor()

# 检查表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
if not cursor.fetchone():
    print("articles表不存在")
    conn.close()
    exit()

# 查看文章数量
cursor.execute("SELECT COUNT(*) FROM articles")
count = cursor.fetchone()[0]
print(f"文章总数: {count}\n")

if count == 0:
    print("数据库为空")
    conn.close()
    exit()

# 查看前2篇文章
cursor.execute("SELECT title, summary, content, url FROM articles LIMIT 2")
rows = cursor.fetchall()

for i, (title, summary, content, url) in enumerate(rows, 1):
    print(f"\n{'='*60}")
    print(f"文章 {i}: {title}")
    print(f"{'='*60}")
    print(f"URL: {url[:80]}...")
    print(f"\nSummary: {summary[:200] if summary else 'None'}...")
    print(f"\nContent长度: {len(content) if content else 0}")
    if content:
        print(f"Content前300字: {content[:300]}...")
    else:
        print("Content: None/Empty")

conn.close()
