import asyncio
import json
import time
from collections import OrderedDict

from common.db import MultiPath
from common.materials import get_all_materials
from common.util import AsyncFs, FreesrUtils, Log
from proto import (
    AvatarPathChangedNotify,
    AvatarSkillTree,
    AvatarType,
    BlackInfo,
    ClientDownloadData,
    DisplayAvatarDetailInfo,
    DisplayAvatarVec,
    GetAssistHistoryScRsp,
    GetBasicInfoScRsp,
    GetPamSkinDataCsReq,
    GetPamSkinDataScRsp,
    GetPhoneDataCsReq,
    GetPhoneDataScRsp,
    GetPlayerBoardDataScRsp,
    GetPlayerDetailInfoScRsp,
    HeadFrameInfo,
    HeadIconData,
    MultiPathAvatarType,
    PlatformType,
    PlayerBasicInfo,
    PlayerDetailInfo,
    PlayerGetTokenScRsp,
    PlayerHeartBeatCsReq,
    PlayerHeartBeatScRsp,
    PlayerLoginFinishScRsp,
    PlayerLoginScRsp,
    PlayerSettingInfo,
    PlayerSyncScNotify,
    SelectChatBubbleCsReq,
    SelectChatBubbleScRsp,
    SelectPamSkinCsReq,
    SelectPamSkinScRsp,
    SelectPhoneCaseCsReq,
    SelectPhoneCaseScRsp,
    SelectPhoneThemeCsReq,
    SelectPhoneThemeScRsp,
    SetHeadIconCsReq,
    SetHeadIconScRsp,
    SetPersonalCardCsReq,
    SetPersonalCardScRsp,
    SetSignatureCsReq,
    SetSignatureScRsp,
)

from common.cosmetics import (
    ALL_CHAT_BUBBLES,
    ALL_HEAD_FRAMES,
    ALL_PAM_SKINS,
    ALL_PHONE_CASES,
    ALL_PHONE_THEMES,
    get_all_head_icons,
    get_all_player_cards,
)

from ..connection import Connection
from ..handler import handler
from ..packet import Packet
from .avatar import build_avatar_sync

DEFAULT_SIGNATURE = "三生縁分 三千世界 三世因果"
MAX_SIGNATURE_BYTES = 50


@handler
async def on_player_get_token(c: Connection, pkt: Packet) -> None:
    rsp = PlayerGetTokenScRsp(
        uid=c.db.player.uid,
        black_info=BlackInfo(),
    )

    await c.send_packet(rsp)


@handler
async def on_player_heart_beat(c: Connection, pkt: Packet) -> None:
    t = int(time.time() * 1000)
    req = c.decode_packet(pkt, PlayerHeartBeatCsReq)
    rsp = PlayerHeartBeatScRsp(
        client_time_ms=req.client_time_ms,
        server_time_ms=t,
    )

    try:
        lua_content = await AsyncFs.read_to_str("main.lua")
        ## -- exec=XY
        ##         ↑↑
        ##         │└─ reset_after
        ##         └── should_execute
        marker = "-- exec="
        pos = lua_content.find(marker)

        if pos != -1:
            flag_pos = pos + len(marker)

            if len(lua_content) >= flag_pos + 2:
                should_execute = lua_content[flag_pos] == "t"
                reset_after = lua_content[flag_pos + 1] == "t"

                if should_execute:
                    rsp.download_data = ClientDownloadData(
                        version=51,
                        time=t,
                        data=lua_content.encode(),
                    )

                    if reset_after:
                        # tt -> ft
                        updated = (
                            lua_content[:flag_pos] + "f" + lua_content[flag_pos + 1 :]
                        )
                        try:
                            await AsyncFs.write_to_file("main.lua", updated)
                        except (OSError, ValueError) as e:
                            Log.warn(f"failed to update main.lua: {e}")
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as e:
        Log.error(e)

    await c.send_packet(rsp)


@handler
async def on_player_login(c: Connection, pkt: Packet) -> None:
    t = int(time.time() * 1000)
    rsp = PlayerLoginScRsp(
        basic_info=PlayerBasicInfo(
            nickname=c.db.player.name,
            level=70,
            stamina=240,
            world_level=6,
            hcoin=9999999,
            mcoin=9999999,
            scoin=99999999,
        ),
        server_timestamp_ms=t,
        stamina=240,
    )

    await c.send_packet(rsp)


