taskkill /f /im StarRail.exe 2>$null | Out-Null
taskkill /f /im ZFGameBrowser.exe 2>$null | Out-Null
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'gameserver|sdkserver|shim\.py|run_proxy' -and $_.CommandLine -notmatch 'zzz-server' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Get-CimInstance Win32_Process -Filter "Name='cmd.exe'" | Where-Object { $_.CommandLine -match 'gameserver|sdkserver|shim\.py|run_proxy' -and $_.CommandLine -notmatch 'zzz-server' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
$key = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
Set-ItemProperty -Path $key -Name ProxyEnable -Value 0 -Type DWord
Add-Type -Namespace Win32 -Name NativeStop -MemberDefinition '[DllImport("wininet.dll")] public static extern bool InternetSetOption(IntPtr hInternet, int dwOption, IntPtr lpBuffer, int dwBufferLength);'
[Win32.NativeStop]::InternetSetOption([IntPtr]::Zero, 39, [IntPtr]::Zero, 0) | Out-Null
[Win32.NativeStop]::InternetSetOption([IntPtr]::Zero, 37, [IntPtr]::Zero, 0) | Out-Null
Write-Host "echium services stopped, system proxy disabled."
