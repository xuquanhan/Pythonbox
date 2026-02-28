# PythonBox 项目规则

## 强制执行规范

### 创建新项目时必须遵循的步骤

1. **调用 project-structure-organizer skill** - 获取项目结构指导
2. **创建完整目录结构** - 包括 data/, models/, tools/, scripts/, tests/
3. **创建 README.md** - 包含项目说明
4. **创建 requirements.txt** - 列出依赖

### 禁止事项

- ❌ 禁止在项目根目录创建临时测试文件
- ❌ 禁止在 PythonBox 根目录留下调试脚本
- ❌ 禁止跳过 skill 直接编写代码

### 项目结构模板

```
project_name/
├── data/
│   ├── raw/
│   └── processed/
├── models/
├── tools/
├── scripts/
├── tests/
│   ├── __init__.py
│   └── test_*.py
├── README.md
└── requirements.txt
```

### 触发规则的关键场景

当用户要求以下操作时，必须先调用 skill：
- 创建新项目
- 创建新目录结构
- 重组现有代码库
- 设置新的子项目
