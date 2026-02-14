@echo off
chcp 65001 >nul
title Git Sync Tool

echo ====================================
echo Git Repository Sync Tool
echo ====================================
echo.

rem Configure Git to handle line endings and Unicode properly
git config --local core.autocrlf true >nul 2>&1
git config --local core.quotepath false >nul 2>&1
git config --local i18n.logoutputencoding utf-8 >nul 2>&1
git config --local i18n.commitencoding utf-8 >nul 2>&1

rem Check if PowerShell is available
powershell -Command "Write-Host 'PowerShell check passed'" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] PowerShell is not available.
    echo Please ensure PowerShell is installed.
    pause
    exit /b 1
)

echo [INFO] Starting Git synchronization...
echo.

rem Execute PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0sync_git_repo.ps1"

rem Check execution result
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Script exited with error code: %errorlevel%
    echo [INFO] Please check error messages above.
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo [INFO] Git synchronization completed.
echo.

rem Show recent commit history to verify sync status
echo ====================================
echo Recent Commits (last 10)
echo ====================================
git log --oneline -10
echo.
echo [INFO] Check above commits to verify Desktop, Laptop, and GitHub are in sync.
echo.
pause
