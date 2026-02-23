# Trading Economics 爬虫项目

## 项目简介

本项目用于爬取 Trading Economics 网站上的财经日历数据，包括经济指标发布、重要新闻事件等信息。

## 功能特性

- 自动登录 Trading Economics 网站
- 根据时间段筛选财经事件（昨天、上周、今天、明天、本周、下周、本月、下月）
- 根据重要程度筛选新闻（普通、重要、十分重要）
- 选择特定国家/地区的数据（中国、欧元区、美国）
- 自动提取事件详细描述
- **使用 Qwen API 进行国别经济分析**（中、美、欧）
- **使用 Qwen API 进行专业财经翻译**
- 导出结果为 Word 文档

## 目录结构

```
trading_economics/
├── data/                    # 数据目录
│   ├── raw/                # 原始爬取数据
│   └── processed/          # 处理后的数据
├── models/                 # 数据模型和分析模型
├── tools/                  # 工具脚本
├── scripts/                # 运行脚本
│   ├── trading_econ_crawler.py    # 【主程序】Qwen翻译版爬虫
│   ├── TradingEcon_HomeDesktop.py # 旧版爬虫（Ollama翻译）
│   └── TradingEcon_Fixed_20260111_Qwen_translation.py # 原始版本
├── tests/                  # 测试代码
├── README.md              # 项目文档
└── requirements.txt       # 项目依赖
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

### 1. Edge WebDriver 配置

确保 Edge WebDriver 路径正确：

```python
service = Service('C:\msedgedriver\msedgedriver.exe')
```

### 2. Qwen API 配置（可选）

如需使用翻译和国别分析功能，需要设置环境变量：

```bash
set DASHSCOPE_API_KEY_Qwen=your_api_key_here
```

获取 API Key：[阿里云 DashScope](https://dashscope.aliyun.com/)

## 使用方法

### 主程序（推荐）

```bash
python scripts/trading_econ_crawler.py
```

程序会依次弹出对话框询问：
1. **时间段**：-1为昨天，-2为上周，1为今天，2为明天，3为本周，4为下周，5为本月，6为下月
2. **重要程度**：1为普通，2为重要，3为十分重要

然后自动：
- 选择中国、欧元区、美国三个地区
- 爬取所有符合条件的财经事件
- 使用 Qwen API 进行国别经济分析
- 使用 Qwen API 翻译为中文
- 保存为 Word 文档

### 输出文件

- **保存位置**：`C:\Users\<用户名>\Documents\TradingEconTransRawData\`
- **文件名格式**：`YYYY-MM-DD_pyTED.doc`
- **文档内容**：
  1. 英文原文
  2. 国别经济数据分析总结（中、美、欧）
  3. 中文翻译

## 依赖列表

| 包名 | 用途 |
|------|------|
| selenium | Web 自动化 |
| beautifulsoup4 | HTML 解析 |
| python-docx | Word 文档生成 |
| requests | HTTP 请求 |
| lxml | XML/HTML 解析器 |
| pyperclip | 剪贴板操作 |
| dashscope | 阿里云 Qwen API |

## 注意事项

1. **需要安装 Edge 浏览器和对应版本的 WebDriver**
2. **翻译和国别分析功能需要配置 Qwen API Key**（可选）
3. **爬取过程中请勿关闭浏览器窗口**
4. **请遵守 Trading Economics 网站的使用条款**
5. **Qwen API 调用会产生费用，请注意使用量**

## 版本历史

- **v2.0** (当前)：使用 Qwen API 进行翻译和国别分析，使用 requests 替代 Selenium 获取详情页，性能大幅提升
- **v1.0**：使用 Ollama 本地模型进行翻译

## 作者

Created for PythonBox Project
