#!/usr/bin/env python3
"""
更新数据库表结构，添加content_images字段
"""

import sqlite3
import os

# 数据库路径
db_path = os.path.join('data', 'db', 'wechat.db')
db_path = os.path.abspath(db_path)

def update_db_schema():
    """更新数据库表结构，添加content_images字段"""
    print(f"更新数据库: {db_path}")
    print("=" * 80)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查content_images字段是否存在
        cursor.execute('PRAGMA table_info(articles)')
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'content_images' not in columns:
            print("添加content_images字段...")
            # 添加content_images字段
            cursor.execute('ALTER TABLE articles ADD COLUMN content_images TEXT')
            conn.commit()
            print("content_images字段添加成功！")
        else:
            print("content_images字段已存在，跳过添加。")
        
        # 显示所有字段
        print("\n当前articles表字段:")
        cursor.execute('PRAGMA table_info(articles)')
        for column in cursor.fetchall():
            print(f"  - {column[1]} ({column[2]})")
        
        conn.close()
        print("\n" + "=" * 80)
        print("数据库更新完成！")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    update_db_schema()
