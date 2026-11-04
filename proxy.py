"""
Star Rail local dispatch redirector addon for mitmproxy.
Intercepts game client HTTPS requests and returns local LunarCore responses
directly without upstream TLS timeouts, guaranteeing that:
1. LoadConfig always forces the Chinese official client UI (hkrpg_cn).
2. All dispatch, gateway, and auth calls reach local LunarCore port 80.
3. Telemetry/log/upload requests receive fast 200 OK responses to avoid Unity Curl timeout errors.
"""
import json
import urllib.request
import urllib.error
from mitmproxy import http

TARGET_DOMAINS = (
    "starrails.com",
    "hoyoverse.com",
    "mihoyo.com",
    "bhsr.com",
)

LUNAR_CORE_URL = "http://127.0.0.1:21000"

# Pre-packaged responses
RESP_LOAD_CONFIG = json.dumps({
    "retcode": 0,
    "message": "OK",
    "data": {
        "id": 24,
        "game_key": "hkrpg_cn",
        "client": "PC",
        "identity": "I_IDENTITY",
        "guest": False,
        "ignore_versions": "",
        "scene": "S_NORMAL",
        "name": "崩坏：星穹铁道",
        "disable_regist": False,
        "enable_email_captcha": False,
        "thirdparty": [],
        "disable_mmt": False,
        "server_guest": False,
        "thirdparty_ignore": {},
        "enable_ps_bind_account": False,
        "thirdparty_login_configs": {},
        "initialize_firebase": False,
        "bbs_auth_login": False,
        "bbs_auth_login_ignore": [],
        "fetch_instance_id": False,
        "enable_flash_login": False
    }
}).encode("utf-8")

RESP_COMBO_CONFIG = json.dumps({
    "retcode": 0,
    "message": "OK",
    "data": {
        "vals": {
            "kibana_pc_config": "{ \"enable\": 0, \"level\": \"Info\",\"modules\": [\"download\"] }\n",
            "network_report_config": "{ \"enable\": 0, \"status_codes\": [206], \"url_paths\": [\"dataUpload\", \"red_dot\"] }\n",
            "list_price_tierv2_enable": "true\n",
            "pay_payco_centered_host": "bill.payco.com",
            "telemetry_config": "{\n \"dataupload_enable\": 0,\n}",
            "enable_web_dpi": "true"
        }
    }
}).encode("utf-8")

RESP_SW_PRECACHE = b'{"retcode":0,"message":"OK","data":{"vals":{"url":"","enable":"false"}}}'
RESP_PROTOCOL = b'{"retcode":0,"message":"OK","data":{"modified":false,"protocol":null}}'
RESP_AGREEMENT = b'{"retcode":0,"message":"OK","data":{"marketing_agreements":[]}}'
RESP_GENERIC_OK = b'{"code":0,"retcode":0,"message":"OK","data":{}}'

class StarRailRedirect:
    def request(self, flow: http.HTTPFlow):
        host = flow.request.pretty_host
        if not any(host == d or host.endswith("." + d) for d in TARGET_DOMAINS):
            return

        path = flow.request.path
        method = flow.request.method

        # 1. Force Chinese official client configuration
        if "loadConfig" in path:
            flow.response = http.Response.make(
                200,
                RESP_LOAD_CONFIG,
                {"Content-Type": "application/json; charset=utf-8"}
            )
            print(f"[StarRail Proxy] Handled loadConfig -> CN Mode (hkrpg_cn)")
            return

        # 2. SDK combo configs
        if "/combo/box/api/config/sdk/combo" in path:
            flow.response = http.Response.make(
                200,
                RESP_COMBO_CONFIG,
                {"Content-Type": "application/json; charset=utf-8"}
            )
            return

        if "/combo/box/api/config/sw/precache" in path:
            flow.response = http.Response.make(
                200,
                RESP_SW_PRECACHE,
                {"Content-Type": "application/json; charset=utf-8"}
            )
            return

        if "compareProtocolVersion" in path:
            flow.response = http.Response.make(
                200,
                RESP_PROTOCOL,
                {"Content-Type": "application/json; charset=utf-8"}
            )
            return

        if "getAgreementInfos" in path:
            flow.response = http.Response.make(
                200,
                RESP_AGREEMENT,
                {"Content-Type": "application/json; charset=utf-8"}
            )
            return

        # 3. Log / telemetry / crashdump fast response to avoid timeout
        if any(x in path for x in ("dataUpload", "apm", "crashdump", "h5log", "log/batch", "red_dot", "action=ACTION_NONE")):
            flow.response = http.Response.make(
                200,
                RESP_GENERIC_OK,
                {"Content-Type": "application/json; charset=utf-8"}
            )
            return

        # 4. Map paths if necessary
        target_path = path
        if "appLoginByPassword" in path or "loginByPassword" in path:
            target_path = "/account/ma-cn-passport/app/loginByPassword"
        elif "verifySToken" in path:
            target_path = "/account/ma-cn-passport/token/verifySToken"
        elif "/account/" in path and "getConfig" in path:
            target_path = "/account/ma-cn-passport/api/getConfig"
        elif "/hkrpg_global/" in target_path:
            target_path = target_path.replace("/hkrpg_global/", "/hkrpg_cn/")

        # 5. Forward to local LunarCore HTTP server (port 80)
        target_url = f"{LUNAR_CORE_URL}{target_path}"
        headers = {k: v for k, v in flow.request.headers.items() if k.lower() not in ("host", "content-length")}
        body = flow.request.raw_content if method in ("POST", "PUT") else None

        req = urllib.request.Request(target_url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                content = resp.read()
                resp_headers = {}
                for k, v in resp.getheaders():
                    if k.lower() not in ("transfer-encoding", "content-encoding"):
                        resp_headers[k] = v
                flow.response = http.Response.make(resp.status, content, resp_headers)
                print(f"[StarRail Proxy] Forwarded {method} {path} -> {resp.status}")
        except urllib.error.HTTPError as e:
            content = e.read()
            flow.response = http.Response.make(e.code, content, dict(e.headers))
            print(f"[StarRail Proxy] Forwarded {method} {path} -> HTTP {e.code}")
        except Exception as e:
            print(f"[StarRail Proxy] Forward Error for {path}: {e}")
            flow.response = http.Response.make(
                200,
                RESP_GENERIC_OK,
                {"Content-Type": "application/json; charset=utf-8"}
            )

addons = [StarRailRedirect()]
