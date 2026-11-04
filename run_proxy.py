"""
Launcher script that sets Windows system proxy, runs mitmdump in-process with proxy.py,
and cleans up system proxy settings on exit.
"""
import os
import sys
import winreg
import atexit
import signal

INTERNET_SETTINGS_KEY = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

def set_system_proxy(enable: bool, server: str = "127.0.0.1:8085"):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, INTERNET_SETTINGS_KEY, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1 if enable else 0)
            if enable:
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, server)
        import ctypes
        ctypes.windll.Wininet.InternetSetOptionW(0, 39, 0, 0) # INTERNET_OPTION_SETTINGS_CHANGED
        ctypes.windll.Wininet.InternetSetOptionW(0, 37, 0, 0) # INTERNET_OPTION_REFRESH
        print(f"[ProxyManager] System proxy {'ENABLED -> ' + server if enable else 'DISABLED'}.")
    except Exception as e:
        print(f"[ProxyManager] Failed to update system proxy: {e}", file=sys.stderr)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    proxy_addon = os.path.join(script_dir, "proxy.py")

    def cleanup():
        set_system_proxy(False)

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

    set_system_proxy(True)

    from mitmproxy.tools.main import mitmdump
    args = [
        "-s", proxy_addon,
        "-p", "8085",
        "--ssl-insecure",
        "--set", "stream_large_bodies=10m",
        "--set", "connection_strategy=lazy"
    ]
    print(f"[ProxyManager] Starting mitmdump on port 8085 with addon {proxy_addon}...")
    sys.stdout.flush()
    try:
        mitmdump(args)
    finally:
        set_system_proxy(False)

if __name__ == "__main__":
    if "--disable" in sys.argv or "--stop" in sys.argv:
        set_system_proxy(False)
        sys.exit(0)
    main()

