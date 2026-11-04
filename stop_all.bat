@echo off
title echium-server 停止器
echo [*] 正在停止 echium-server 与游戏客户端...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_services.ps1"
echo.
echo [OK] 所有服务已停止，系统代理已关闭。
pause
