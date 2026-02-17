# Wind服务号专属爬虫使用指南

## 1. 功能概述

Wind服务号专属爬虫是一个专门为获取Wind服务号推送内容而设计的脚本，具有以下功能：

- **自动登录**：自动登录微信公众号平台，支持保存会话信息
- **服务号识别**：自动搜索并获取Wind服务号的fakeid
- **内容获取**：获取Wind服务号推送的定制新闻和报告
- **内容提取**：提取文章完整内容和图片
- **多种格式**：支持保存为JSON、CSV、TXT等便于后续操作的格式
- **定时运行**：支持自动运行模式，定时获取新推送
- **数据存储**：同时保存到数据库和文件系统，便于后续操作

## 2. 安装与准备

### 2.1 环境要求

- Python 3.7+
- 已安装微信爬虫的依赖包（见`requirements.txt`）
- 可访问微信公众号平台的网络环境
- 微信账号（用于扫码登录）

### 2.2 安装步骤

1. **克隆或下载**微信爬虫项目到本地
2. **安装依赖**：
   ```bash
   cd wechat_crawler
   pip install -r requirements.txt
   ```
3. **确保目录结构完整**：
   - `config/`：配置文件目录
   - `data/wind/`：Wind服务号内容输出目录
   - `logs/`：日志文件目录

## 3. 快速开始

### 3.1 首次运行

1. **启动脚本**：
   ```bash
   cd wechat_crawler
   python scripts/wind_service_crawler.py
   ```

2. **登录微信**：
   - 脚本会自动打开浏览器并显示二维码
   - 使用微信扫码登录
   - 登录成功后，脚本会自动获取token和cookie

3. **配置Wind服务号**：
   - 首次运行时，脚本会自动搜索"Wind万得"服务号
   - 如果搜索不到，会提示手动输入服务号名称
   - 成功获取fakeid后，会自动保存到配置文件

4. **获取内容**：
   - 脚本会自动获取Wind服务号的最新文章
   - 提取文章内容和图片
   - 保存为配置的格式（默认为JSON）

### 3.2 运行示例

```bash
# 运行一次爬虫
python scripts/wind_service_crawler.py

# 选择操作选项
请输入选项 (1-4): 1

# 运行过程
运行Wind服务号爬虫...
开始登录微信公众号平台...
使用已保存的登录会话
搜索Wind服务号: Wind万得
获取到Wind服务号fakeid: abcdef123456
获取Wind服务号文章，最多获取10篇
成功获取 5 篇Wind服务号文章
提取文章内容: Wind万得：2026年2月15日市场要闻
提取文章内容: Wind万得：2026年2月14日市场回顾
文章保存成功: data/wind/wind_20260215_100000_Wind万得：2026年2月15日市场要闻.json
文章保存成功: data/wind/wind_20260214_180000_Wind万得：2026年2月14日市场回顾.json
Wind服务号爬虫运行完成，保存了2个文件

成功保存以下文件:
  - data/wind/wind_20260215_100000_Wind万得：2026年2月15日市场要闻.json
  - data/wind/wind_20260214_180000_Wind万得：2026年2月14日市场回顾.json
```

## 4. 配置选项

### 4.1 配置文件

脚本会在首次运行时自动创建配置文件 `config/wind_service_config.json`，内容如下：

```json
{
  "wind_service_name": "Wind万得",
  "wind_fakeid": "abcdef123456",
  "output_format": "json",
  "output_dir": "data/wind",
  "max_articles": 10,
  "auto_run": false,
  "run_interval": 3600
}
```

### 4.2 配置参数说明

| 参数 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| wind_service_name | Wind服务号名称 | "Wind万得" | 服务号实际名称 |
| wind_fakeid | Wind服务号的fakeid | "" | 自动获取或手动输入 |
| output_format | 输出文件格式 | "json" | json, csv, txt |
| output_dir | 输出文件目录 | "data/wind" | 任意有效路径 |
| max_articles | 最大获取文章数 | 10 | 正整数 |
| auto_run | 是否自动运行 | false | true, false |
| run_interval | 自动运行间隔（秒） | 3600 | 正整数 |

### 4.3 手动配置

可以通过以下方式修改配置：

1. **直接编辑配置文件**：修改 `config/wind_service_config.json`
2. **运行时配置**：启动脚本后选择"3. 更新配置"

## 5. 输出格式说明

### 5.1 JSON格式

**特点**：包含完整的文章信息，便于后续程序处理

**文件示例**：`wind_20260215_100000_Wind万得：市场要闻.json`

**内容结构**：
```json
{
  "title": "Wind万得：2026年2月15日市场要闻",
  "url": "http://mp.weixin.qq.com/s?__biz=...",
  "publish_time": "2026-02-15 10:00:00",
  "account_name": "Wind万得",
  "content": "完整的文章内容...",
  "content_images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
  "content_length": 5000,
  "crawl_time": "2026-02-15T12:00:00",
  "extraction_method": "js_content"
}
```

### 5.2 TXT格式

**特点**：纯文本格式，便于阅读和简单处理

**文件示例**：`wind_20260215_100000_Wind万得：市场要闻.txt`

**内容结构**：
```
标题: Wind万得：2026年2月15日市场要闻
发布时间: 2026-02-15 10:00:00
URL: http://mp.weixin.qq.com/s?__biz=...
服务号: Wind万得

================================================================================

完整的文章内容...
```

### 5.3 CSV格式

**特点**：表格格式，便于数据分析和Excel处理

**文件**：`data/wind/wind_articles.csv`（追加模式）

