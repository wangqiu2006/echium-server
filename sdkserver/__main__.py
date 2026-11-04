import base64
import os
import sys

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from common import (
    ASSET_BUNDLE_URL,
    EX_RESOURCE_URL,
    GAMESERVER_ADDR,
    IFIX_URL,
    LUA_URL,
    SDKSERVER_ADDR,
    SEND_HOTFIX,
)
from proto import Dispatch, GateServer, RegionInfo


class Tee:
    def __init__(self, filename: str):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.file = open(filename, "a", encoding="utf-8")
        self.stdout = sys.__stdout__

    def write(self, data: str):
        self.stdout.write(data)
        self.file.write(data)
        self.file.flush()

    def flush(self):
        self.stdout.flush()
        self.file.flush()

    def isatty(self):
        return False

    def fileno(self):
        return self.stdout.fileno() if hasattr(self.stdout, "fileno") else 1


sys.stdout = Tee("logs/sdkserver.log")
sys.stderr = sys.stdout

app = FastAPI()


@app.middleware("http")
async def log_and_auto_heal_middleware(request: Request, call_next):
    print(f"[*] [SDK] {request.method} {request.url.path}")
    response = await call_next(request)
    if response.status_code == 404:
        path = request.url.path.lower()
        print(f"[!] [SDK 404 Intercepted -> Auto-Healing] {request.method} {request.url.path}")
        if "login" in path:
            return JSONResponse({
                "data": {
                    "account": {
                        "area_code": "**",
                        "email": "go.play@limbus.company",
                        "country": "ID",
                        "is_email_verify": "1",
                        "token": "arayashiki",
                        "uid": "1",
                    },
                    "token": {"token": "arayashiki", "token_type": 1},
                    "user_info": {
                        "aid": "1",
                        "mid": "1",
                        "account_name": "test111",
                        "is_email_verify": 1,
                        "area_code": "**",
                        "country": "ID",
                        "is_adult": 1,
                        "email": "go.play@limbus.company",
                    },
                    "account_type": 1,
                    "combo_id": "1",
                    "combo_token": "arayashiki",
                    "open_id": "1",
                    "device_grant_required": False,
                    "reactivate_required": False,
                    "realperson_required": False,
                    "safe_mobile_required": False,
                },
                "message": "OK",
                "retcode": 0,
            })
        elif "config" in path:
            return JSONResponse({
                "data": {
                    "id": 24,
                    "game_key": "hkrpg_cn",
                    "client": "PC",
                    "identity": "I_IDENTITY",
                    "guest": False,
                    "scene": "S_NORMAL",
                    "name": "崩坏：星穹铁道",
                    "protocol": True,
                    "vals": {"url": "", "enable": "false"},
                },
                "message": "OK",
                "retcode": 0,
            })
        elif "upload" in path or "log" in path or "report" in path or "telemetry" in path:
            return JSONResponse({"code": 0, "retcode": 0, "message": "OK"})
        elif "verify" in path:
            return JSONResponse({
                "data": {
                    "account": {
                        "area_code": "**",
                        "email": "go.play@limbus.company",
                        "token": "arayashiki",
                        "uid": "1",
                    },
                    "tokens": [{"token": "arayashiki", "token_type": 1}],
                    "user_info": {
                        "aid": "1",
                        "mid": "1",
                        "account_name": "test111",
                        "is_email_verify": 1,
                        "email": "go.play@limbus.company",
                    },
                },
                "message": "OK",
                "retcode": 0,
            })
    return response


def _varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _field_str(field: int, value: str) -> bytes:
    data = value.encode("utf-8")
    return _varint((field << 3) | 2) + _varint(len(data)) + data


def _field_varint(field: int, value: int) -> bytes:
    return _varint((field << 3) | 0) + _varint(value)


@app.head("/query_dispatch")
@app.get("/query_dispatch")
async def query_dispatch() -> PlainTextResponse:
    gateway_url = f"http://{SDKSERVER_ADDR[0]}:{SDKSERVER_ADDR[1]}/query_gateway"
    region_definitions = [
        ("prod_gf_cn", "星穹列车", "星穹列车"),
        ("prod_qd_cn", "无名客", "无名客"),
        ("House of Spiders", "H.O.S", "Lunar Core"),
        ("hos", "House of Spiders", "Lunar Core"),
        ("prod_official_asia", "Asia", "Asia"),
        ("prod_official_usa", "America", "America"),
        ("prod_official_euro", "Europe", "Europe"),
        ("prod_official_cht", "TW/HK/MO", "TW/HK/MO"),
    ]

    regions = [
        RegionInfo(
            name=name,
            title=title,
            dispatch_url=gateway_url,
            env_type="2",
            display_name=display,
        )
        for name, title, display in region_definitions
    ]
    rsp = Dispatch(
        retcode=0,
        msg="OK",
        top_sever_region_name="prod_gf_cn",
        region_list=regions,
    )
    rsp = bytes(rsp)
    rsp = base64.b64encode(rsp)

    return PlainTextResponse(rsp)