@handler
async def on_get_basic_info(c: Connection, pkt: Packet) -> None:
    gender = 2 if (c.db.multi_path.tb_multi_path.to_int() & 1) == 0 else 1
    rsp = GetBasicInfoScRsp(
        cur_day=1,
        player_setting_info=PlayerSettingInfo(),
        is_gender_set=True,
        gender=gender,
    )

    await c.send_packet(rsp)


@handler
async def on_get_player_board_data(c: Connection, pkt: Packet) -> None:
    all_icons = [HeadIconData(id=i) for i in get_all_head_icons()]
    all_cards = get_all_player_cards()
    current_icon = c.db.player.head_icon if c.db.player.head_icon else 200143
    current_card = c.db.player.personal_card if c.db.player.personal_card else 253001

    rsp = GetPlayerBoardDataScRsp(
        signature=DEFAULT_SIGNATURE,
        current_head_icon_id=current_icon,
        unlocked_head_icon_list=all_icons,
        current_personal_card_id=current_card,
        unlocked_personal_card_list=all_cards,
        head_frame_info=HeadFrameInfo(
            head_frame_item_id=226004,
            head_frame_expire_time=int(time.time() * 1000) + 86400000000,
        ),
        display_avatar_vec=DisplayAvatarVec(is_display=False),
    )

    await c.send_packet(rsp)


@handler
async def on_get_player_detail_info(c: Connection, pkt: Packet) -> None:
    gender = 2 if (c.db.multi_path.tb_multi_path.to_int() & 1) == 0 else 1

    display = []
    for pos, a in enumerate(c.freesr_data.avatars.values()):
        if pos >= 6:
            break
        display.append(
            DisplayAvatarDetailInfo(
                avatar_id=a.avatar_id,
                avatar_type=int(AvatarType.AvatarType_AvatarFormalType),
                pos=pos,
                level=a.level,
                promotion=a.promotion,
                rank=a.data.rank,
                enhanced_id=a.enhanced_id or 0,
                dressed_skin_id=getattr(a, "dressed_skin_id", 0) or 0,
                skilltree_list=[
                    AvatarSkillTree(point_id=k, level=v)
                    for k, v in a.data.skills_by_anchor_type.items()
                ],
            )
        )

    assist = display[:4] or [DisplayAvatarDetailInfo(avatar_id=1001)]
    current_icon = c.db.player.head_icon if c.db.player.head_icon else 200143
    await c.send_packet(
        GetPlayerDetailInfoScRsp(
            detail_info=PlayerDetailInfo(
                uid=c.db.player.uid,
                world_level=5,
                platform=PlatformType.PC,
                signature=DEFAULT_SIGNATURE,
                display_avatar_list=display,
                assist_avatar_list=assist,
                is_banned=False,
                level=67,
                head_icon=current_icon,
                nickname=c.db.player.name,
                gender=gender,
                head_frame_info=HeadFrameInfo(
                    head_frame_item_id=226004,
                    head_frame_expire_time=(int(time.time()) + 86400) * 1000,
                ),
            )
        )
    )


@handler
async def on_get_assist_history(c: Connection, pkt: Packet) -> None:
    await c.send_packet(GetAssistHistoryScRsp())


@handler
async def on_set_head_icon(c: Connection, pkt: Packet) -> None:
    req = c.decode_packet(pkt, SetHeadIconCsReq)
    if req.id:
        c.db.player.head_icon = req.id
        asyncio.create_task(c.save_db())
    await c.send_packet(
        SetHeadIconScRsp(retcode=0, current_head_icon_id=c.db.player.head_icon)
    )


@handler
async def on_set_personal_card(c: Connection, pkt: Packet) -> None:
    req = c.decode_packet(pkt, SetPersonalCardCsReq)
    if req.id:
        c.db.player.personal_card = req.id
        asyncio.create_task(c.save_db())
    await c.send_packet(
        SetPersonalCardScRsp(
            retcode=0, current_personal_card_id=c.db.player.personal_card
        )
    )


@handler
async def on_get_phone_data(c: Connection, pkt: Packet) -> None:
    rsp = GetPhoneDataScRsp(
        cur_phone_theme=c.db.player.phone_theme or 221000,
        cur_phone_case=c.db.player.phone_case or 254000,
        cur_chat_bubble=c.db.player.chat_bubble or 220000,
        owned_phone_themes=ALL_PHONE_THEMES,
        owned_chat_bubbles=ALL_CHAT_BUBBLES,
        owned_phone_cases=ALL_PHONE_CASES,
        retcode=0,
    )
    await c.send_packet(rsp)


