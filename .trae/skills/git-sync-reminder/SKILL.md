---
name: "git-sync-reminder"
description: "提醒用户在开始编码前先执行 Git 同步流程（pull/commit/push）。Invoke when user starts working on a project, switches computers, or asks about workflow."
---

# Git 同步提醒助手

## 🎯 目的

提醒用户在开始编写代码之前，先完成 Git 同步流程，确保代码版本一致，避免冲突。

## 📋 同步流程

### 开始工作前（每台电脑）

```bash
# 1. 检查当前状态
git status

# 2. 拉取最新代码（从 GitHub 同步其他电脑的更改）
git pull origin main

# 3. 确认同步成功
git log --oneline -1
```

### 完成工作后（每台电脑）

```bash
# 1. 查看更改
git status

# 2. 添加更改
git add .

# 3. 提交更改
git commit -m "描述你的更改"

# 4. 推送到 GitHub
git push origin main
```

### 切换到另一台电脑前

```bash
# 确保所有更改已提交并推送
git status          # 确认工作目录干净
git push origin main # 推送所有更改
```

## ⚠️ 重要提醒

1. **开始编码前**：先 `git pull` 获取最新代码
2. **切换电脑前**：先 `git push` 推送本地更改
3. **遇到冲突**：不要慌，按照冲突解决流程处理
4. **定期同步**：养成习惯，避免积累太多差异

## 🔍 检查同步状态

```bash
# 查看本地和远程的差异
git status

# 查看提交历史
git log --oneline -5

# 查看远程仓库地址
git remote -v
```

## 💡 最佳实践

- ✅ 小步提交，频繁同步
- ✅ 写有意义的提交信息
- ✅ 推送前检查状态
- ✅ 拉取后测试代码
- ❌ 不要积累大量未提交更改
- ❌ 不要在未同步情况下长时间工作
