# 微信公众号爬取工具

一个功能强大的微信公众号爬取工具，支持单公众号爬取、批量爬取和定时更新。

## 🎯 功能特点

- **单公众号爬取**：输入公众号名称，自动爬取所有历史文章
- **批量爬取**：从配置文件读取公众号列表，批量爬取多个公众号
- **定时更新**：定期检查并拉取新的推送
- **数据存储**：使用 SQLite 数据库存储文章内容
- **数据导出**：支持导出为 CSV、JSON、Excel 格式
- **自动去重**：避免重复爬取相同文章
- **错误处理**：完善的错误处理和重试机制
- **日志管理**：详细的日志记录

## 📁 项目结构

```
wechat_crawler/
├── data/              # 数据目录
│   ├── raw/           # 原始数据
│   ├── processed/     # 处理后的数据
│   └── db/            # 数据库文件
├── modules/           # 核心模块
│   ├── crawler.py     # 爬虫模块
│   ├── storage.py     # 存储模块
│   └── scheduler.py   # 定时任务模块
├── config/            # 配置文件
│   ├── config.yaml    # 主配置文件
│   └── accounts.yaml  # 公众号列表
├── scripts/           # 运行脚本
│   ├── single_crawl.py # 单公众号爬取
│   └── batch_crawl.py  # 批量爬取
├── utils/             # 工具函数
│   ├── tools.py       # 工具函数
│   └── logger.py      # 日志管理
├── logs/              # 日志文件
├── README.md          # 说明文档
└── requirements.txt   # 依赖文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置公众号列表

编辑 `config/accounts.yaml` 文件，添加要爬取的公众号：

```yaml
accounts:
  - name: "人民日报"
    id: ""
    last_update: ""
  - name: "新华社"
    id: ""
    last_update: ""
```

### 3. 单公众号爬取

```bash
# 交互式模式
python scripts/single_crawl.py

# 命令行模式
python scripts/single_crawl.py --name "人民日报" --export csv
```

### 4. 批量爬取

```bash
# 交互式模式
python scripts/batch_crawl.py

# 命令行模式
python scripts/batch_crawl.py --action crawl
```

### 5. 启动定时任务

```bash
python scripts/batch_crawl.py --action start
```

## ⚙️ 配置说明

### config.yaml

```yaml
# 爬虫配置
crawler:
  timeout: 30          # 请求超时时间
  retry_times: 3       # 重试次数
  sleep_interval: 2    # 爬取间隔
  max_articles: 1000   # 最大文章数
  headers:             # HTTP 请求头
    User-Agent: "Mozilla/5.0..."

# 定时任务配置
scheduler:
  check_interval: "1h"  # 检查间隔（1小时）
  max_workers: 3       # 最大并发数
  notify: false        # 是否发送通知

# 存储配置
storage:
  db_path: "data/db/wechat.db"
  batch_size: 100
  export_format: "csv"
  export_path: "data/processed"

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/wechat_crawler.log"
```

## 📊 数据结构

### 数据库表

- **accounts**：存储公众号信息
- **articles**：存储文章内容

### 文章字段

- title: 文章标题
- content: 文章内容
- url: 文章链接
- publish_time: 发布时间
- account_name: 公众号名称
- account_id: 公众号ID
- reading_count: 阅读数
- like_count: 点赞数
- crawl_time: 爬取时间

## 💡 使用示例

### 示例 1：爬取单个公众号

```bash
$ python scripts/single_crawl.py
请输入微信公众号名称: 人民日报

✅ 爬取成功！
公众号: 人民日报
时间: 2026-02-10 16:30:00
```

### 示例 2：批量爬取

```bash
$ python scripts/batch_crawl.py --action crawl
开始批量爬取...
发现 5 篇新文章
批量爬取完成
```

### 示例 3：管理公众号列表

```bash
$ python scripts/batch_crawl.py --action list

📋 公众号列表:
------------------------------------------------------------
1. 人民日报
   ID: gh_123456
   上次更新: 2026-02-10 16:30:00
------------------------------------------------------------
2. 新华社
   ID: gh_789012
   上次更新: 2026-02-10 16:25:00
------------------------------------------------------------
```

## 🔧 命令行参数

### single_crawl.py

| 参数 | 说明 |
|------|------|
| --name | 公众号名称 |
| --export | 导出格式 (csv/json/excel) |

### batch_crawl.py

| 参数 | 说明 |
|------|------|
| --action | 操作 (list/add/remove/crawl/start/stats) |

## 🚨 注意事项

1. **合规性**：请遵守微信公众平台的相关规定，合理使用爬取工具
2. **频率控制**：避免请求过快，导致IP被封禁
3. **数据存储**：定期清理数据库，避免数据过大
4. **依赖问题**：确保安装了所有必要的依赖
5. **网络环境**：确保网络连接稳定

## 📝 日志说明

- logs/app.log: 应用主日志
- logs/crawler.log: 爬虫日志
- logs/storage.log: 存储日志
- logs/scheduler.log: 定时任务日志
- logs/single_crawl.log: 单公众号爬取日志
- logs/batch_crawl.log: 批量爬取日志

## 🔍 故障排查

### 常见问题

1. **爬取失败**：检查网络连接和公众号名称是否正确
2. **导出失败**：检查导出目录权限
3. **定时任务不运行**：检查是否有其他进程占用
4. **数据库错误**：检查数据库文件权限

### 查看日志

```bash
# 查看最新日志
tail -f logs/app.log
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系

如有问题，请联系项目维护者。

---

**版本**：1.0.0
**更新时间**：2026-02-10
**作者**：AI Assistant
