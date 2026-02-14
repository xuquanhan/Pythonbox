#!/usr/bin/env powershell

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

$oldErrorAction = $ErrorActionPreference
$ErrorActionPreference = "Continue"

try {
    $pullOutput = git pull origin main 2>&1
    $pullExitCode = $LASTEXITCODE
    
    if ($pullOutput) {
        Write-Host $pullOutput
    }
    
    if ($pullExitCode -ne 0) {
        Write-Host "[WARNING] Pull operation returned exit code: $pullExitCode" -ForegroundColor Yellow
        Write-Host "[INFO] This may be due to network issues." -ForegroundColor Gray
        Write-Host "[HINT]  Please check if Clash is running and try again!" -ForegroundColor Cyan
        $openClash = Read-Host "Do you want to open Clash now? (Y/N)"
        if ($openClash -eq "Y" -or $openClash -eq "y") {
            try {
                Start-Process "Clash for Windows"
                Write-Host "[INFO] Clash is starting... Please wait a moment and re-run this script." -ForegroundColor Green
                exit 0
            } catch {
                Write-Host "[ERROR] Failed to start Clash. Please open it manually." -ForegroundColor Red
            }
        }
        Write-Host "[INFO] Continuing with local operations..." -ForegroundColor Gray
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
            Write-Host "[HINT]  Please check if Clash is running and try again!" -ForegroundColor Cyan
            $openClash = Read-Host "Do you want to open Clash now? (Y/N)"
            if ($openClash -eq "Y" -or $openClash -eq "y") {
                try {
                    Start-Process "Clash for Windows"
                    Write-Host "[INFO] Clash is starting... Please wait a moment and re-run this script." -ForegroundColor Green
                    exit 0
                } catch {
                    Write-Host "[ERROR] Failed to start Clash. Please open it manually." -ForegroundColor Red
                }
            }
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

# Get git status information
try {
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
} catch {
    Write-Host "[ERROR] Error verifying status: $($_.Exception.Message)" -ForegroundColor Red
}

# Show detailed sync status
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "SYNC STATUS SUMMARY" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Detect current device type
$deviceType = "Unknown"
if ($env:COMPUTERNAME -match "DESKTOP" -or $env:USERPROFILE -match "Desktop") {
    $deviceType = "Desktop"
} elseif ($env:COMPUTERNAME -match "LAPTOP" -or $env:USERPROFILE -match "Laptop") {
    $deviceType = "Laptop"
}

Write-Host "[DEVICE] Current device: $deviceType" -ForegroundColor Gray
Write-Host ""

# Check git status for sync analysis
Write-Host "[STATUS] Detailed Sync Analysis:" -ForegroundColor Cyan
Write-Host "----------------------------------" -ForegroundColor Cyan

try {
    # Check if local is ahead of remote
    $aheadOutput = git log origin/main..HEAD --oneline
    $aheadCount = ($aheadOutput | Measure-Object -Line).Lines
    
    # Check if local is behind remote
    $behindOutput = git log HEAD..origin/main --oneline
    $behindCount = ($behindOutput | Measure-Object -Line).Lines
    
    # Check for unstaged changes
    $unstagedOutput = git status --porcelain | Where-Object { $_ -match '^[MADRCU] ' }
    $unstagedCount = ($unstagedOutput | Measure-Object -Line).Lines
    
    # Check for untracked files
    $untrackedOutput = git status --porcelain | Where-Object { $_ -match '^\?\? ' }
    $untrackedCount = ($untrackedOutput | Measure-Object -Line).Lines
    
    if ($aheadCount -eq 0 -and $behindCount -eq 0 -and $unstagedCount -eq 0 -and $untrackedCount -eq 0) {
        Write-Host "[GITHUB] GitHub: Fully synchronized" -ForegroundColor Green
        Write-Host "[Device] ${deviceType}: Fully synchronized" -ForegroundColor Green
        Write-Host "[OVERALL] All devices: Completely synchronized" -ForegroundColor Green
        Write-Host "[INFO]    No pending changes or commits" -ForegroundColor Gray
    } else {
        $syncIssues = @()
        
        if ($aheadCount -gt 0) {
            Write-Host "[GITHUB] GitHub: Partially synchronized" -ForegroundColor Yellow
            Write-Host "[Device] ${deviceType}: Has latest changes" -ForegroundColor Green
            Write-Host "[LOCAL]  Local commits: $aheadCount commit(s) ready to push" -ForegroundColor Yellow
            $syncIssues += "$aheadCount commit(s) not pushed to GitHub"
        } elseif ($behindCount -gt 0) {
            Write-Host "[GITHUB] GitHub: Has latest changes" -ForegroundColor Green
            Write-Host "[Device] ${deviceType}: Partially synchronized" -ForegroundColor Yellow
            Write-Host "[REMOTE] Remote commits: $behindCount commit(s) ready to pull" -ForegroundColor Yellow
            $syncIssues += "$behindCount commit(s) not pulled from GitHub"
        } else {
            Write-Host "[GITHUB] GitHub: Synchronized" -ForegroundColor Green
            Write-Host "[Device] ${deviceType}: Partially synchronized" -ForegroundColor Yellow
        }
        
        if ($unstagedCount -gt 0) {
            Write-Host "[LOCAL]  Modified files on ${deviceType}: $unstagedCount file(s) (not staged for commit)" -ForegroundColor Yellow
            $syncIssues += "$unstagedCount modified file(s) on $deviceType (not staged)"
        }
        if ($untrackedCount -gt 0) {
            Write-Host "[LOCAL]  New files on ${deviceType}: $untrackedCount file(s) (not tracked by Git)" -ForegroundColor Yellow
            $syncIssues += "$untrackedCount new file(s) on $deviceType (not tracked)"
        }
        
        if ($syncIssues.Count -gt 0) {
            Write-Host "[OVERALL] Sync status: Partially synchronized" -ForegroundColor Yellow
            Write-Host "[ISSUES]  Pending synchronization issues:" -ForegroundColor Red
            foreach ($issue in $syncIssues) {
                Write-Host "          - $issue" -ForegroundColor Red
            }
        }
    }
} catch {
    Write-Host "[ERROR] Error analyzing sync status: $($_.Exception.Message)" -ForegroundColor Red
}

# Show terminal sync status
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

# Push failure reminders
if ($pushFailed) {
    Write-Host "" -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
    Write-Host "[ALERT] WARNING: PUSH FAILED - PLEASE ATTENTION!" -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
    
    # Three consecutive reminders
    for ($i = 1; $i -le 3; $i++) {
        Write-Host "[ALERT] WARNING: REMINDER $i/3: Push was NOT successful!" -ForegroundColor Red
        Write-Host "[ALERT] WARNING: Your changes are committed locally but not pushed to GitHub!" -ForegroundColor Yellow
        Write-Host "[ALERT] WARNING: Please run 'git push' manually when network is available!" -ForegroundColor Yellow
        Write-Host "" -ForegroundColor Yellow
    }
    
    Write-Host "[ALERT] WARNING: SYNC STATUS: Local and GitHub are NOT synchronized!" -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Sync script completed!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
