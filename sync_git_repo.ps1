#!/usr/bin/env powershell

<#
.SYNOPSIS
    Git repository sync tool
.DESCRIPTION
    Syncs local Git repository with remote
.EXAMPLE
    .\sync_git_repo.ps1
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

# 0. Check sync status
Write-Host "0. Checking repository sync status..." -ForegroundColor Yellow
Write-Host ""
try {
    $remoteHash = git ls-remote origin main 2>$null | Select-String -Pattern "^\w+" | ForEach-Object { $_.Matches.Value }
    
    if (-not $remoteHash) {
        Write-Host "[WARNING] Unable to connect to remote repository." -ForegroundColor Yellow
        Write-Host "[INFO] Continuing with local operations..." -ForegroundColor Gray
    } else {
        $localHash = git rev-parse main
        
        if ($localHash -eq $remoteHash) {
            Write-Host "[OK] Local repository is up to date with remote!" -ForegroundColor Green
            Write-Host "[INFO] Latest commit: $localHash" -ForegroundColor Gray
        } else {
            Write-Host "[INFO] Local repository is NOT up to date with remote." -ForegroundColor Yellow
            Write-Host "[INFO] Local:  $localHash" -ForegroundColor Gray
            Write-Host "[INFO] Remote: $remoteHash" -ForegroundColor Gray
            Write-Host ""
            Write-Host "[INFO] Pulling latest changes..." -ForegroundColor Cyan
            
            $pullOutput = git pull origin main 2>$null
            Write-Host $pullOutput
            
            if ($pullOutput -match "CONFLICT") {
                Write-Host "[ERROR] Conflicts detected! Please resolve manually." -ForegroundColor Red
                exit 1
            }
            
            Write-Host "[OK] Successfully pulled latest changes!" -ForegroundColor Green
            Write-Host ""
        }
    }
} catch {
    Write-Host "[WARNING] Error checking status: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "[INFO] Continuing with local operations..." -ForegroundColor Gray
}

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
try {
    $pullOutput = git pull origin main
    Write-Host $pullOutput
    
    if ($pullOutput -match "CONFLICT") {
        Write-Host "[ERROR] Conflicts detected! Please resolve manually." -ForegroundColor Red
        exit 1
    }
    
    if ($pullOutput -match "Already up to date") {
        Write-Host "[OK] Repository is synchronized!" -ForegroundColor Green
    } else {
        Write-Host "[OK] Successfully pulled changes!" -ForegroundColor Green
    }
} catch {
    Write-Host "[ERROR] Error pulling changes: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
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
    } else {
        if ($pushError -match "Everything up-to-date") {
            Write-Host "[OK] No changes to push." -ForegroundColor Green
        } else {
            Write-Host "[WARNING] Push failed. Network issue?" -ForegroundColor Yellow
            Write-Host "[INFO] Changes committed locally but not pushed." -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "[WARNING] Push error: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "[INFO] Changes committed locally but not pushed." -ForegroundColor Gray
}

# 4. Verify status
Write-Host ""
Write-Host "4. Verifying sync status..." -ForegroundColor Yellow
Write-Host ""
try {
    $logOutput = git log --oneline -1
    Write-Host "Latest commit:"
    Write-Host $logOutput
    
    $branchOutput = git branch -vv
    Write-Host ""
    Write-Host "Branch status:"
    Write-Host $branchOutput
    
    if ($branchOutput -match "\[origin/main\]" -and -not ($branchOutput -match "\[origin/main.*ahead|behind\]")) {
        Write-Host ""
        Write-Host "[OK] Local and remote are synchronized!" -ForegroundColor Green
    } elseif ($branchOutput -match "\[origin/main.*ahead\]") {
        Write-Host ""
        Write-Host "[WARNING] Local has unpushed changes!" -ForegroundColor Yellow
    } elseif ($branchOutput -match "\[origin/main.*behind\]") {
        Write-Host ""
        Write-Host "[WARNING] Local is behind remote!" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERROR] Error verifying status: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Remote info
Write-Host ""
Write-Host "5. Remote repository info..." -ForegroundColor Yellow
Write-Host ""
try {
    $remoteOutput = git remote -v
    Write-Host "Remote repositories:"
    Write-Host $remoteOutput
} catch {
    Write-Host "[ERROR] Error getting remote info: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Sync script completed!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 6. Modify commit message
Write-Host "6. Modify recent commit message..." -ForegroundColor Yellow
Write-Host ""

try {
    $latestCommit = git log --oneline -1
    Write-Host "Latest commit:"
    Write-Host $latestCommit
    Write-Host ""
    
    $modifyCommit = Read-Host "Do you want to modify the latest commit message? (Y/N)"
    
    if ($modifyCommit -eq "Y" -or $modifyCommit -eq "y") {
        $newCommitMessage = Read-Host "Enter new commit message"
        
        if (-not [string]::IsNullOrEmpty($newCommitMessage)) {
            Write-Host "[INFO] Modifying commit message..." -ForegroundColor Cyan
            git commit --amend -m "$newCommitMessage" --no-edit
            
            Write-Host "[INFO] Pushing modified commit..." -ForegroundColor Cyan
            git push origin main --force
            
            Write-Host "[OK] Successfully modified commit message!" -ForegroundColor Green
        } else {
            Write-Host "[INFO] No new message provided, skipping." -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "[WARNING] Error modifying commit: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Tips:" -ForegroundColor Gray
Write-Host "- Run this script before starting work on any computer" -ForegroundColor Gray
Write-Host "- Run this script after completing work on any computer" -ForegroundColor Gray
Write-Host "- Run this script regularly to keep repositories synchronized" -ForegroundColor Gray
Write-Host "- Press Ctrl+C at any prompt to interrupt the script" -ForegroundColor Gray
