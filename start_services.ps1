$ErrorActionPreference = "Continue"

# Stop existing
taskkill /f /im StarRail.exe 2>$null | Out-Null
taskkill /f /im ZFGameBrowser.exe 2>$null | Out-Null
& "$PSScriptRoot\stop_services.ps1"
Start-Sleep -Seconds 1

# Start services with log redirection
if (!(Test-Path "$PSScriptRoot\logs")) { New-Item -ItemType Directory -Path "$PSScriptRoot\logs" | Out-Null }
$proxy = Start-Process -FilePath "C:\Users\Administrator\AppData\Local\Python\pythoncore-3.14-64\python.exe" -ArgumentList "run_proxy.py" -WorkingDirectory "$PSScriptRoot" -RedirectStandardOutput "$PSScriptRoot\logs\proxy.log" -RedirectStandardError "$PSScriptRoot\logs\proxy_err.log" -PassThru
$gameserver = Start-Process -FilePath "$PSScriptRoot\.venv\Scripts\python.exe" -ArgumentList "-u -m gameserver" -WorkingDirectory "$PSScriptRoot" -RedirectStandardOutput "$PSScriptRoot\logs\gameserver.log" -RedirectStandardError "$PSScriptRoot\logs\gameserver_err.log" -PassThru
$sdkserver = Start-Process -FilePath "$PSScriptRoot\.venv\Scripts\python.exe" -ArgumentList "-u -m sdkserver" -WorkingDirectory "$PSScriptRoot" -RedirectStandardOutput "$PSScriptRoot\logs\sdkserver.log" -RedirectStandardError "$PSScriptRoot\logs\sdkserver_err.log" -PassThru
$shim = Start-Process -FilePath "$PSScriptRoot\.venv\Scripts\python.exe" -ArgumentList "-u shim.py" -WorkingDirectory "$PSScriptRoot\kcpshimmy" -RedirectStandardOutput "$PSScriptRoot\logs\kcpshimmy.log" -RedirectStandardError "$PSScriptRoot\logs\kcpshimmy_err.log" -PassThru

Start-Sleep -Seconds 5

Write-Host "Services started:"
Write-Host "  Proxy (8085):      PID $($proxy.Id) (Running: $(!$proxy.HasExited))"
Write-Host "  Gameserver (23301): PID $($gameserver.Id) (Running: $(!$gameserver.HasExited))"
Write-Host "  SDK (21000):       PID $($sdkserver.Id) (Running: $(!$sdkserver.HasExited))"
Write-Host "  KCP Shim (23301):  PID $($shim.Id) (Running: $(!$shim.HasExited))"
