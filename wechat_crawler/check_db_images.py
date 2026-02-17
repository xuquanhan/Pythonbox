#!/usr/bin/env python3
"""
检查数据库中文章的图片信息
"""

import sqlite3
import os
import json

# 数据库路径
db_path = os.path.join('data', 'db', 'wechat.db')
db_path = os.path.abspath(db_path)

def check_db_images():
    """检查数据库中文章的图片信息"""
    print(f"检查数据库: {db_path}")
    print("=" * 80)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取文章总数
        cursor.execute('SELECT COUNT(*) FROM articles')
        total_articles = cursor.fetchone()[0]
        print(f"总文章数: {total_articles}")
        print("=" * 80)
        
        # 获取所有文章的信息
        cursor.execute('''
            SELECT id, title, content, cover_image, publish_time
            FROM articles
            ORDER BY publish_time DESC
        ''')
        
        articles = cursor.fetchall()
        
        for i, article in enumerate(articles[:10], 1):  # 只显示前10篇
            article_id = article['id']
            title = article['title']
            content = article['content']
            cover_image = article['cover_image']
            publish_time = article['publish_time']
            
            # 检查content中是否包含图片URL
            has_images_in_content = 'http' in content and 'img' in content.lower()
            
            print(f"\n{i}. {title[:60]}...")
            print(f"   发布时间: {publish_time}")
            print(f"   封面图片: {'有' if cover_image else '无'}")
            print(f"   内容长度: {len(content)} 字符")
            print(f"   内容中包含图片URL: {'是' if has_images_in_content else '否'}")
            
            # 提取内容中的图片URL
            if has_images_in_content:
                # 简单提取图片URL
                import re
                img_urls = re.findall(r'https?://[^\s]+?(?=(?:\s|$))', content)
                img_urls = [url for url in img_urls if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])]
                if img_urls:
                    print(f"   提取到 {len(img_urls)} 个图片URL")
                    for j, img_url in enumerate(img_urls[:3], 1):  # 只显示前3个
                        print(f"     {j}. {img_url[:80]}...")
        
        conn.close()
        print("\n" + "=" * 80)
        print("检查完成！")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    check_db_images()
