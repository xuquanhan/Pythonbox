# PythonBox

PythonBox 是一个金融数据分析和爬虫项目的集合，包含多个独立的子项目。

## 项目结构

```
PythonBox/
├── trade_analysis/          # 交易分析系统
├── trading_economics/       # Trading Economics 爬虫
├── wechat_crawler/          # 微信公众号爬虫
├── financial_models/        # 金融模型（LPPL、HP-Filter等）
├── fed_data_processing/     # 美联储数据处理
├── data_analysis/           # 数据分析工具
├── encoding_tools/          # 编码修复工具
└── config/                  # 全局配置文件
```

## 子项目说明

### 1. trade_analysis - 交易分析系统
个人交易记录分析和盈亏计算工具。

**功能：**
- 导入券商交割单数据
- 计算持仓成本和盈亏
- 生成交易分析报告（Excel/HTML）
- 支持多数据源价格获取（Wind/Bloomberg/AkShare）

**快速开始：**
```bash
cd trade_analysis
python main.py
```

### 2. trading_economics - Trading Economics 爬虫
爬取 Trading Economics 网站财经日历数据。

**功能：**
- 自动筛选时间段和重要程度
- 选择特定国家/地区数据
- 提取事件详细描述
- 导出为 Word 文档

**快速开始：**
```bash
cd trading_economics
python scripts/TradingEcon_HomeDesktop.py
```

### 3. wechat_crawler - 微信公众号爬虫
自动化获取微信公众号文章。

**功能：**
- 自动登录微信
- 获取指定公众号文章列表
- 下载文章内容并保存为 Word
- 支持 Wind 消息服务

### 4. financial_models - 金融模型
各种金融分析模型的实现。

**包含模型：**
- LPPL（对数周期幂律）模型 - 泡沫检测
- HP-Filter - 趋势分解

### 5. fed_data_processing - 美联储数据处理
美联储公开数据的爬取和处理。

### 6. data_analysis - 数据分析工具
通用的数据分析脚本和工具。

### 7. encoding_tools - 编码修复工具
处理各种中文编码问题的工具集合。

## 全局文档

- [WIND_PY_INSTALL_GUIDE.md](WIND_PY_INSTALL_GUIDE.md) - WindPy 安装配置指南

## 开发规范

每个子项目都是独立的，包含：
- `data/` - 数据文件（raw/ 和 processed/）
- `scripts/` - 运行脚本
- `tools/` - 工具脚本
- `README.md` - 项目文档
- `requirements.txt` - 依赖配置

## 环境要求

- Python 3.8+
- 各子项目的依赖见各自的 requirements.txt

## 注意事项

1. 各子项目相互独立，可以单独运行
2. 数据文件统一存放在各项目的 `data/` 目录下
3. 配置文件存放在 `config/` 目录（全局）或各项目的 `config/` 目录（局部）
