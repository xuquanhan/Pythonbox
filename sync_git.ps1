#!/usr/bin/env powershell

# 设置编码为UTF-8
$OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new()

Write-Host "正在启动 Git 同步..." -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green

Write-Host "当前目录: $(Get-Location)" -ForegroundColor Blue

# 检查 Git 是否可用
if (-not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    Write-Host "错误: Git 未安装或未添加到 PATH" -ForegroundColor Red
    Read-Host "按任意键退出..."
    exit 1
}

# 检查是否在 Git 仓库中
if (-not (Test-Path ".git")) {
    Write-Host "错误: 当前目录不是 Git 仓库" -ForegroundColor Red
    Read-Host "按任意键退出..."
    exit 1
}

# 执行 Git 操作
Write-Host "执行 Git 同步操作..." -ForegroundColor Green
Write-Host "===================" -ForegroundColor Green

Write-Host "1. 拉取最新更改..." -ForegroundColor Yellow
try {
    $pullOutput = git pull origin main
    Write-Host $pullOutput
} catch {
    Write-Host "警告: 拉取失败，可能是网络问题" -ForegroundColor Yellow
}

Write-Host "2. 检查状态..." -ForegroundColor Yellow
try {
    $statusOutput = git status
    Write-Host $statusOutput
} catch {
    Write-Host "警告: 检查状态失败" -ForegroundColor Yellow
}

Write-Host "3. 推送更改..." -ForegroundColor Yellow
try {
    $pushOutput = git push origin main
    Write-Host $pushOutput
} catch {
    Write-Host "警告: 推送失败，可能是网络问题" -ForegroundColor Yellow
}

Write-Host "4. 检查最终状态..." -ForegroundColor Yellow
try {
    $finalStatus = git status
    Write-Host $finalStatus
    $branchStatus = git branch -vv
    Write-Host $branchStatus
} catch {
    Write-Host "警告: 检查最终状态失败" -ForegroundColor Yellow
}

Write-Host "===================" -ForegroundColor Green
Write-Host "Git 同步操作完成" -ForegroundColor Green
Read-Host "按任意键退出..."
