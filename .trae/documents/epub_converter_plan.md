# EPUB转Mobi翻译工具 - 项目计划

## 1. 项目概述

创建一个基于浏览器的Web工具，实现：
- **EPUB转Mobi**：将EPUB电子书转换为Amazon Kindle兼容的Mobi格式
- **智能翻译**：调用大语言模型API将非中文材料翻译成中文

## 2. 技术架构

### 前端
- **HTML/CSS/JavaScript**：简洁的Web界面
- **文件上传**：支持拖拽上传EPUB文件
- **进度显示**：实时显示转换/翻译进度

### 后端
- **框架**：Flask（轻量级，易于部署）
- **EPUB解析**：python-epub 或 ebooklib
- **Mobi生成**：KindleGen（命令行）或 Calibre（Python绑定）
- **翻译API**：OpenAI GPT / Anthropic Claude / 硅基流动（支持免费额度）

## 3. 项目结构

```
epub_converter/
├── data/
│   ├── raw/                 # 上传的EPUB文件
│   ├── converted/            # 转换后的Mobi文件
│   └── translated/          # 翻译后的EPUB/Mobi
├── static/                  # 前端静态资源
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/
│   └── index.html           # 主页面
├── tools/
│   ├── converter.py          # EPUB转Mobi核心逻辑
│   ├── epub_parser.py       # EPUB解析
│   └── translator.py        # 翻译模块
├── scripts/
│   └── server.py            # Flask服务器
├── tests/
│   └── test_converter.py    # 单元测试
├── README.md
├── requirements.txt
└── .env.example             # 环境变量示例
```

## 4. 功能模块

### 4.1 EPUB解析 (epub_parser.py)
- 读取EPUB文件结构
- 提取章节内容（HTML/XHTML）
- 获取元数据（书名、作者、语言）

### 4.2 格式转换 (converter.py)
- EPUB → HTML/文本
- HTML/文本 → Mobi
- 调用KindleGen或calibre命令

### 4.3 翻译模块 (translator.py)
- 检测原文语言
- 调用LLM API翻译
- 保持章节结构
- 支持流式输出（进度显示）

### 4.4 Web服务 (server.py)
- 文件上传接口
- 转换任务管理
- 下载接口

## 5. 核心API设计

### 翻译API选项
| 提供商 | 模型 | 免费额度 | 说明 |
|--------|------|----------|------|
| 硅基流动 | Qwen/DeepSeek | 有免费额度 | 中文支持好 |
| OpenAI | GPT-4o | 首次有余额 | 翻译质量高 |
| Anthropic | Claude | 暂无免费 | 速度快 |

### 后端接口
```
POST /api/upload          # 上传EPUB文件
POST /api/convert         # 开始转换
POST /api/translate       # 开始翻译
GET  /api/status/{task_id} # 查询进度
GET  /api/download/{file_id} # 下载文件
```

## 6. 实现步骤

### 第一阶段：基础转换功能
1. 创建项目目录结构
2. 实现EPUB解析模块
3. 实现EPUB→Mobi转换
4. 本地命令行测试

### 第二阶段：Web界面
1. 创建Flask后端
2. 编写前端页面
3. 实现文件上传/下载

### 第三阶段：翻译功能
1. 集成LLM API
2. 实现翻译逻辑
3. 流式输出进度

### 第四阶段：优化
1. 错误处理
2. 并发任务支持
3. 用户体验优化

## 7. 依赖项

```
Flask>=2.0
ebooklib>=0.17
python-mobi>=0.6
openai>=1.0
anthropic>=0.18
requests>=2.28
python-dotenv>=0.19
```

## 8. 部署方式

- 本地运行：`python scripts/server.py`
- Docker容器化（可选）
