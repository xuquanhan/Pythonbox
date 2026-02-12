@echo off

rem 设置窗口标题
title Git 仓库同步工具

rem 进入脚本所在目录
echo 进入目录: %~dp0
cd /d "%~dp0"
echo 当前目录: %cd%

echo 正在运行 Git 同步脚本...
echo =========================

rem 检查 PowerShell 是否已启用
echo 检查 PowerShell 可用性...
powershell -command "Write-Output 'PowerShell 可用'" > nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: PowerShell 不可用，请确保已启用 PowerShell
    pause
    exit /b 1
)

rem 检查 Git 是否已安装
echo 检查 Git 可用性...
git --version > nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Git 不可用，请确保已安装 Git 并添加到 PATH
    pause
    exit /b 1
)

rem 检查是否在 Git 仓库中
echo 检查是否在 Git 仓库中...
if not exist ".git" (
    echo 错误: 当前目录不是 Git 仓库
    pause
    exit /b 1
)

rem 运行 PowerShell 同步脚本
echo 运行 PowerShell 同步脚本...
echo 请耐心等待，脚本正在执行 Git 同步操作...
echo =========================
powershell -ExecutionPolicy Bypass -File "%~dp0sync_git_repo.ps1"

rem 检查脚本执行结果
if %errorlevel% neq 0 (
    echo =========================
    echo 错误: Git 同步脚本执行失败
    echo 请检查上述错误信息
    pause
    exit /b 1
)

echo =========================
echo Git 同步脚本执行完成
pause

