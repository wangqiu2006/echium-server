@echo off
title echium-server 控制台
cd /d "%~dp0"
if not exist logs mkdir logs

echo ===================================================================
echo               echium-server (HSR 4.5.x 私服) 启动器
echo ===================================================================
echo.
echo [*] [1/5] 清理残留进程与端口...
taskkill /f /im StarRail.exe >nul 2>&1
taskkill /f /im ZFGameBrowser.exe >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop_services.ps1" >nul 2>&1
ping 127.0.0.1 -n 2 >nul

echo [*] [2/5] 启动流量代理与分发 (mitmproxy 8085 -> 21000)...
start "echium-proxy" cmd /k "title echium-proxy (8085) & C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe run_proxy.py"

echo [*] [3/5] 启动 gameserver (TCP 23301)...
start "echium-gameserver" cmd /k "title echium-gameserver (23301) & .venv\Scripts\python.exe -u -m gameserver"

echo [*] [4/5] 启动 sdkserver (TCP 21000)...
start "echium-sdkserver" cmd /k "title echium-sdkserver (21000) & .venv\Scripts\python.exe -u -m sdkserver"

echo [*] [5/5] 启动 kcpshimmy (UDP 23301)...
start "echium-kcpshimmy" cmd /k "title echium-kcpshimmy (UDP 23301) & cd /d "%~dp0kcpshimmy" & ..\.venv\Scripts\python.exe -u shim.py"

echo [*] 正在等待服务启动 (5秒)...
ping 127.0.0.1 -n 6 >nul
echo.
echo [*] 检查端口监听状态:
netstat -ano | findstr "LISTENING" | findstr "8085 21000 23301"
netstat -ano | findstr "UDP" | findstr "23301"
echo.
echo ===================================================================
echo  [OK] 所有服务已启动完毕！窗口已弹出，你可以直接启动客户端：
echo       D:\Star Rail Game\StarRail.exe
echo  关闭服务器请运行 stop_all.bat
echo ===================================================================
pause
