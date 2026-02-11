#!/usr/bin/env powershell

<#
.SYNOPSIS
    Automatically checks and syncs Git repository differences between local and GitHub.

.DESCRIPTION
    This script performs the following operations:
    1. Checks current Git repository status
    2. Pulls latest changes from remote repository
    3. Handles possible conflicts
    4. Pushes local changes to remote repository
    5. Verifies synchronization status

.EXAMPLE
    .\sync_git_repo.ps1

.NOTES
    Author: PythonBox Assistant
    Date: 2026-02-11
    Version: 1.0
#>

# Set error handling
$ErrorActionPreference = "Stop"

# Main script starts
Write-Host "====================================" -ForegroundColor Blue
Write-Host "Git Repository Sync Script" -ForegroundColor Blue
Write-Host "====================================" -ForegroundColor Blue

# Check if Git is installed
if (-not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Git is not installed or not in PATH!" -ForegroundColor Red
    exit 1
}

# Check if current directory is a Git repository
if (-not (Test-Path ".git")) {
    Write-Host "Error: Current directory is not a Git repository!" -ForegroundColor Red
    exit 1
}

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Blue

# 0. Check if local repo is up to date with remote
Write-Host -NoNewline "`n0. Checking if local repository is up to date..." -ForegroundColor Yellow
Write-Host
try {
    # Get remote latest commit hash
    $remoteHash = git ls-remote origin main | Select-String -Pattern "^\w+" | ForEach-Object { $_.Matches.Value }
    
    # Get local latest commit hash
    $localHash = git rev-parse main
    
    # Compare hashes
    if ($localHash -eq $remoteHash) {
        Write-Host "✅ Local repository is already up to date with GitHub!" -ForegroundColor Green
        Write-Host "Latest commit hash: $localHash" -ForegroundColor Blue
    } else {
        Write-Host "⚠️  Local repository is NOT up to date with GitHub!" -ForegroundColor Yellow
        Write-Host "Local commit: $localHash" -ForegroundColor Yellow
        Write-Host "Remote commit: $remoteHash" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Automatically pulling latest changes from GitHub..." -ForegroundColor Blue
        
        # Pull latest changes
        $pullOutput = git pull origin main
        Write-Host "Pull result:" -ForegroundColor Blue
        Write-Host $pullOutput
        
        # Check for conflicts
        if ($pullOutput -match "CONFLICT") {
            Write-Host "Warning: Conflicts detected during pull!" -ForegroundColor Red
            Write-Host "Please resolve conflicts manually, then re-run this script." -ForegroundColor Red
            exit 1
        }
        
        Write-Host "✅ Successfully pulled latest changes!" -ForegroundColor Green
        Write-Host ""
    }
} catch {
    Write-Host "Error checking repository status: $($_.Exception.Message)" -ForegroundColor Red
    # Continue with script even if this check fails
}

# 1. Check current Git status
Write-Host -NoNewline "`n1. Checking current Git status..." -ForegroundColor Yellow
Write-Host
try {
    $statusOutput = git status
    Write-Host "Git status:"
    Write-Host $statusOutput
    
    # Check for uncommitted changes
    if ($statusOutput -match "Changes not staged for commit" -or $statusOutput -match "Untracked files") {
        Write-Host "Found uncommitted changes!" -ForegroundColor Yellow
        
        # Ask if user wants to add and commit changes
        $addChanges = Read-Host "Do you want to add and commit all changes? (Y/N)"
        if ($addChanges -eq "Y" -or $addChanges -eq "y") {
            Write-Host "Adding all changes..." -ForegroundColor Blue
            git add .
            
            $commitMessage = Read-Host "Please enter commit message:"
            if ([string]::IsNullOrEmpty($commitMessage)) {
                $commitMessage = "Auto commit: Sync changes"
            }
            
            Write-Host "Committing changes..." -ForegroundColor Blue
            git commit -m $commitMessage
        }
    }
} catch {
    Write-Host "Error checking Git status: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Pull remote changes (additional check)
Write-Host -NoNewline "`n2. Performing final pull to ensure synchronization..." -ForegroundColor Yellow
Write-Host
try {
    $pullOutput = git pull origin main
    Write-Host "Pull result:"
    Write-Host $pullOutput
    
    # Check for conflicts
    if ($pullOutput -match "CONFLICT") {
        Write-Host "Warning: Conflicts detected during pull!" -ForegroundColor Red
        Write-Host "Please resolve conflicts manually, then re-run this script." -ForegroundColor Red
        exit 1
    }
    
    if ($pullOutput -match "Already up to date") {
        Write-Host "Repository is fully synchronized!" -ForegroundColor Green
    } else {
        Write-Host "Successfully pulled latest changes!" -ForegroundColor Green
    }
} catch {
    Write-Host "Error pulling remote changes: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 3. Push local changes
Write-Host -NoNewline "`n3. Pushing local changes to remote repository..." -ForegroundColor Yellow
Write-Host
try {
    $pushOutput = git push origin main
    Write-Host "Push result:"
    Write-Host $pushOutput
    
    if ($pushOutput -match "Everything up-to-date") {
        Write-Host "Local repository is already up to date, no need to push." -ForegroundColor Green
    } else {
        Write-Host "Successfully pushed local changes!" -ForegroundColor Green
    }
} catch {
    Write-Host "Error pushing local changes: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 4. Verify sync status
Write-Host -NoNewline "`n4. Verifying synchronization status..." -ForegroundColor Yellow
Write-Host
try {
    $logOutput = git log --oneline -1
    Write-Host "Latest commit:"
    Write-Host $logOutput
    
    # Check local and remote branch status
    $branchOutput = git branch -vv
    Write-Host -NoNewline "`nBranch status:"
    Write-Host
    Write-Host $branchOutput
    
    # Check if synchronized
    if ($branchOutput -match "\[origin/main\]" -and -not ($branchOutput -match "\[origin/main.*ahead|behind\]")) {
        Write-Host -NoNewline "`n✅ Sync status: Local and remote repositories are fully synchronized!" -ForegroundColor Green
        Write-Host
    } elseif ($branchOutput -match "\[origin/main.*ahead\]") {
        Write-Host -NoNewline "`n⚠️  Sync status: Local repository has unpushed changes!" -ForegroundColor Yellow
        Write-Host
        Write-Host "Please re-run the script or push changes manually." -ForegroundColor Yellow
    } elseif ($branchOutput -match "\[origin/main.*behind\]") {
        Write-Host -NoNewline "`n⚠️  Sync status: Local repository is behind remote repository!" -ForegroundColor Yellow
        Write-Host
        Write-Host "Please re-run the script or pull changes manually." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error verifying sync status: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 5. Show remote repository info
Write-Host -NoNewline "`n5. Remote repository information..." -ForegroundColor Yellow
Write-Host
try {
    $remoteOutput = git remote -v
    Write-Host "Remote repositories:"
    Write-Host $remoteOutput
} catch {
    Write-Host "Error getting remote repository info: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n====================================" -ForegroundColor Blue
Write-Host "Sync script execution completed!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Blue
Write-Host -NoNewline "`nTips:"
Write-Host
Write-Host "- Before starting work on any computer, run this script to sync changes"
Write-Host "- After completing work on any computer, run this script to push changes"
Write-Host "- Run this script regularly to keep repositories synchronized"
