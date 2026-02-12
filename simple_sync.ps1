#!/usr/bin/env powershell

Write-Host "Starting Git sync..."
Write-Host "==================="

Write-Host "Current directory: $(Get-Location)"

# Check if Git is available
if (-not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Git is not installed or not in PATH"
    Read-Host "Press any key to exit..."
    exit 1
}

# Check if current directory is a Git repository
if (-not (Test-Path ".git")) {
    Write-Host "Error: Current directory is not a Git repository"
    Read-Host "Press any key to exit..."
    exit 1
}

# Execute Git operations
Write-Host "Executing Git sync operations..."
Write-Host "==================="

Write-Host "1. Pulling latest changes..."
try {
    git pull origin main
} catch {
    Write-Host "Warning: Pull failed, maybe network issue"
}

Write-Host "2. Checking status..."
try {
    git status
} catch {
    Write-Host "Warning: Status check failed"
}

Write-Host "3. Pushing changes..."
try {
    git push origin main
} catch {
    Write-Host "Warning: Push failed, maybe network issue"
}

Write-Host "4. Checking final status..."
try {
    git status
    git branch -vv
} catch {
    Write-Host "Warning: Final status check failed"
}

Write-Host "==================="
Write-Host "Git sync operations completed"
Read-Host "Press any key to exit..."