@handler
async def on_select_phone_theme(c: Connection, pkt: Packet) -> None:
    req = c.decode_packet(pkt, SelectPhoneThemeCsReq)
    if req.theme_id:
        c.db.player.phone_theme = req.theme_id
        asyncio.create_task(c.save_db())
    await c.send_packet(
        SelectPhoneThemeScRsp(
            retcode=0, cur_phone_theme=c.db.player.phone_theme
        )
    )


@handler
async def on_select_chat_bubble(c: Connection, pkt: Packet) -> None:
    req = c.decode_packet(pkt, SelectChatBubbleCsReq)
    if req.bubble_id:
        c.db.player.chat_bubble = req.bubble_id
        asyncio.create_task(c.save_db())
    await c.send_packet(
        SelectChatBubbleScRsp(
            retcode=0, cur_chat_bubble=c.db.player.chat_bubble
        )
    )


@handler
async def on_select_phone_case(c: Connection, pkt: Packet) -> None:
    req = c.decode_packet(pkt, SelectPhoneCaseCsReq)
    if req.phone_case_id:
        c.db.player.phone_case = req.phone_case_id
        asyncio.create_task(c.save_db())
    await c.send_packet(
        SelectPhoneCaseScRsp(
            retcode=0, cur_phone_case=c.db.player.phone_case
        )
    )


@handler
async def on_get_pam_skin_data(c: Connection, pkt: Packet) -> None:
    rsp = GetPamSkinDataScRsp(
        cur_skin=c.db.player.pam_skin or 252000,
        unlock_skin_list=ALL_PAM_SKINS,
    )
    await c.send_packet(rsp)


@handler
async def on_select_pam_skin(c: Connection, pkt: Packet) -> None:
    req = c.decode_packet(pkt, SelectPamSkinCsReq)
    if req.pam_skin:
        c.db.player.pam_skin = req.pam_skin
        asyncio.create_task(c.save_db())
    await c.send_packet(
        SelectPamSkinScRsp(
            set_skin=c.db.player.pam_skin, cur_skin=c.db.player.pam_skin
        )
    )


def truncate_sig(s: str) -> str:
    return s.encode("utf-8")[:MAX_SIGNATURE_BYTES].decode("utf-8", errors="ignore")


def parse_bool(args: list[str], default: bool) -> bool | None:
    if not args:
        return default
    a = args[0]
    if a in ("on", "1", "true"):
        return True
    if a in ("off", "0", "false"):
        return False
    return None


def parse_vore_level(s: str) -> int | None:
    try:
        level = int(s)
    except ValueError:
        return None
    return level if 0 <= level <= 3 else None


async def sync_player(c: Connection) -> None:
    await c.send_packet(
        PlayerSyncScNotify(
            del_relic_list=list(range(1, 3001)),
            del_equipment_list=list(range(3001, 3501)),
        )
    )
    await c.send_packet(
        PlayerSyncScNotify(avatar_sync=build_avatar_sync(c, equipped=False))
    )
    await c.send_packet(
        PlayerSyncScNotify(
            relic_list=[
                FreesrUtils.relic_to_relic_proto(r) for r in c.freesr_data.relics
            ],
            equipment_list=[
                FreesrUtils.lightcone_to_equipment_proto(lc)
                for lc in c.freesr_data.lightcones
            ],
            material_list=get_all_materials(),
            basic_info=PlayerBasicInfo(
                nickname=c.db.player.name,
                level=70,
                stamina=240,
                world_level=6,
                hcoin=9999999,
                mcoin=9999999,
                scoin=99999999,
            ),
        )
    )
    await c.send_packet(
        PlayerSyncScNotify(avatar_sync=build_avatar_sync(c, equipped=True))
    )


async def path_command(c: Connection, command: str, args: list[str]) -> str:
    if not args:
        return "missing id"
    is_tb = command == "tb"
    mp = MultiPath.parse(args[0])
    if mp is None:
        return f"unknown path: {truncate_sig(args[0])}"
    if is_tb and not (8001 <= mp.to_int() <= 8010):
        return "tb id must be 8001-8010"
    if not is_tb and mp not in (MultiPath.MARCH_PRESERVATION, MultiPath.MARCH_HUNT):
        return "m7 must be 1001/1224"

    if is_tb:
        if c.db.multi_path.tb_multi_path != mp:
            c.db.multi_path.tb_multi_path = mp
            asyncio.create_task(c.save_db())
        await c.send_packet(
            AvatarPathChangedNotify(
                base_avatar_id=8001,
                cur_multi_path_avatar_type=MultiPathAvatarType(mp.to_int()),
            )
        )
        await sync_player(c)
    else:
        if c.db.multi_path.march_multi_path != mp:
            c.db.multi_path.march_multi_path = mp
            asyncio.create_task(c.save_db())
        await c.send_packet(
            AvatarPathChangedNotify(
                base_avatar_id=1001,
                cur_multi_path_avatar_type=MultiPathAvatarType(mp.to_int()),
            )
        )
    return f"{command}: {mp.name.lower()}"


