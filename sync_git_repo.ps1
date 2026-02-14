#!/usr/bin/env powershell

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Git Repository Sync Script" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Global variables
$pushFailed = $false
$pushErrorMessage = ""
$clashPath = "C:\Users\xuqua\AppData\Local\Programs\Clash for Windows\Clash for Windows.exe"

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

# Function to open Clash
function Open-Clash {
    Write-Host "[HINT]  Please check if Clash is running and try again!" -ForegroundColor Cyan
    
    # Check if Clash is already running
    $clashProcess = Get-Process | Where-Object { $_.ProcessName -like "*Clash*" } | Select-Object -First 1
    if ($clashProcess) {
        Write-Host "[INFO] Clash is already running (PID: $($clashProcess.Id))" -ForegroundColor Green
        Write-Host "[HINT]  Please check Clash connection status and try again." -ForegroundColor Cyan
        return
    }
    
    $openClash = Read-Host "Do you want to open Clash now? (Y/N)"
    if ($openClash -eq "Y" -or $openClash -eq "y") {
        try {
            if (Test-Path $clashPath) {
                Write-Host "[INFO] Starting Clash from: $clashPath" -ForegroundColor Cyan
                $process = Start-Process $clashPath -PassThru
                if ($process) {
                    Write-Host "[INFO] Clash started successfully (PID: $($process.Id))" -ForegroundColor Green
                    Write-Host "[INFO] Please wait a moment for Clash to connect, then re-run this script." -ForegroundColor Green
                } else {
                    Write-Host "[WARNING] Clash may have started but process info not available." -ForegroundColor Yellow
                }
                exit 0
            } else {
                Write-Host "[ERROR] Clash not found at: $clashPath" -ForegroundColor Red
                Write-Host "[HINT]  Please open Clash manually." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "[ERROR] Failed to start Clash: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "[HINT]  You may need to open Clash manually." -ForegroundColor Yellow
        }
    }
}

# 1. Check Git status and analyze sync state
Write-Host "1. Analyzing Git status..." -ForegroundColor Yellow
Write-Host ""

try {
    # Fetch remote info first (without merging)
    $fetchOutput = git fetch origin main 2>&1
    $fetchExitCode = $LASTEXITCODE
    
    if ($fetchExitCode -ne 0) {
        Write-Host "[WARNING] Failed to fetch from remote. Network issue?" -ForegroundColor Yellow
        Open-Clash
    }
    
    # Check if local is ahead of remote
    $aheadOutput = git log origin/main..HEAD --oneline 2>$null
    $aheadCount = ($aheadOutput | Measure-Object -Line).Lines
    
    # Check if local is behind remote
    $behindOutput = git log HEAD..origin/main --oneline 2>$null
    $behindCount = ($behindOutput | Measure-Object -Line).Lines
    
    # Check for unstaged changes (modified, added, deleted, renamed, copied, updated but unmerged)
    $unstagedOutput = git status --porcelain | Where-Object { $_ -match '^.[MADRCU]' -or $_ -match '^[MADRCU].' }
    $unstagedCount = ($unstagedOutput | Measure-Object -Line).Lines
    
    # Check for untracked files
    $untrackedOutput = git status --porcelain | Where-Object { $_ -match '^\?\?' }
    $untrackedCount = ($untrackedOutput | Measure-Object -Line).Lines
    
    # Display current status
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host "CURRENT SYNC STATUS" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    
    if ($aheadCount -eq 0 -and $behindCount -eq 0) {
        Write-Host "[STATUS] Local and Remote are in sync" -ForegroundColor Green
    } elseif ($aheadCount -gt 0 -and $behindCount -eq 0) {
        Write-Host "[STATUS] Local is AHEAD of remote by $aheadCount commit(s)" -ForegroundColor Yellow
        Write-Host "[ACTION] You need to PUSH local changes to GitHub" -ForegroundColor Cyan
    } elseif ($behindCount -gt 0 -and $aheadCount -eq 0) {
        Write-Host "[STATUS] Local is BEHIND remote by $behindCount commit(s)" -ForegroundColor Yellow
        Write-Host "[ACTION] You need to PULL remote changes from GitHub" -ForegroundColor Cyan
    } else {
        Write-Host "[STATUS] Local and Remote have DIVERGED" -ForegroundColor Red
        Write-Host "[INFO]   Local ahead: $aheadCount commit(s)" -ForegroundColor Yellow
        Write-Host "[INFO]   Local behind: $behindCount commit(s)" -ForegroundColor Yellow
        Write-Host "[ACTION] You need to PULL first, then PUSH" -ForegroundColor Cyan
    }
    
    if ($unstagedCount -gt 0) {
        Write-Host "[LOCAL]  Modified files (not staged): $unstagedCount" -ForegroundColor Yellow
    }
    if ($untrackedCount -gt 0) {
        Write-Host "[LOCAL]  New files (not tracked): $untrackedCount" -ForegroundColor Yellow
    }
    
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] Error analyzing Git status: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Handle local uncommitted changes
if ($unstagedCount -gt 0 -or $untrackedCount -gt 0) {
    Write-Host "2. Handling uncommitted changes..." -ForegroundColor Yellow
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
        
        # Update ahead count after commit
        $aheadOutput = git log origin/main..HEAD --oneline 2>$null
        $aheadCount = ($aheadOutput | Measure-Object -Line).Lines
    }
    Write-Host ""
}

