# Trade Analysis - 股票交易分析系统

## 项目简介

本项目用于分析A股交易记录，提供交易统计、盈亏分析、持仓管理等功能。

## 功能特性

- 数据清洗：自动解析券商导出的结算数据
- 持仓追踪：FIFO先进先出法追踪持仓变化
- 盈亏计算：计算已实现盈亏、交易费用、股息收入等
- 报告生成：支持控制台、Excel、HTML多种输出格式
- 可视化：资金曲线、盈亏分布、持仓占比等图表

## 目录结构

```
trade_analysis/
├── data/                    # 数据目录
│   ├── raw/                 # 原始数据
│   └── processed/           # 处理后数据
├── models/                  # 分析模型
│   ├── data_cleaner.py      # 数据清洗
│   ├── position_tracker.py  # 持仓追踪
│   ├── profit_calculator.py # 盈亏计算
│   └── report_generator.py  # 报告生成
├── tools/                   # 工具模块
│   ├── data_loader.py       # 数据加载
│   ├── visualization.py     # 可视化
│   └── export_utils.py      # 导出工具
├── scripts/                 # 运行脚本
│   └── analyze_trades.py    # 主分析脚本
├── tests/                   # 测试代码
├── README.md
└── requirements.txt
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python scripts/analyze_trades.py --input data/raw/settlement.csv
```

## 数据格式

支持券商导出的结算数据CSV文件，字段包括：
- 交割日期、证券代码、证券名称、业务类型
- 成交价格、成交数量、成交金额
- 佣金、印花税、过户费、发生金额、剩余金额等

## 作者

PythonBox Project