@app.head("/query_gateway/{region:path}")
@app.head("/query_gateway")
async def query_gateway_head(region: str = "") -> PlainTextResponse:
    return PlainTextResponse("")


@app.get("/query_gateway/{region:path}")
@app.get("/query_gateway")
async def query_gateway(request: Request, region: str = "") -> PlainTextResponse:
    if not region:
        region = request.query_params.get("region", "")
    if "?" in region:
        region = region.split("?")[0]
    if not region:
        region = "prod_gf_cn"

    ip = GAMESERVER_ADDR[0]
    port = GAMESERVER_ADDR[1]

    # Multi-version compatible protobuf union:
    # 4.4.53: port=3, region_name=6, asset_bundle_url=7, ip=9, ifix_version=1154
    # 4.5.51: lua_url=2, unk1=3, ex_resource_url=5, unk2=9, region_name=12,
    #         port=13, ip=14, asset_bundle_url=15, ifix_version=1094
    # Wire type mismatch allows single safe union:
    raw = bytearray()
    raw += _field_varint(1, 1)  # unk1 (4.4.53)
    raw += _field_varint(3, port)  # port (4.4.53) / unk1 (4.5.51)
    raw += _field_str(6, region)  # region_name (4.4.53)
    raw += _field_str(7, "")  # asset_bundle_url (4.4.53)
    raw += _field_str(9, ip)  # ip (4.4.53) / unk2 (4.5.51, skipped due to wire type mismatch)
    raw += _field_str(12, region)  # region_name (4.5.51)
    raw += _field_varint(13, port)  # port (4.5.51) / ex_resource_url (4.4.53, skipped)
    raw += _field_str(14, ip)  # ip (4.5.51)
    raw += _field_varint(15, 1)  # unk2 (4.4.53)
    for _f in (88, 416, 477, 623, 688, 736, 805, 816, 980, 1660):
        raw += _field_varint(_f, 1)
    raw += _field_str(1094, "0")  # ifix_version (4.5.51)
    raw += _field_str(1154, "0")  # ifix_version (4.4.53)

    if SEND_HOTFIX:
        raw += _field_str(2, LUA_URL)
        raw += _field_str(5, EX_RESOURCE_URL)
        raw += _field_str(7, ASSET_BUNDLE_URL)
        raw += _field_str(15, ASSET_BUNDLE_URL)
        raw += _field_str(120, IFIX_URL)

    rsp = base64.b64encode(bytes(raw))
    return PlainTextResponse(rsp)