# 3. Ask user what to do
Write-Host "3. Choose sync action..." -ForegroundColor Yellow
Write-Host ""

if ($behindCount -gt 0 -and $aheadCount -gt 0) {
    # Diverged - need both pull and push
    Write-Host "[INFO] Repository has diverged. Will PULL then PUSH." -ForegroundColor Yellow
    $action = "both"
} elseif ($behindCount -gt 0) {
    # Only behind - ask if pull
    $doPull = Read-Host "Pull $behindCount commit(s) from GitHub? (Y/N)"
    if ($doPull -eq "Y" -or $doPull -eq "y") {
        $action = "pull"
    } else {
        $action = "none"
    }
} elseif ($aheadCount -gt 0) {
    # Only ahead - ask if push
    $doPush = Read-Host "Push $aheadCount commit(s) to GitHub? (Y/N)"
    if ($doPush -eq "Y" -or $doPush -eq "y") {
        $action = "push"
    } else {
        $action = "none"
    }
} else {
    Write-Host "[OK] Already in sync. Nothing to do." -ForegroundColor Green
    $action = "none"
}

# 4. Execute chosen action
if ($action -eq "pull" -or $action -eq "both") {
    Write-Host ""
    Write-Host "4. Pulling remote changes..." -ForegroundColor Yellow
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
            Write-Host "[WARNING] Pull operation failed!" -ForegroundColor Yellow
            Open-Clash
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
        Open-Clash
    } finally {
        $ErrorActionPreference = $oldErrorAction
    }
}

if ($action -eq "push" -or $action -eq "both") {
    Write-Host ""
    Write-Host "5. Pushing local changes..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        $pushOutput = git push origin main 2>&1
        $pushExitCode = $LASTEXITCODE
        
        if ($pushOutput) {
            Write-Host $pushOutput
        }
        
        if ($pushExitCode -eq 0) {
            if ($pushOutput -match "Everything up-to-date") {
                Write-Host "[OK] No changes to push." -ForegroundColor Green
            } else {
                Write-Host "[OK] Successfully pushed changes!" -ForegroundColor Green
            }
            $pushFailed = $false
        } else {
            if ($pushOutput -match "Everything up-to-date") {
                Write-Host "[OK] No changes to push." -ForegroundColor Green
                $pushFailed = $false
            } else {
                Write-Host "[WARNING] Push failed!" -ForegroundColor Yellow
                Open-Clash
                Write-Host "[INFO] Changes committed locally but not pushed." -ForegroundColor Gray
                $pushFailed = $true
                $pushErrorMessage = $pushOutput
            }
        }
    } catch {
        Write-Host "[WARNING] Push error: $($_.Exception.Message)" -ForegroundColor Yellow
        Open-Clash
        Write-Host "[INFO] Changes committed locally but not pushed." -ForegroundColor Gray
        $pushFailed = $true
        $pushErrorMessage = $_.Exception.Message
    }
}

