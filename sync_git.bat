@echo off
chcp 65001 > nul

title Git 仓库同步

echo 正在启动 Git 同步...
echo ===================

echo 当前目录: %CD%

rem 检查 Git 是否可用
git --version > nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Git 未安装或未添加到 PATH
    pause
    exit /b 1
)

rem 检查是否在 Git 仓库中
if not exist ".git" (
    echo 错误: 当前目录不是 Git 仓库
    pause
    exit /b 1
)

rem 执行 Git 操作
echo 执行 Git 同步操作...
echo ===================

echo 1. 拉取最新更改...
git pull origin main
if %errorlevel% neq 0 (
    echo 警告: 拉取失败，可能是网络问题
)

echo 2. 检查状态...
git status

echo 3. 推送更改...
git push origin main
if %errorlevel% neq 0 (
    echo 警告: 推送失败，可能是网络问题
)

echo 4. 检查最终状态...
git status
git branch -vv

echo ===================
echo Git 同步操作完成
pause
