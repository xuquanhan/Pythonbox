# 微信爬虫增量爬取机制分析

## 1. 核心功能概述

微信爬虫实现了完整的增量爬取功能，能够：
- **检索历史库内容**：在获取新推送时，会检查数据库中已有的文章
- **自动去重**：避免重复爬取和存储相同的文章
- **增量更新**：只获取和处理新的或更新的文章
- **时间过滤**：基于数据库中最新文章的时间进行过滤

## 2. 增量爬取实现流程

### 2.1 初始化阶段

1. **加载监控公众号列表**：从 `config/wechat_accounts.json` 加载需要监控的公众号
2. **自动登录**：使用已保存的会话信息或扫码登录微信公众号平台
3. **获取公众号fakeid**：确保每个公众号都有对应的fakeid（用于API调用）

### 2.2 增量爬取核心流程

对于每个公众号：

1. **获取历史最新文章时间**：
   ```python
   # 获取该公众号的最新文章时间（用于增量爬取）
   latest_article = storage.get_latest_article_by_account(name)
   latest_time = latest_article.get('publish_time', '') if latest_article else ''
   
   if latest_time:
       print(f"[INFO] 数据库中最新的文章时间: {latest_time}")
       print(f"[INFO] 将只获取更新的文章...")
   ```

2. **获取公众号文章列表**：
   ```python
   # 获取文章
   articles = api_crawler.get_all_articles(fakeid, max_count=20)
   ```

3. **文章去重与增量处理**：
   - **URL去重**：通过数据库中的URL唯一性约束和 `article_exists` 方法检查
   - **时间过滤**：虽然API返回的文章已经按时间倒序排列，但仍会基于URL去重确保完整性

4. **文章详情获取**：
   - 对于每篇文章，无论是否已存在，都会获取详情以确保内容和图片信息完整
   - 实现了3次重试机制，提高成功率

5. **分类处理**：
   - **新文章**：保存到数据库，加入 `new_articles` 列表
   - **已存在文章**：更新内容和图片信息，加入 `updated_articles` 列表

6. **数据存储**：
   - 保存新文章到数据库
   - 更新已存在文章的内容和图片信息

## 3. 数据库设计与去重机制

### 3.1 表结构设计

```sql
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT,
    account_name TEXT,
    title TEXT,
    summary TEXT,
    content TEXT,
    url TEXT UNIQUE,  -- 关键：URL字段设置为UNIQUE
    publish_time TEXT,
    cover_image TEXT,
    content_images TEXT,  -- 存储正文中的图片URL，JSON格式
    reading_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    crawl_time TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
)
```

### 3.2 去重机制

1. **URL唯一性约束**：数据库表中 `url` 字段设置为 `UNIQUE`，确保不会重复插入相同URL的文章

2. **文章存在性检查**：
   ```python
   def article_exists(self, url: str) -> bool:
       """检查文章是否已存在"""
       try:
           conn = self._connect()
           cursor = conn.cursor()
           
           cursor.execute('''
               SELECT id FROM articles WHERE url = ?
           ''', (url,))
           
           exists = cursor.fetchone() is not None
           conn.close()
           return exists
       except Exception as e:
           self.logger.error(f"检查文章是否存在失败: {str(e)}")
           return False
   ```

3. **最新文章获取**：
   ```python
   def get_latest_article_by_account(self, account_name: str) -> Optional[Dict]:
       """获取指定公众号的最新文章"""
       try:
           conn = self._connect()
           conn.row_factory = sqlite3.Row
           cursor = conn.cursor()
           
           cursor.execute('''
               SELECT * FROM articles 
               WHERE account_name = ?
               ORDER BY publish_time DESC
               LIMIT 1
           ''', (account_name,))
           
           row = cursor.fetchone()
           # 处理结果...
           return article_dict if row else None
       except Exception as e:
           self.logger.error(f"获取最新文章失败: {str(e)}")
           return None
   ```

## 4. 技术实现细节

### 4.1 时间过滤机制

- **逻辑过滤**：虽然API返回的文章已经按时间倒序排列，但爬虫通过URL去重确保只处理新文章
- **效率优化**：通过检查数据库中最新文章时间，用户可以了解爬取范围，但实际去重仍依赖URL唯一性

### 4.2 文章更新机制

- **强制更新**：即使文章已存在，也会重新获取详情以确保内容和图片信息完整
- **内容增强**：对于已存在但内容不完整的文章（如缺少图片信息），会自动更新

### 4.3 错误处理与重试机制

- **网络错误处理**：实现了3次重试机制，每次失败后等待2秒
- **数据库错误处理**：捕获并记录数据库操作错误，确保爬取过程不会因局部错误而中断

## 5. 代码优化建议

### 5.1 性能优化

1. **添加索引**：为 `account_name` 和 `publish_time` 字段添加索引，加速查询
   ```sql
   CREATE INDEX IF NOT EXISTS idx_articles_account_name ON articles(account_name);
   CREATE INDEX IF NOT EXISTS idx_articles_publish_time ON articles(publish_time);
   ```

2. **批量操作**：对于更新操作，考虑使用批量更新以减少数据库连接次数

3. **缓存机制**：添加内存缓存，减少重复的数据库查询

### 5.2 功能增强

1. **时间戳标准化**：统一处理不同格式的时间戳，确保时间过滤的准确性

2. **增量爬取策略配置**：允许用户配置不同的增量爬取策略（如基于时间、基于数量等）

3. **失败恢复机制**：添加爬取状态记录，支持从中断点恢复爬取

## 6. 测试验证方法

### 6.1 功能测试

1. **首次爬取**：清空数据库后，运行爬虫，验证是否能正确爬取和存储所有文章

2. **增量爬取测试**：
   - 首次爬取后，等待一段时间（确保有新文章）
   - 再次运行爬虫，验证是否只获取新文章
   - 检查数据库，确保没有重复文章

3. **更新测试**：
   - 爬取某公众号的文章
   - 手动修改数据库中某篇文章的内容
   - 再次运行爬虫，验证是否能正确更新文章内容

### 6.2 性能测试

1. **大规模爬取测试**：监控10个以上公众号，测试爬取效率和内存使用

2. **并发测试**：测试多公众号并行爬取的性能

## 7. 总结

微信爬虫实现了完善的增量爬取机制，通过：

- **URL唯一性约束**：确保文章不会重复存储
- **文章存在性检查**：避免重复爬取
- **时间过滤**：提供爬取范围的参考
- **强制更新机制**：确保文章内容的完整性
- **错误处理与重试**：提高爬取的可靠性

这种实现方式既保证了数据的完整性和准确性，又提高了爬取效率，是一个设计合理的增量爬取系统。

## 8. 代码参考

### 8.1 核心函数

- **增量爬取入口**：`scripts/wechat_crawler_main.py` 中的 `crawl_accounts` 函数
- **文章存在性检查**：`modules/storage.py` 中的 `article_exists` 方法
- **最新文章获取**：`modules/storage.py` 中的 `get_latest_article_by_account` 方法
- **文章保存与更新**：`modules/storage.py` 中的 `save_article` 方法

### 8.2 关键SQL语句

- **检查文章是否存在**：
  ```sql
  SELECT id FROM articles WHERE url = ?
  ```

- **获取最新文章**：
  ```sql
  SELECT * FROM articles WHERE account_name = ? ORDER BY publish_time DESC LIMIT 1
  ```

- **文章表结构**：
  ```sql
  CREATE TABLE IF NOT EXISTS articles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ...
      url TEXT UNIQUE,  -- 关键：URL字段设置为UNIQUE
      ...
  )
  ```