# 6. Final status verification
Write-Host ""
Write-Host "6. Verifying final sync status..." -ForegroundColor Yellow
Write-Host ""

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

# Re-check git status for final summary
try {
    $aheadOutput = git log origin/main..HEAD --oneline 2>$null
    $aheadCount = ($aheadOutput | Measure-Object -Line).Lines
    
    $behindOutput = git log HEAD..origin/main --oneline 2>$null
    $behindCount = ($behindOutput | Measure-Object -Line).Lines
    
    $unstagedOutput = git status --porcelain | Where-Object { $_ -match '^.[MADRCU]' -or $_ -match '^[MADRCU].' }
    $unstagedCount = ($unstagedOutput | Measure-Object -Line).Lines
    
    $untrackedOutput = git status --porcelain | Where-Object { $_ -match '^\?\?' }
    $untrackedCount = ($untrackedOutput | Measure-Object -Line).Lines
    
    if ($aheadCount -eq 0 -and $behindCount -eq 0 -and $unstagedCount -eq 0 -and $untrackedCount -eq 0) {
        Write-Host "[GITHUB] GitHub: Fully synchronized" -ForegroundColor Green
        Write-Host "[Device] ${deviceType}: Fully synchronized" -ForegroundColor Green
        Write-Host "[OVERALL] All devices: Completely synchronized" -ForegroundColor Green
    } else {
        $syncIssues = @()
        
        if ($aheadCount -gt 0) {
            Write-Host "[GITHUB] GitHub: Partially synchronized" -ForegroundColor Yellow
            Write-Host "[Device] ${deviceType}: Has unpushed commits" -ForegroundColor Yellow
            $syncIssues += "$aheadCount commit(s) not pushed to GitHub"
        } elseif ($behindCount -gt 0) {
            Write-Host "[GITHUB] GitHub: Has unpulled commits" -ForegroundColor Yellow
            Write-Host "[Device] ${deviceType}: Partially synchronized" -ForegroundColor Yellow
            $syncIssues += "$behindCount commit(s) not pulled from GitHub"
        }
        
        if ($unstagedCount -gt 0) {
            Write-Host "[LOCAL]  Modified files on ${deviceType}: $unstagedCount (not staged)" -ForegroundColor Yellow
            $syncIssues += "$unstagedCount modified file(s) not staged"
        }
        if ($untrackedCount -gt 0) {
            Write-Host "[LOCAL]  New files on ${deviceType}: $untrackedCount (not tracked)" -ForegroundColor Yellow
            $syncIssues += "$untrackedCount new file(s) not tracked"
        }
        
        if ($syncIssues.Count -gt 0) {
            Write-Host "[OVERALL] Sync status: Partially synchronized" -ForegroundColor Yellow
            Write-Host "[ISSUES]  Pending issues:" -ForegroundColor Red
            foreach ($issue in $syncIssues) {
                Write-Host "          - $issue" -ForegroundColor Red
            }
        }
    }
} catch {
    Write-Host "[ERROR] Error analyzing sync status: $($_.Exception.Message)" -ForegroundColor Red
}

# Push failure reminders
if ($pushFailed) {
    Write-Host ""
    Write-Host "====================================" -ForegroundColor Red
    Write-Host "[ALERT] WARNING: PUSH FAILED!" -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
    
    for ($i = 1; $i -le 3; $i++) {
        Write-Host "[ALERT] REMINDER $i/3: Push was NOT successful!" -ForegroundColor Red
        Write-Host "[ALERT] Changes are committed locally but not pushed!" -ForegroundColor Yellow
        Write-Host ""
    }
    
    Write-Host "[ALERT] Please run 'git push' manually when network is available!" -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Red
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Sync script completed!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