@app.post("/hkrpg_cn/mdk/shield/api/login")
@app.post("/hkrpg_global/mdk/shield/api/login")
@app.post("/mdk/shield/api/login")
async def login_with_password() -> JSONResponse:
    rsp = {
        "data": {
            "account": {
                "area_code": "**",
                "email": "go.play@limbus.company",
                "country": "ID",
                "is_email_verify": "1",
                "token": "arayashiki",
                "uid": "1",
            },
            "device_grant_required": False,
            "reactivate_required": False,
            "realperson_required": False,
            "safe_mobile_required": False,
        },
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


@app.post("/hkrpg_cn/mdk/shield/api/verify")
@app.post("/hkrpg_global/mdk/shield/api/verify")
@app.post("/mdk/shield/api/verify")
async def login_with_session_token() -> JSONResponse:
    rsp = {
        "data": {
            "account": {
                "area_code": "**",
                "email": "go.play@limbus.company",
                "country": "ID",
                "is_email_verify": "1",
                "token": "arayashiki",
                "uid": "1",
            },
            "device_grant_required": False,
            "reactivate_required": False,
            "realperson_required": False,
            "safe_mobile_required": False,
        },
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


@app.post("/hkrpg_cn/combo/granter/login/v2/login")
@app.post("/hkrpg_global/combo/granter/login/v2/login")
@app.post("/combo/granter/login/v2/login")
async def granter_login_verification() -> JSONResponse:
    rsp = {
        "data": {
            "account_type": 1,
            "combo_id": "1",
            "combo_token": "arayashiki",
            "data": '{"guest":false}',
            "heartbeat": False,
            "open_id": "1",
        },
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


@app.get("/hkrpg_cn/mdk/shield/api/loadConfig")
@app.get("/hkrpg_global/mdk/shield/api/loadConfig")
@app.get("/mdk/shield/api/loadConfig")
async def load_config() -> JSONResponse:
    return JSONResponse({
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
            "enable_flash_login": False,
        },
    })


@app.post("/account/risky/api/check")
async def risky_api_check() -> JSONResponse:
    rsp = {
        "data": {"id": "arayashiki", "action": "ACTION_NONE", "geetest": None},
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


@app.post("/account/ma-cn-passport/app/loginByPassword")
@app.post("/account/ma-passport/app/loginByPassword")
@app.post("/account/ma-cn-passport/api/appLoginByPassword")
@app.post("/account/ma-passport/api/appLoginByPassword")
@app.post("/hkrpg_cn/account/ma-passport/api/appLoginByPassword")
@app.post("/hkrpg_global/account/ma-passport/api/appLoginByPassword")
@app.post("/hkrpg_cn/account/ma-passport/app/loginByPassword")
@app.post("/hkrpg_global/account/ma-passport/app/loginByPassword")
async def apn_login_with_password() -> JSONResponse:
    rsp = {
        "data": {
            "token": {"token": "arayashiki", "token_type": 1},
            "user_info": {
                "aid": "1",
                "mid": "1",
                "account_name": "test111",
                "is_email_verify": 1,
                "area_code": "**",
                "country": "ID",
                "is_adult": 1,
                "email": "go.play@limbus.company",
            },
        },
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


@app.post("/account/ma-cn-session/app/verify")
@app.post("/account/ma-session/app/verify")
async def apn_verify_token() -> JSONResponse:
    rsp = {
        "data": {
            "tokens": [{"token": "arayashiki", "token_type": 1}],
            "user_info": {
                "aid": "1",
                "mid": "1",
                "account_name": "test111",
                "is_email_verify": 1,
                "area_code": "**",
                "country": "ID",
                "is_adult": 1,
                "email": "go.play@limbus.company",
            },
        },
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


@app.get("/hkrpg_cn/mdk/shield/api/loadConfig")
@app.get("/hkrpg_global/mdk/shield/api/loadConfig")
async def load_config(request: Request) -> JSONResponse:
    game_key = "hkrpg_cn"
    rsp = {
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
            "enable_flash_login": False,
        },
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


@app.get("/hkrpg_cn/combo/granter/api/getConfig")
@app.get("/hkrpg_global/combo/granter/api/getConfig")
async def granter_get_config() -> JSONResponse:
    rsp = {
        "data": {
            "protocol": True,
            "qr_enabled": False,
            "log_level": "INFO",
            "announce_url": "",
            "push_alias_type": 0,
            "disable_ysdk_guard": True,
            "enable_announce_pic_popup": False,
            "app_name": "崩坏：星穹铁道",
            "qr_enabled_apps": {"bbs": False, "cloud": False},
            "qr_app_icons": {"app": "", "bbs": "", "cloud": ""},
            "qr_cloud_display_name": "",
            "enable_user_center": True,
            "functional_switch_configs": {},
        },
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


@app.get("/combo/box/api/config/sdk/combo")
async def combo_box_config() -> JSONResponse:
    rsp = {
        "data": {
            "vals": {
                "kibana_pc_config": '{ "enable": 0, "level": "Info","modules": ["download"] }\n',
                "network_report_config": '{ "enable": 0, "status_codes": [206], "url_paths": ["dataUpload", "red_dot"] }\n',
                "list_price_tierv2_enable": "true\n",
                "pay_payco_centered_host": "bill.payco.com",
                "telemetry_config": '{\n "dataupload_enable": 0,\n}',
                "enable_web_dpi": "true",
            }
        },
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


@app.get("/combo/box/api/config/sw/precache")
async def sw_precache() -> JSONResponse:
    rsp = {"data": {"vals": {"url": "", "enable": "false"}}, "message": "OK", "retcode": 0}

    return JSONResponse(rsp)


@app.api_route("/device-fp/api/getExtList", methods=["GET", "POST"])
async def device_fp_ext_list() -> JSONResponse:
    rsp = {
        "data": {
            "code": 200,
            "msg": "ok",
            "ext_list": [],
            "pkg_list": [],
            "pkg_str": "/vK5WTh5SS3SAj8Zm0qPWg==",
        },
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


@app.api_route("/device-fp/api/getFp", methods=["GET", "POST"])
async def device_fp() -> JSONResponse:
    return JSONResponse({"data": {"code": 200, "device_fp": "46903274", "msg": "ok"}, "message": "OK", "retcode": 0})


@app.get("/admin/mi18n/{path:path}")
async def mi18n(path: str) -> JSONResponse:
    return JSONResponse({"version": 134})


@app.post("/data_abtest_api/config/experiment/list")
async def abtest_experiment_list() -> JSONResponse:
    rsp = {
        "data": [
            {
                "code": 1000,
                "type": 2,
                "config_id": "14",
                "period_id": "6125_197",
                "version": "1",
                "configs": {"cardType": "direct"},
            }
        ],
        "message": "",
        "retcode": 0,
        "success": True,
    }

    return JSONResponse(rsp)


@app.api_route("/hkrpg_cn/combo/granter/api/compareProtocolVersion", methods=["GET", "POST"])
@app.api_route("/hkrpg_global/combo/granter/api/compareProtocolVersion", methods=["GET", "POST"])
async def compare_protocol_version() -> JSONResponse:
    rsp = {"data": {"modified": False, "protocol": None}, "message": "OK", "retcode": 0}

    return JSONResponse(rsp)


@app.get("/hkrpg_cn/mdk/agreement/api/getAgreementInfos")
@app.get("/hkrpg_global/mdk/agreement/api/getAgreementInfos")
async def agreement_infos() -> JSONResponse:
    rsp = {"data": {"marketing_agreements": []}, "message": "OK", "retcode": 0}

    return JSONResponse(rsp)


@app.post("/account/ma-cn-passport/token/verifySToken")
@app.post("/account/ma-passport/token/verifySToken")
@app.post("/hkrpg_cn/account/ma-passport/token/verifySToken")
@app.post("/hkrpg_global/account/ma-passport/token/verifySToken")
async def apn_verify_stoken() -> JSONResponse:
    rsp = {
        "data": {
            "token": {"token": "arayashiki", "token_type": 1},
            "user_info": {
                "aid": "1",
                "mid": "1",
                "account_name": "test111",
                "is_email_verify": 1,
                "area_code": "**",
                "country": "ID",
                "is_adult": 1,
                "email": "go.play@limbus.company",
            },
        },
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


@app.api_route("/account/ma-cn-passport/api/getConfig", methods=["GET", "POST"])
@app.api_route("/account/ma-passport/api/getConfig", methods=["GET", "POST"])
@app.api_route("/hkrpg_cn/account/ma-passport/api/getConfig", methods=["GET", "POST"])
@app.api_route("/hkrpg_global/account/ma-passport/api/getConfig", methods=["GET", "POST"])
async def apn_get_config() -> JSONResponse:
    rsp = {
        "data": {
            "ip": None,
            "tick_marketing_email": True,
            "area_wl": [],
            "realname_wl": [],
            "show_birthday": False,
            "age_gate_enabled": False,
            "age_gate_country_wl": [],
        },
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


@app.api_route("/sdk/dataUpload", methods=["GET", "POST"])
@app.api_route("/loginsdk/dataUpload", methods=["GET", "POST"])
@app.api_route("/crashdump/dataUpload", methods=["GET", "POST"])
@app.api_route("/apm/dataUpload", methods=["GET", "POST"])
@app.api_route("/log/sdk/upload", methods=["GET", "POST"])
@app.api_route("/common/h5log/log/batch", methods=["GET", "POST"])
async def sdk_data_upload() -> JSONResponse:
    return JSONResponse({"code": 0, "retcode": 0, "message": "OK", "data": None})


@app.post("/account/ma-cn-session/app/exchange")
@app.post("/account/ma-session/app/exchange")
async def apn_exchange_token() -> JSONResponse:
    rsp = {
        "data": {
            "token": {"token": "arayashiki", "token_type": 1},
            "user_info": {
                "aid": "1",
                "mid": "1",
                "account_name": "test111",
                "is_email_verify": 1,
                "area_code": "**",
                "country": "ID",
                "is_adult": 1,
                "email": "go.play@limbus.company",
            },
        },
        "message": "OK",
        "retcode": 0,
    }

    return JSONResponse(rsp)


if __name__ == "__main__":
    uvicorn.run(app, host=SDKSERVER_ADDR[0], port=SDKSERVER_ADDR[1])