_NAME_TO_AVATAR_ID: dict[str, int] = {}


def _resolve_avatar_id(token: str) -> int | None:
    global _NAME_TO_AVATAR_ID
    if not _NAME_TO_AVATAR_ID:
        try:
            with open(
                "g:/sf/LunarCore/resources/TextMap/TextMapCHS.json",
                encoding="utf-8",
            ) as f:
                tmap = json.load(f)
            with open(
                "g:/sf/LunarCore/resources/ExcelOutput/AvatarConfig.json",
                encoding="utf-8",
            ) as f:
                acfg = json.load(f)
            for a in acfg:
                aid = a.get("AvatarID")
                h = str(a.get("AvatarName", {}).get("Hash", ""))
                name = tmap.get(h)
                if aid and name:
                    _NAME_TO_AVATAR_ID[name.lower()] = aid
        except Exception:
            pass

        aliases = {
            "acheron": 1308, "huangquan": 1308, "黄泉": 1308,
            "firefly": 1310, "liuying": 1310, "流萤": 1310,
            "sunday": 1313, "xingqiri": 1313, "星期日": 1313,
            "feixiao": 1220, "飞霄": 1220,
            "castorice": 1407, "xiadili": 1407, "遐蝶": 1407,
            "rappa": 1317, "乱破": 1317,
            "fugue": 1225, "guihuo": 1225, "归火": 1225, "忘归人": 1225,
            "tingyun": 1202, "停云": 1202,
            "sparkle": 1306, "huahuo": 1306, "花火": 1306,
            "blackswan": 1307, "heitiane": 1307, "黑天鹅": 1307,
            "aventurine": 1304, "shajin": 1304, "砂金": 1304,
            "robin": 1309, "zhiniao": 1309, "知更鸟": 1309,
            "boothill": 1315, "botihu": 1315, "波提欧": 1315,
            "jiaoqiu": 1218, "椒丘": 1218,
            "yunli": 1221, "云璃": 1221,
            "lingsha": 1222, "灵砂": 1222,
            "moze": 1223, "貊泽": 1223,
            "ruanmei": 1303, "阮梅": 1303,
            "silverwolf": 1006, "sw": 1006, "sw999": 1506, "银狼": 1006,
            "kafka": 1005, "卡芙卡": 1005,
            "blade": 1205, "刃": 1205,
            "danheng": 1002, "dhil": 1213, "饮月": 1213,
            "jingliu": 1212, "镜流": 1212,
            "jingyuan": 1204, "景元": 1204,
            "seele": 1102, "希儿": 1102,
            "bronya": 1101, "布洛妮娅": 1101,
            "luocha": 1203, "罗刹": 1203,
            "fuxuan": 1208, "符玄": 1208,
            "huohuo": 1217, "藿藿": 1217,
            # Fate Collaboration Avatars
            "saber": 1014, "阿尔托莉雅": 1014, "塞芭": 1014, "呆毛王": 1014, "吾王": 1014, "亚瑟王": 1014,
            "archer": 1015, "红a": 1015, "卫宫": 1015, "无铭": 1015, "emiya": 1015, "卫宫士郎": 1015,
            "rin": 1508, "tohsakarin": 1508, "远坂凛": 1508, "凛": 1508,
            "gilgamesh": 1509, "吉尔伽美什": 1509, "金闪闪": 1509, "闪闪": 1509, "英雄王": 1509,
        }
        _NAME_TO_AVATAR_ID.update(aliases)

    token = token.strip().lower()
    try:
        return int(token)
    except ValueError:
        return _NAME_TO_AVATAR_ID.get(token)


