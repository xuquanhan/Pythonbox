#!/usr/bin/env python3
"""检查数据库真实状态"""
import sqlite3
import os

os.chdir('C:\\Dev\\PythonBox\\wechat_crawler')

print("="*60)
print("数据库状态检查")
print("="*60)

# 检查文件是否存在
if not os.path.exists('data/db/wechat.db'):
    print("\n数据库文件不存在")
    exit()

# 检查文件大小
file_size = os.path.getsize('data/db/wechat.db')
print(f"\n数据库文件: data/db/wechat.db")
print(f"文件大小: {file_size} 字节")

if file_size == 0:
    print("\n数据库文件为空（0字节）")
    print("需要运行主程序初始化数据库")
    exit()

# 连接数据库检查表
conn = sqlite3.connect('data/db/wechat.db')
cursor = conn.cursor()

# 检查articles表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
if not cursor.fetchone():
    print("\narticles表不存在")
    conn.close()
    exit()

# 查看文章数量
cursor.execute("SELECT COUNT(*) FROM articles")
count = cursor.fetchone()[0]
print(f"\n文章数量: {count}")

if count > 0:
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
else:
    print("\n数据库已初始化，但没有文章数据")

conn.close()
