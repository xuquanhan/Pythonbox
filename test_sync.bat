@echo on

rem 设置窗口标题
title Git 同步测试

rem 进入脚本所在目录
echo 进入目录: %~dp0
cd /d "%~dp0"
echo 当前目录: %cd%

echo 测试环境变量...
echo PATH: %PATH%
echo USERPROFILE: %USERPROFILE%

echo 测试 PowerShell...
powershell -version
if %errorlevel% neq 0 (
    echo PowerShell 错误: %errorlevel%
    pause
    exit /b 1
)

echo 测试 Git...
git --version
if %errorlevel% neq 0 (
    echo Git 错误: %errorlevel%
    pause
    exit /b 1
)

echo 测试目录结构...
dir /a

rem 暂停以查看结果
echo 测试完成，按任意键退出...
pause
