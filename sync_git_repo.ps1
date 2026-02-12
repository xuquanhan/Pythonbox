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
    6. Allows modification of recent commit messages

.EXAMPLE
    .\sync_git_repo.ps1

.NOTES
    Author: PythonBox Assistant
    Date: 2026-02-12
    Version: 1.1
#>

# Set error handling
$ErrorActionPreference = "Stop"

# Set encoding to UTF-8 to fix garbled characters
$OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new()

# Handle Ctrl+C gracefully
[Console]::TreatControlCAsInput = $false

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
    $remoteHash = git ls-remote origin main 2>$null | Select-String -Pattern "^\w+" | ForEach-Object { $_.Matches.Value }
    
    if (-not $remoteHash) {
        Write-Host "⚠️  Unable to connect to remote repository. Network issue detected!" -ForegroundColor Yellow
        Write-Host "Continuing with local operations..." -ForegroundColor Blue
    } else {
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
            $pullOutput = git pull origin main 2>$null
            Write-Host "Pull result:" -ForegroundColor Blue
            Write-Host $pullOutput
            
            # Check for conflicts
            if ($pullOutput -match "CONFLICT") {
                Write-Host "Warning: Conflicts detected during pull!" -ForegroundColor Red
                Write-Host "Please resolve conflicts manually, then re-run this script." -ForegroundColor Red
                exit 1
            } elseif (-not $pullOutput) {
                Write-Host "⚠️  Pull operation failed. Network issue detected!" -ForegroundColor Yellow
                Write-Host "Continuing with local operations..." -ForegroundColor Blue
            } else {
                Write-Host "✅ Successfully pulled latest changes!" -ForegroundColor Green
                Write-Host ""
            }
        }
    }
} catch {
    Write-Host "Error checking repository status: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Continuing with local operations..." -ForegroundColor Blue
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
        Write-Host "(Press Ctrl+C to interrupt at any time)" -ForegroundColor Gray
        $addChanges = Read-Host "Do you want to add and commit all changes? (Y/N)"
        if ($addChanges -eq "Y" -or $addChanges -eq "y") {
            Write-Host "Adding all changes..." -ForegroundColor Blue
            git add .
            
            Write-Host "(Press Ctrl+C to interrupt at any time)" -ForegroundColor Gray
            $commitMessage = Read-Host "Please enter commit message:"
            if ([string]::IsNullOrEmpty($commitMessage)) {
                $commitMessage = "Auto commit: Sync changes"
            }
            
            Write-Host "Committing changes..." -ForegroundColor Blue
            git commit -m $commitMessage
        } elseif ($addChanges -ne "N" -and $addChanges -ne "n") {
            Write-Host "⚠️  Invalid input. Please enter Y or N." -ForegroundColor Yellow
            Write-Host "Skipping commit operation." -ForegroundColor Blue
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
    # Capture both stdout and stderr
    $process = Start-Process -FilePath "git" -ArgumentList "push", "origin", "main" -NoNewWindow -PassThru -RedirectStandardOutput "push_output.txt" -RedirectStandardError "push_error.txt"
    $process.WaitForExit()
    
    # Read output
    $pushOutput = Get-Content "push_output.txt" -Raw
    $pushError = Get-Content "push_error.txt" -Raw
    
    # Clean up temporary files
    Remove-Item "push_output.txt", "push_error.txt" -ErrorAction SilentlyContinue
    
    # Combine output
    if ($pushOutput) {
        Write-Host "Push result:"
        Write-Host $pushOutput
    }
    if ($pushError) {
        Write-Host "Push error:"
        Write-Host $pushError
    }
    
    # Check results
    if ($process.ExitCode -eq 0) {
        if ($pushOutput -match "Everything up-to-date") {
            Write-Host "Local repository is already up to date, no need to push." -ForegroundColor Green
        } else {
            Write-Host "Successfully pushed local changes!" -ForegroundColor Green
        }
    } else {
        if ($pushError -match "Everything up-to-date") {
            Write-Host "Local repository is already up to date, no need to push." -ForegroundColor Green
        } else {
            Write-Host "⚠️  Push operation failed. Network issue detected!" -ForegroundColor Yellow
            Write-Host "Local changes have been committed but not pushed." -ForegroundColor Yellow
            Write-Host "Please try pushing again when network is available." -ForegroundColor Blue
        }
    }
} catch {
    Write-Host "Error pushing local changes: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Local changes have been committed but not pushed." -ForegroundColor Yellow
    Write-Host "Please try pushing again when network is available." -ForegroundColor Blue
    # Continue with script instead of exiting
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

# 6. Allow modifying recent commit message
Write-Host -NoNewline "`n6. Modify recent commit message..." -ForegroundColor Yellow
Write-Host

try {
    # Get latest commit information
    $latestCommit = git log --oneline -1
    Write-Host "Latest commit:" -ForegroundColor Blue
    Write-Host $latestCommit
    
    # Ask if user wants to modify the commit message
    Write-Host "(Press Ctrl+C to interrupt at any time)" -ForegroundColor Gray
    $modifyCommit = Read-Host "Do you want to modify the latest commit message? (Y/N)"
    
    if ($modifyCommit -eq "Y" -or $modifyCommit -eq "y") {
        Write-Host "(Press Ctrl+C to interrupt at any time)" -ForegroundColor Gray
        $newCommitMessage = Read-Host "Enter new commit message:"
        
        if (-not [string]::IsNullOrEmpty($newCommitMessage)) {
            Write-Host "Modifying commit message..." -ForegroundColor Blue
            # Use git commit --amend to modify the latest commit message
            git commit --amend -m "$newCommitMessage" --no-edit
            
            # Push the modified commit (force push)
            Write-Host "Pushing modified commit..." -ForegroundColor Blue
            git push origin main --force
            
            Write-Host "✅ Successfully modified commit message!" -ForegroundColor Green
        } else {
            Write-Host "⚠️  No new commit message provided, skipping modification." -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "Error modifying commit message: $($_.Exception.Message)" -ForegroundColor Red
    # Continue with script even if this fails
}

Write-Host -NoNewline "`nTips:"
Write-Host
Write-Host "- Before starting work on any computer, run this script to sync changes"
Write-Host "- After completing work on any computer, run this script to push changes"
Write-Host "- Run this script regularly to keep repositories synchronized"
Write-Host "- Press Ctrl+C at any prompt to interrupt the script"
