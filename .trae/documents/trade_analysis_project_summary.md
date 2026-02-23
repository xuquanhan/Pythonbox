# 交易分析项目总结

## 项目概述

开发一个股票交易分析工具，用于导入清算数据、计算账户净值、分析最大回撤等。

## 项目结构

```
C:\Dev\PythonBox\trade_analysis\
├── __init__.py
├── main.py                          # 主程序入口
├── config.py                        # 配置文件
├── db\                              # 数据库模块
│   ├── __init__.py
│   └── database.py                  # SQLite数据库管理
├── models\                          # 数据模型
│   ├── __init__.py
│   ├── data_cleaner.py              # 数据清洗
│   └── record_parser.py             # 记录解析
├── services\                        # 服务层
│   ├── __init__.py
│   ├── data_manager.py              # 数据管理（净值计算、回撤分析）
│   ├── price_fetcher.py             # 多数据源价格获取
│   └── report_generator.py          # 报告生成
└── utils\                           # 工具函数
    └── __init__.py

数据目录:
├── data\                            # 数据目录
│   ├── raw\                         # 原始清算文件
│   │   └── 2025_2026settlement.xls
│   └── trade_data.db                # SQLite数据库
└── output\                          # 输出目录
```

## 已完成的功能

### 1. 数据导入模块 ✅
- 支持导入 Excel 清算文件（.xls/.xlsx）
- 自动解析交易记录（买入、卖出、逆回购、转账等）
- 增量更新数据库

### 2. 数据库模块 ✅
- SQLite 数据库设计
- 交易记录表（trade_records）
- 每日净值表（daily_net_values）
- 股票价格表（daily_prices）

### 3. 净值计算模块 ✅
- **计算公式**: 净值 = 现金余额 + 逆回购借出 + 持仓市值
- 自动计算每日账户净值
- 支持重新计算所有净值

### 4. 最大回撤计算 ✅
- **阶段性回撤逻辑**: 净值回升时重置回撤段
- 计算所有回撤段
- 找出最大回撤

### 5. 多数据源价格获取 ✅
已实现的数据源（按优先级）：

| 优先级 | 数据源 | 状态 | 说明 |
|--------|--------|------|------|
| 1 | Wind API | ✅ 可用 | 需要 Wind 终端 |
| 2 | Bloomberg API | ✅ 可用 | 需要 Bloomberg 终端 |
| 3 | Refinitiv Workspace | ⏳ 框架 | 待实现 |
| 4 | AkShare | ✅ 可用 | 免费备选 |

### 6. 交互式菜单 ✅
主菜单功能：
1. 导入新的清算数据
2. 进行交易分析（最大回撤、净值曲线）
3. 查看数据摘要
4. 验证净值计算
5. 重新计算净值
6. 清空数据库

## 当前状态

### 已知问题
1. **持仓重建逻辑有 Bug**: 2025-12-15 的黄金9999持仓计算错误（显示17000股，实际应为7000股）
2. **净值计算不准确**: 由于持仓计算错误，导致净值计算结果不正确

### 已验证的数据
- 2025-12-15 实际持仓：
  - 600089 特变电工: 2000股
  - 159937 黄金9999: **7000股**（不是17000股）
  - 002594 比亚迪: 200股
  - 601989 中国重工: 4000股

## 下一步计划

### 高优先级
1. **修复持仓重建 Bug**
   - 问题文件: `trade_analysis/services/data_manager.py`
   - 问题方法: `_rebuild_position_history()`
   - 问题: 累计计算时没有正确处理之前的卖出记录

2. **重新计算净值**
   - 修复 Bug 后，需要重新计算所有净值数据

### 中优先级
3. **完善 Bloomberg API 实现**
   - 已实现基本功能，可以进一步优化

4. **添加数据验证**
   - 验证导入的数据完整性
   - 检查异常交易记录

### 低优先级
5. **添加可视化功能**
   - 净值曲线图
   - 回撤分析图

6. **实现 Refinitiv Workspace API**
   - 框架已搭建，待实现具体功能

## 关键代码位置

### 需要修复的文件
```python
# trade_analysis/services/data_manager.py
# 方法: _rebuild_position_history()
# 行数: 约 350-400 行
```

### 价格获取模块
```python
# trade_analysis/services/price_fetcher.py
# 已实现: Wind、Bloomberg、AkShare
# 待实现: Refinitiv Workspace
```

## 测试数据

### 清算文件
- 路径: `C:\Dev\PythonBox\trade_analysis\data\raw\2025_2026settlement.xls`
- 记录数: 2423 行
- 日期范围: 2023-06-13 至 2025-12-31

### 数据库
- 路径: `C:\Dev\PythonBox\trade_analysis\data\trade_data.db`
- 净值记录: 473 天

## 运行方式

```bash
# 进入项目目录
cd C:\Dev\PythonBox

# 运行主程序
python -m trade_analysis.main
```

## 依赖项

```
pandas
numpy
akshare
WindPy (需安装)
blpapi (已安装)
refinitiv.data (可选)
```

## 技能文件

已创建技能文件：
- `.trae/skills/bloomberg-api-helper/SKILL.md` - Bloomberg API 帮助文档

---

**最后更新**: 2026-02-21
**状态**: 开发中（持仓计算 Bug 待修复）
