#!/usr/bin/env python3
"""
测试微信爬虫的增量爬取功能
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.storage import DataStorage

class TestIncrementalCrawling:
    """测试增量爬取功能"""
    
    def __init__(self):
        """初始化测试"""
        # 使用测试数据库
        self.test_db_path = os.path.join('data', 'db', 'wechat_test.db')
        self.test_db_path = os.path.abspath(self.test_db_path)
        
        # 确保测试数据库目录存在
        os.makedirs(os.path.dirname(self.test_db_path), exist_ok=True)
        
        # 删除旧的测试数据库
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        # 创建存储实例
        self.storage = DataStorage(self.test_db_path)
        print(f"测试数据库: {self.test_db_path}")
        print("=" * 80)
    
    def create_test_article(self, title, url, publish_time):
        """创建测试文章"""
        return {
            'title': title,
            'url': url,
            'account_name': '测试公众号',
            'publish_time': publish_time,
            'content': f"这是{title}的内容",
            'cover_image': 'https://example.com/cover.jpg',
            'crawl_time': datetime.now().isoformat()
        }
    
    def test_first_crawl(self):
        """测试首次爬取"""
        print("\n测试场景1: 首次爬取")
        print("-" * 60)
        
        # 创建测试文章
        test_articles = []
        base_time = datetime.now()
        
        for i in range(5):
            publish_time = (base_time - timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S')
            article = self.create_test_article(
                f"测试文章{i+1}",
                f"https://example.com/article{i+1}",
                publish_time
            )
            test_articles.append(article)
        
        # 保存文章
        for article in test_articles:
            self.storage.save_article(article)
            print(f"保存文章: {article['title']} ({article['publish_time']})")
        
        # 验证保存结果
        all_articles = self.storage.get_all_articles()
        print(f"\n数据库中文章总数: {len(all_articles)}")
        assert len(all_articles) == 5, f"预期5篇文章，实际{len(all_articles)}篇"
        
        # 验证最新文章
        latest_article = self.storage.get_latest_article_by_account('测试公众号')
        print(f"最新文章: {latest_article['title']} ({latest_article['publish_time']})")
        assert latest_article['title'] == '测试文章1', f"预期最新文章是测试文章1"
        
        print("✓ 首次爬取测试通过！")
    
    def test_incremental_crawl(self):
        """测试增量爬取"""
        print("\n测试场景2: 增量爬取")
        print("-" * 60)
        
        # 模拟已有文章（来自首次爬取）
        existing_count = len(self.storage.get_all_articles())
        print(f"爬取前数据库中文章数: {existing_count}")
        
        # 创建新文章（比现有文章更新）
        new_article = self.create_test_article(
            "新测试文章",
            "https://example.com/new_article",
            (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')  # 未来时间
        )
        
        # 创建重复文章（URL相同）
        duplicate_article = self.create_test_article(
            "重复测试文章",
            "https://example.com/article1",  # 与现有文章URL相同
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 保存新文章
        self.storage.save_article(new_article)
        print(f"保存新文章: {new_article['title']}")
        
        # 尝试保存重复文章
        self.storage.save_article(duplicate_article)
        print(f"尝试保存重复文章: {duplicate_article['title']}")
        
        # 验证结果
        final_count = len(self.storage.get_all_articles())
        print(f"爬取后数据库中文章数: {final_count}")
        assert final_count == existing_count + 1, f"预期新增1篇文章，实际新增{final_count - existing_count}篇"
        
        # 验证重复文章是否被正确处理
        article_by_url = self.storage.get_article_by_url("https://example.com/article1")
        print(f"重复URL的文章标题: {article_by_url['title']}")
        assert article_by_url['title'] == '测试文章1', f"预期标题不变"
        
        print("✓ 增量爬取测试通过！")
    
    def test_article_update(self):
        """测试文章更新"""
        print("\n测试场景3: 文章更新")
        print("-" * 60)
        
        # 获取现有文章
        existing_article = self.storage.get_article_by_url("https://example.com/article1")
        print(f"更新前文章标题: {existing_article['title']}")
        print(f"更新前文章内容: {existing_article['content']}")
        
        # 创建更新的文章
        updated_article = {
            'title': existing_article['title'],
            'url': existing_article['url'],
            'account_name': existing_article['account_name'],
            'publish_time': existing_article['publish_time'],
            'content': f"这是{existing_article['title']}的更新内容",  # 更新内容
            'cover_image': existing_article['cover_image'],
            'crawl_time': datetime.now().isoformat()
        }
        
        # 保存更新
        self.storage.save_article(updated_article)
        print(f"更新文章内容")
        
        # 验证更新结果
        updated_db_article = self.storage.get_article_by_url("https://example.com/article1")
        print(f"更新后文章内容: {updated_db_article['content']}")
        assert updated_db_article['content'] == updated_article['content'], f"预期内容已更新"
        
        print("✓ 文章更新测试通过！")
    
    def test_article_exists(self):
        """测试文章存在性检查"""
        print("\n测试场景4: 文章存在性检查")
        print("-" * 60)
        
        # 检查存在的文章
        exists = self.storage.article_exists("https://example.com/article1")
        print(f"检查存在的文章: {'存在' if exists else '不存在'}")
        assert exists, "预期文章存在"
        
        # 检查不存在的文章
        not_exists = self.storage.article_exists("https://example.com/nonexistent")
        print(f"检查不存在的文章: {'存在' if not_exists else '不存在'}")
        assert not not_exists, "预期文章不存在"
        
        print("✓ 文章存在性检查测试通过！")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始测试增量爬取功能")
        print("=" * 80)
        
        try:
            self.test_first_crawl()
            self.test_incremental_crawl()
            self.test_article_update()
            self.test_article_exists()
            
            print("\n" + "=" * 80)
            print("🎉 所有测试通过！")
            print("增量爬取功能工作正常！")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 清理测试数据库
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
                print(f"\n清理测试数据库: {self.test_db_path}")

if __name__ == "__main__":
    test = TestIncrementalCrawling()
    test.run_all_tests()