def lineup_command(c: Connection, args: list[str]) -> str:
    if not args or args[0] in ("list", "status"):
        cl = c.db.lineup.custom_battle_lineup
        if not cl:
            return f"cl: default ({len(c.db.lineup.overworld_lineup)} units)"
        ids = list(cl.values())
        return f"cl: {ids} ({len(ids)} units)"

    sub = args[0]
    if sub == "clear":
        c.db.lineup.custom_battle_lineup = None
        asyncio.create_task(c.save_db())
        return "cl: cleared"

    if sub == "add":
        targets = args[1:]
        lineup = c.db.lineup.custom_battle_lineup or OrderedDict()
        added = 0
        for token in targets:
            aid = _resolve_avatar_id(token)
            if aid is None:
                continue
            next_idx = max(lineup.keys()) + 1 if lineup else 0
            lineup[next_idx] = aid
            added += 1
        c.db.lineup.custom_battle_lineup = lineup
        asyncio.create_task(c.save_db())
        return f"cl: +{added} (total {len(lineup)})"

    # Direct setting: cl set <id...> or cl <id1> <id2> ...
    targets = args[1:] if sub == "set" else args
    new_lineup = OrderedDict()
    for token in targets:
        aid = _resolve_avatar_id(token)
        if aid is not None:
            new_lineup[len(new_lineup)] = aid

    if new_lineup:
        c.db.lineup.custom_battle_lineup = new_lineup
        asyncio.create_task(c.save_db())
        return f"cl: {len(new_lineup)} units {list(new_lineup.values())}"

    return "cl: use cl <ids/names...> or cl clear/add/list"



async def boss_command(c: Connection, args: list[str]) -> str:
    if not args or args[0] in ("list", "help"):
        from common.boss_config import list_bosses
        return f"bosses: {list_bosses()}"

    target = args[0]
    level = 95
    if len(args) > 1:
        try:
            level = int(args[1])
        except ValueError:
            pass

    from common.boss_config import apply_boss

    ok, msg = apply_boss(c.freesr_data, target, level)
    if ok:
        await c.save_freesr()
        return f"boss: {msg}"
    return f"boss err: {msg}"


async def stage_command(c: Connection, args: list[str]) -> str:
    if not args:
        return f"stage: {c.freesr_data.battle_config.stage_id}"
    try:
        sid = int(args[0])
        c.freesr_data.battle_config.stage_id = sid
        await c.save_freesr()
        return f"stage: {sid}"
    except ValueError:
        return "stage must be number"


@handler
async def on_set_signature(c: Connection, pkt: Packet) -> None:
    req = c.decode_packet(pkt, SetSignatureCsReq)
    parts = req.signature.lower().split()
    command = parts[0] if parts else ""
    parts = req.signature.split()
    command = parts[0].lower() if parts else ""
    args = parts[1:]
    feedback = None

    if command in ("tb", "m7"):
        feedback = await path_command(c, command, args)
    elif command == "boss":
        feedback = await boss_command(c, args)
    elif command == "stage":
        feedback = await stage_command(c, args)
    elif command == "sb":
        sub = args[0] if args else ""
        if sub == "vorelvl":
            if len(args) < 2:
                feedback = "vorelvl needs 0-3"
            else:
                level = parse_vore_level(args[1])
                if level is None:
                    feedback = "vorelvl needs 0-3"
                else:
                    if c.db.special_blessing.vore_level != level:
                        c.db.special_blessing.vore_level = level
                        asyncio.create_task(c.save_db())
                    feedback = f"vorelvl {level}"
        else:
            on = parse_bool(args[1:], True)
            if on is None:
                feedback = "sb needs on/off"
            else:
                match sub:
                    case "cast":
                        if c.db.special_blessing.castorice != on:
                            c.db.special_blessing.castorice = on
                            asyncio.create_task(c.save_db())
                        feedback = f"castorice {'on' if on else 'off'}"
                    case "sw":
                        if c.db.special_blessing.sw_999 != on:
                            c.db.special_blessing.sw_999 = on
                            asyncio.create_task(c.save_db())
                        feedback = f"sw {'on' if on else 'off'}"
                    case "vore":
                        if c.db.special_blessing.vore_override != on:
                            c.db.special_blessing.vore_override = on
                            asyncio.create_task(c.save_db())
                        feedback = f"vore {'on' if on else 'off'}"
                    case _:
                        feedback = "sb needs cast/sw/vore/vorelvl"
    elif command == "cl":
        feedback = lineup_command(c, args)
    elif command == "sync":
        await c.refresh_freesr()
        await sync_player(c)
        feedback = "synced"

    await c.send_packet(
        SetSignatureScRsp(
            signature=truncate_sig(
                feedback if feedback is not None else DEFAULT_SIGNATURE
            )
        )
    )


@handler
async def on_player_login_finish(c: Connection, pkt: Packet) -> None:
    await c.send_packet(PlayerLoginFinishScRsp())