**内容结构**：
```csv
标题,发布时间,URL,服务号,内容长度
Wind万得：2026年2月15日市场要闻,2026-02-15 10:00:00,http://mp.weixin.qq.com/s?__biz=...,Wind万得,5000
Wind万得：2026年2月14日市场回顾,2026-02-14 18:00:00,http://mp.weixin.qq.com/s?__biz=...,Wind万得,4500
```

## 6. 自动运行模式

### 6.1 启动自动运行

1. **运行脚本**：
   ```bash
   python scripts/wind_service_crawler.py
   ```

2. **选择选项**：
   - 选择"2. 启动自动运行模式"
   - 按提示输入配置（可选）

3. **运行间隔**：
   - 默认每小时运行一次
   - 可在配置文件中修改 `run_interval` 参数

### 6.2 后台运行

在Linux或Mac系统中，可以使用nohup命令后台运行：

```bash
nohup python scripts/wind_service_crawler.py > wind_crawler.log 2>&1 &
```

在Windows系统中，可以创建批处理文件或使用任务计划程序。

## 7. 后续操作建议

### 7.1 数据处理

获取的Wind服务号内容可以用于以下操作：

1. **市场分析**：分析市场要闻和行业报告
2. **数据提取**：从报告中提取关键数据
3. **趋势分析**：分析Wind服务号推送内容的趋势
4. **自动化报告**：基于Wind内容生成自动化报告
5. **监控提醒**：监控特定关键词的出现

### 7.2 示例代码

**读取JSON文件**：
```python
import json

# 读取Wind服务号内容
with open('data/wind/wind_20260215_100000_Wind万得：市场要闻.json', 'r', encoding='utf-8') as f:
    article = json.load(f)

# 提取标题和内容
title = article['title']
content = article['content']
publish_time = article['publish_time']

print(f"标题: {title}")
print(f"发布时间: {publish_time}")
print(f"内容长度: {len(content)}字")
```

**读取CSV文件**：
```python
import pandas as pd

# 读取Wind服务号内容
df = pd.read_csv('data/wind/wind_articles.csv')

# 查看最近的文章
print(df.tail())

# 按发布时间排序
df['发布时间'] = pd.to_datetime(df['发布时间'])
df_sorted = df.sort_values('发布时间', ascending=False)

print("最近的5篇文章:")
print(df_sorted.head())
```

## 8. 常见问题与解决方案

### 8.1 登录问题

**问题**：登录失败或二维码不显示

**解决方案**：
- 确保网络可访问微信公众号平台
- 检查浏览器驱动是否正确安装
- 尝试手动登录后再运行脚本

### 8.2 服务号识别问题

**问题**：搜索不到Wind服务号

**解决方案**：
- 确认服务号名称正确
- 尝试在微信中手动搜索服务号，确认存在
- 在脚本运行时选择手动输入服务号名称

### 8.3 内容获取问题

**问题**：获取的内容不完整或为空

**解决方案**：
- 检查网络连接
- 确认Wind服务号确实有推送内容
- 尝试重新登录后再运行

### 8.4 自动运行问题

**问题**：自动运行模式下程序崩溃

**解决方案**：
- 检查日志文件，查看具体错误
- 确保网络稳定
- 适当调整运行间隔

## 9. 高级功能

### 9.1 自定义服务号

除了Wind服务号，脚本也可以用于其他服务号：

1. **修改配置文件**：
   ```json
   {
     "wind_service_name": "其他服务号名称",
     "wind_fakeid": "",
     "output_dir": "data/other_service"
   }
   ```

2. **运行脚本**：脚本会自动搜索并获取新服务号的fakeid

### 9.2 集成到其他系统

可以将Wind服务号爬虫集成到其他系统：

```python
from scripts.wind_service_crawler import WindServiceCrawler

# 初始化爬虫
crawler = WindServiceCrawler('config/custom_config.json')

# 运行一次
crawler.login()
articles = crawler.get_wind_articles()
processed_articles = [crawler.extract_article_content(article) for article in articles]
saved_files = crawler.save_articles(processed_articles)

print(f"成功获取并保存 {len(saved_files)} 个文件")
```

### 9.3 自定义输出格式

可以通过修改脚本中的 `save_articles` 方法添加自定义输出格式，例如：

- **Excel格式**：保存为.xlsx文件
- **数据库格式**：保存到其他数据库系统
- **API格式**：直接推送到其他API

## 10. 监控与维护

### 10.1 日志文件

脚本会生成以下日志文件：

- `logs/wind_crawler.log`：Wind服务号爬虫日志
- `logs/wechat_crawler.log`：微信爬虫通用日志

### 10.2 定期维护

- **会话更新**：微信登录会话有效期约为7天，过期后需要重新登录
- **依赖更新**：定期更新依赖包，确保兼容性
- **配置检查**：定期检查配置文件，确保服务号信息正确

### 10.3 性能优化

- **减少获取数量**：如果只需要最新内容，可减少 `max_articles`
- **调整运行间隔**：根据Wind服务号推送频率调整 `run_interval`
- **选择合适格式**：根据后续操作需求选择输出格式

## 11. 总结

Wind服务号专属爬虫为用户提供了一种便捷的方式来获取和处理Wind服务号的推送内容，具有以下优势：

- **专门化**：专为Wind服务号设计，针对性强
- **自动化**：从登录到获取、提取、保存全流程自动化
- **灵活**：支持多种输出格式和运行模式
- **可扩展**：易于集成到其他系统或扩展功能

通过合理配置和使用，可以将Wind服务号的内容转化为有价值的信息资源，为市场分析、投资决策等提供支持。