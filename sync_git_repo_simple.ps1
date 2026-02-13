#!/usr/bin/env powershell

<#
.SYNOPSIS
    Git repository sync tool
.DESCRIPTION
    Syncs local Git repository with remote
.EXAMPLE
    .\sync_git_repo_simple.ps1
#>

# Set error handling
$ErrorActionPreference = "Stop"

# Set encoding
$OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new()

# Main script
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Git Repository Sync Script" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Global variables
$pushFailed = $false
$pushErrorMessage = ""

# Check Git
if (-not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Git is not installed or not in PATH!" -ForegroundColor Red
    exit 1
}

# Check Git repository
if (-not (Test-Path ".git")) {
    Write-Host "[ERROR] Current directory is not a Git repository!" -ForegroundColor Red
    exit 1
}

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# 1. Check Git status
Write-Host "1. Checking Git status..." -ForegroundColor Yellow
Write-Host ""

try {
    $statusOutput = git status
    Write-Host $statusOutput
    
    if ($statusOutput -match "Changes not staged for commit" -or $statusOutput -match "Untracked files") {
        Write-Host "[INFO] Found uncommitted changes!" -ForegroundColor Yellow
        Write-Host ""
        
        $addChanges = Read-Host "Do you want to add and commit all changes? (Y/N)"
        if ($addChanges -eq "Y" -or $addChanges -eq "y") {
            Write-Host "[INFO] Adding all changes..." -ForegroundColor Cyan
            git add .
            
            $commitMessage = Read-Host "Please enter commit message"
            if ([string]::IsNullOrEmpty($commitMessage)) {
                $commitMessage = "Auto commit: Sync changes"
            }
            
            Write-Host "[INFO] Committing changes..." -ForegroundColor Cyan
            git commit -m "$commitMessage"
            Write-Host "[OK] Changes committed!" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "[ERROR] Error checking Git status: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Pull changes
Write-Host ""
Write-Host "2. Pulling remote changes..." -ForegroundColor Yellow
Write-Host ""

# Temporarily set error action to continue to handle git errors gracefully
$oldErrorAction = $ErrorActionPreference
$ErrorActionPreference = "Continue"

try {
    $pullOutput = git pull origin main 2>&1
    $pullExitCode = $LASTEXITCODE
    
    # Output the result
    if ($pullOutput) {
        Write-Host $pullOutput
    }
    
    # Check the exit code and output
    if ($pullExitCode -ne 0) {
        Write-Host "[WARNING] Pull operation returned exit code: $pullExitCode" -ForegroundColor Yellow
        Write-Host "[INFO] This may be due to network issues. Continuing with local operations..." -ForegroundColor Gray
    } elseif ($pullOutput -match "CONFLICT") {
        Write-Host "[ERROR] Conflicts detected! Please resolve manually." -ForegroundColor Red
        exit 1
    } elseif ($pullOutput -match "Already up to date") {
        Write-Host "[OK] Repository is already up to date!" -ForegroundColor Green
    } else {
        Write-Host "[OK] Successfully pulled changes!" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARNING] Exception during pull: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "[INFO] Continuing with local operations..." -ForegroundColor Gray
} finally {
    # Restore original error action preference
    $ErrorActionPreference = $oldErrorAction
}

# 3. Push changes
Write-Host ""
Write-Host "3. Pushing local changes..." -ForegroundColor Yellow
Write-Host ""

try {
    $process = Start-Process -FilePath "git" -ArgumentList "push", "origin", "main" -NoNewWindow -PassThru -RedirectStandardOutput "push_output.txt" -RedirectStandardError "push_error.txt"
    $process.WaitForExit()
    
    $pushOutput = Get-Content "push_output.txt" -Raw -ErrorAction SilentlyContinue
    $pushError = Get-Content "push_error.txt" -Raw -ErrorAction SilentlyContinue
    
    Remove-Item "push_output.txt", "push_error.txt" -ErrorAction SilentlyContinue
    
    if ($pushOutput) {
        Write-Host $pushOutput
    }
    if ($pushError) {
        Write-Host $pushError
    }
    
    if ($process.ExitCode -eq 0) {
        if ($pushOutput -match "Everything up-to-date") {
            Write-Host "[OK] No changes to push." -ForegroundColor Green
        } else {
            Write-Host "[OK] Successfully pushed changes!" -ForegroundColor Green
        }
        $pushFailed = $false
    } else {
        if ($pushError -match "Everything up-to-date") {
            Write-Host "[OK] No changes to push." -ForegroundColor Green
            $pushFailed = $false
        } else {
            Write-Host "[WARNING] Push failed. Network issue?" -ForegroundColor Yellow
            Write-Host "[INFO] Changes committed locally but not pushed." -ForegroundColor Gray
            $pushFailed = $true
            $pushErrorMessage = $pushError
        }
    }
} catch {
    Write-Host "[WARNING] Push error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "[INFO] Changes committed locally but not pushed." -ForegroundColor Gray
    $pushFailed = $true
    $pushErrorMessage = $_.Exception.Message
}

# 4. Verify status
Write-Host ""
Write-Host "4. Verifying sync status..." -ForegroundColor Yellow
Write-Host ""

# 分析同步状态
$aheadCount = 0
$behindCount = 0
$unstagedCount = 0
$untrackedCount = 0

# 获取 git 状态信息
$logOutput = git log --oneline -1
Write-Host "Latest commit:"
Write-Host $logOutput

$branchOutput = git branch -vv
Write-Host ""
Write-Host "Branch status:"
Write-Host $branchOutput

$statusOutput = git status -sb
Write-Host ""
Write-Host "Status summary:"
Write-Host $statusOutput

# 提取 ahead/behind 数量
if ($branchOutput -match "ahead (\d+)") {
    $aheadCount = $matches[1]
}
if ($branchOutput -match "behind (\d+)") {
    $behindCount = $matches[1]
}

# 提取未暂存和未跟踪文件数量
if ($statusOutput -match "\d+ modified") {
    $unstagedCount = $matches[0] -replace " modified", ""
}
if ($statusOutput -match "\d+ untracked") {
    $untrackedCount = $matches[0] -replace " untracked", ""
}

# 显示详细的同步状态
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "SYNC STATUS SUMMARY" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# 检测当前设备类型
$deviceType = "Unknown"
if ($env:COMPUTERNAME -like "*DESKTOP*" -or $env:USERPROFILE -like "*Desktop*") {
    $deviceType = "Desktop"
} elseif ($env:COMPUTERNAME -like "*LAPTOP*" -or $env:USERPROFILE -like "*Laptop*") {
    $deviceType = "Laptop"
}

Write-Host "[DEVICE] Current device: $deviceType" -ForegroundColor Gray

# 分析同步状态
Write-Host "[STATUS] Detailed Sync Analysis:" -ForegroundColor Cyan
Write-Host "----------------------------------" -ForegroundColor Cyan

if ($aheadCount -eq 0 -and $behindCount -eq 0 -and $unstagedCount -eq 0 -and $untrackedCount -eq 0) {
    Write-Host "[GITHUB] GitHub: Fully synchronized" -ForegroundColor Green
    Write-Host "[Device] $($deviceType): Fully synchronized" -ForegroundColor Green
    Write-Host "[OVERALL] All devices: Completely synchronized" -ForegroundColor Green
    Write-Host "[INFO]    No pending changes or commits" -ForegroundColor Gray
} else {
    $syncIssues = @()
    
    if ($aheadCount -gt 0) {
        Write-Host "[GITHUB] GitHub: Partially synchronized" -ForegroundColor Yellow
        Write-Host "[Device] $($deviceType): Has latest changes" -ForegroundColor Green
        Write-Host "[LOCAL]  Local commits: $aheadCount commit(s) ready to push" -ForegroundColor Yellow
        $syncIssues += "$aheadCount commit(s) not pushed to GitHub"
    } elseif ($behindCount -gt 0) {
        Write-Host "[GITHUB] GitHub: Has latest changes" -ForegroundColor Green
        Write-Host "[Device] $($deviceType): Partially synchronized" -ForegroundColor Yellow
        Write-Host "[REMOTE] Remote commits: $behindCount commit(s) ready to pull" -ForegroundColor Yellow
        $syncIssues += "$behindCount commit(s) not pulled from GitHub"
    } else {
        Write-Host "[GITHUB] GitHub: Synchronized" -ForegroundColor Green
        Write-Host "[Device] $($deviceType): Partially synchronized" -ForegroundColor Yellow
        
        if ($unstagedCount -gt 0) {
            Write-Host "[FILES]  Unstaged files: $unstagedCount file(s) need staging" -ForegroundColor Yellow
            $syncIssues += "$unstagedCount unstaged file(s)"
        }
        if ($untrackedCount -gt 0) {
            Write-Host "[FILES]  Untracked files: $untrackedCount file(s) need tracking" -ForegroundColor Yellow
            $syncIssues += "$untrackedCount untracked file(s)"
        }
    }
    
    if ($syncIssues.Count -gt 0) {
        Write-Host "[OVERALL] Sync status: Partially synchronized" -ForegroundColor Yellow
        Write-Host "[ISSUES]  Pending synchronization issues:" -ForegroundColor Red
        foreach ($issue in $syncIssues) {
            Write-Host "          - $issue" -ForegroundColor Red
        }
    }
}

# 显示终端同步状态
Write-Host "----------------------------------" -ForegroundColor Cyan
Write-Host "[TERMINAL] Current terminal status:" -ForegroundColor Cyan

if ($pushFailed) {
    Write-Host "[PUSH]    Push operation: Failed" -ForegroundColor Red
    Write-Host "[SYNC]    Terminal sync: Partial sync (commits not pushed)" -ForegroundColor Yellow
} else {
    if ($aheadCount -eq 0 -and $behindCount -eq 0) {
        Write-Host "[PUSH]    Push operation: Successful" -ForegroundColor Green
        Write-Host "[SYNC]    Terminal sync: Fully synchronized" -ForegroundColor Green
    } else {
        Write-Host "[PUSH]    Push operation: Successful" -ForegroundColor Green
        Write-Host "[SYNC]    Terminal sync: Partial sync (check above)" -ForegroundColor Yellow
    }
}

Write-Host "====================================" -ForegroundColor Cyan

# 推送失败提醒
if ($pushFailed) {
    Write-Host "" -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
    Write-Host "[ALERT] ⚠️  PUSH FAILED - PLEASE ATTENTION! ⚠️" -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
    
    # 连续三次提醒
    for ($i = 1; $i -le 3; $i++) {
        Write-Host "[ALERT] ⚠️  REMINDER $i/3: Push was NOT successful! ⚠️" -ForegroundColor Red
        Write-Host "[ALERT] ⚠️  Your changes are committed locally but not pushed to GitHub! ⚠️" -ForegroundColor Yellow
        Write-Host "[ALERT] ⚠️  Please run 'git push' manually when network is available! ⚠️" -ForegroundColor Yellow
        Write-Host "" -ForegroundColor Yellow
    }
    
    Write-Host "[ALERT] ⚠️  SYNC STATUS: Local and GitHub are NOT synchronized! ⚠️" -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Sync script completed!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
