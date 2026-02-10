# 统一两台电脑编码环境方案

## 🎯 目标

确保 Desktop 和 Laptop 的编码环境一致，避免未来出现编码问题

## 📋 检查项目

### 1. 检查当前编码设置

在 Desktop 上运行：

```bash
# 查看 PowerShell 编码
$OutputEncoding

# 查看系统区域设置
Get-WinSystemLocale

# 查看 Git 编码设置
git config --list | findstr encoding
```

### 2. 推荐的统一编码设置

**PowerShell 配置**（两台电脑都执行）：

```powershell
# 设置 PowerShell 使用 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 永久保存到 profile
Add-Content $PROFILE "`n[Console]::OutputEncoding = [System.Text.Encoding]::UTF8"
Add-Content $PROFILE "`n`$OutputEncoding = [System.Text.Encoding]::UTF8"
```

**Git 配置**（两台电脑都执行）：

```bash
# 设置 Git 使用 UTF-8
git config --global core.quotepath false
git config --global i18n.logoutputencoding utf-8
git config --global i18n.commitencoding utf-8
git config --global core.editor "notepad"
```

**VS Code 配置**（如果使用）：
确保 `.vscode/settings.json` 包含：

```json
{
    "files.encoding": "utf8",
    "files.autoGuessEncoding": true
}
```

### 3. Python 文件编码

确保所有 `.py` 文件开头有：

```python
# -*- coding: utf-8 -*-
```

## 🚀 执行步骤

1. **先在 Desktop 上检查和设置**
2. **然后在 Laptop 上执行相同设置**
3. **测试提交一个包含中文的 commit 验证**

## ✅ 预期结果

* 两台电脑编码环境一致

* 支持中文文件名和提交信息

* Python 代码运行无编码错误

