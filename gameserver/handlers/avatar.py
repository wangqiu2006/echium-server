import asyncio
from common.db import MultiPath
from common.util import FreesrUtils
from proto import (
    Avatar,
    AvatarExpUpCsReq,
    AvatarExpUpScRsp,
    AvatarPathChangedNotify,
    AvatarPathData,
    AvatarPathSkillTree,
    AvatarSync,
    DressAvatarCsReq,
    DressAvatarScRsp,
    DressAvatarSkinCsReq,
    DressAvatarSkinScRsp,
    DressRelicAvatarCsReq,
    DressRelicAvatarScRsp,
    GetAvatarDataScRsp,
    MarkAvatarCsReq,
    MarkAvatarScRsp,
    MultiPathAvatarType,
    PromoteAvatarCsReq,
    PromoteAvatarScRsp,
    RankUpAvatarCsReq,
    RankUpAvatarScRsp,
    SetAssistAvatarCsReq,
    SetAssistAvatarScRsp,
    SetAvatarEnhancedIdScRsp,
    SetAvatarPathCsReq,
    SetAvatarPathScRsp,
    SetDisplayAvatarCsReq,
    SetDisplayAvatarScRsp,
    SetGrowthTargetAvatarCsReq,
    SetGrowthTargetAvatarScRsp,
    SetIsDisplayAvatarInfoCsReq,
    SetIsDisplayAvatarInfoScRsp,
    TakeOffAvatarSkinCsReq,
    TakeOffAvatarSkinScRsp,
    TakeOffEquipmentCsReq,
    TakeOffEquipmentScRsp,
    TakeOffRelicCsReq,
    TakeOffRelicScRsp,
    TakePromotionRewardScRsp,
    UnlockSkillTreeCsReq,
    UnlockSkillTreeScRsp,
)

from ..connection import Connection


def build_avatar_sync(c: Connection, equipped: bool = True) -> AvatarSync:
    lightcone_uid_by_avatar = (
        {lc.equip_avatar: lc.internal_uid for lc in c.freesr_data.lightcones}
        if equipped
        else {}
    )

    seen_base_ids = set()
    avatar_list = []
    for av in c.freesr_data.avatars.values():
        base_id = MultiPath.get_base_id(av.avatar_id)
        if base_id in seen_base_ids:
            continue
        seen_base_ids.add(base_id)

        active_id = (
            c.db.multi_path.tb_multi_path.to_int()
            if base_id == 8001
            else c.db.multi_path.march_multi_path.to_int()
            if base_id == 1001
            else base_id
        )

        avatar = Avatar(
            base_avatar_id=base_id,
            level=av.level,
            promotion=av.promotion,
            first_met_time_stamp=1712924677,
            equipment_unique_id=lightcone_uid_by_avatar.get(
                active_id, lightcone_uid_by_avatar.get(base_id, 0)
            ),
            has_taken_promotion_reward_list=[1, 3, 5],
            cur_multi_path_avatar_type=active_id,
        )
        avatar_list.append(avatar)

    relics_by_avatar = (
        {
            avatar: [
                FreesrUtils.relic_to_equip_relic_proto(relic)
                for relic in c.freesr_data.relics
                if relic.equip_avatar == avatar
            ]
            for avatar in {relic.equip_avatar for relic in c.freesr_data.relics}
        }
        if equipped
        else {}
    )

    path_list = [
        AvatarPathData(
            avatar_id=av.avatar_id,
            rank=av.data.rank,
            equip_relic_list=relics_by_avatar.get(av.avatar_id, []),
            avatar_path_skill_tree=[
                AvatarPathSkillTree(
                    point_id=k,
                    level=v,
                )
                for k, v in av.data.skills_by_anchor_type.items()
            ],
            path_equipment_id=lightcone_uid_by_avatar.get(av.avatar_id, 0),
            unk_enhanced_id=av.enhanced_id or 0,
            unlock_timestamp=1712924677,
            dressed_skin_id=getattr(av, "dressed_skin_id", 0) or 0,
        )
        for av in c.freesr_data.avatars.values()
    ]

    return AvatarSync(avatar_list=avatar_list, avatar_path_data_info_list=path_list)


from ..handler import handler
from ..packet import Packet
from common.cosmetics import ALL_AVATAR_SKINS


async def _safe_sync_player(c: Connection) -> None:
    try:
        from .player import sync_player

        await sync_player(c)
    except Exception:
        pass


@handler
async def on_get_avatar_data(c: Connection, pkt: Packet) -> None:
    sync = build_avatar_sync(c)

    multi_path_ids = [
        av.avatar_id
        for av in c.freesr_data.avatars.values()
        if av.avatar_id in (1001, 1224) or 8001 <= av.avatar_id <= 8010
    ]

    rsp = GetAvatarDataScRsp(
        is_get_all=True,
        avatar_list=sync.avatar_list,
        avatar_path_data_info_list=sync.avatar_path_data_info_list,
        basic_type_id_list=multi_path_ids,
        skin_list=ALL_AVATAR_SKINS,
    )

    await c.send_packet(rsp)


@handler
async def on_take_promotion_reward(c: Connection, pkt: Packet) -> None:
    await c.send_packet(TakePromotionRewardScRsp())


@handler
async def on_set_avatar_enhanced_id(c: Connection, pkt: Packet) -> None:
    await c.send_packet(SetAvatarEnhancedIdScRsp())


@handler
async def on_set_avatar_path(c: Connection, pkt: Packet) -> None:
    req = SetAvatarPathCsReq.parse(pkt.body)
    aid = int(req.avatar_id)
    if aid in (1001, 1224):
        mp = MultiPath.from_id(aid)
        if mp:
            c.db.multi_path.march_multi_path = mp
            asyncio.create_task(c.save_db())
            await c.send_packet(
                AvatarPathChangedNotify(
                    base_avatar_id=1001,
                    cur_multi_path_avatar_type=MultiPathAvatarType(aid),
                )
            )
    elif 8001 <= aid <= 8010:
        mp = MultiPath.from_id(aid)
        if mp:
            c.db.multi_path.tb_multi_path = mp
            asyncio.create_task(c.save_db())
            await c.send_packet(
                AvatarPathChangedNotify(
                    base_avatar_id=8001,
                    cur_multi_path_avatar_type=MultiPathAvatarType(aid),
                )
            )
    await c.send_packet(SetAvatarPathScRsp(avatar_id=req.avatar_id))
    await _safe_sync_player(c)


@handler
async def on_dress_relic_avatar(c: Connection, pkt: Packet) -> None:
    req = DressRelicAvatarCsReq.parse(pkt.body)
    for param in req.switch_list:
        for r in c.freesr_data.relics:
            if r.equip_avatar == req.avatar_id and (r.relic_id % 10) == param.relic_type:
                r.equip_avatar = 0
            if r.internal_uid == param.relic_unique_id:
                r.equip_avatar = req.avatar_id

    await c.send_packet(DressRelicAvatarScRsp())
    await _safe_sync_player(c)


@handler
async def on_take_off_relic(c: Connection, pkt: Packet) -> None:
    req = TakeOffRelicCsReq.parse(pkt.body)
    for r in c.freesr_data.relics:
        if r.equip_avatar == req.avatar_id and (r.relic_id % 10) in req.relic_type_list:
            r.equip_avatar = 0

    await c.send_packet(TakeOffRelicScRsp())
    await _safe_sync_player(c)


@handler
async def on_dress_avatar(c: Connection, pkt: Packet) -> None:
    req = DressAvatarCsReq.parse(pkt.body)
    for lc in c.freesr_data.lightcones:
        if lc.equip_avatar == req.avatar_id:
            lc.equip_avatar = 0
        if lc.internal_uid == req.equipment_unique_id:
            lc.equip_avatar = req.avatar_id

    await c.send_packet(DressAvatarScRsp())
    await _safe_sync_player(c)


@handler
async def on_take_off_equipment(c: Connection, pkt: Packet) -> None:
    req = TakeOffEquipmentCsReq.parse(pkt.body)
    for lc in c.freesr_data.lightcones:
        if lc.equip_avatar == req.avatar_id:
            lc.equip_avatar = 0

    await c.send_packet(TakeOffEquipmentScRsp())
    await _safe_sync_player(c)

import json
from pathlib import Path

_POINT_TO_ANCHOR: dict[int, tuple[int, int]] = {}


def _get_point_info(point_id: int) -> tuple[int, int] | None:
    global _POINT_TO_ANCHOR
    if not _POINT_TO_ANCHOR:
        cfg_path = Path("G:/sf/LunarCore/resources/ExcelOutput/AvatarSkillTreeConfig.json")
        if cfg_path.exists():
            try:
                with open(cfg_path, encoding="utf-8") as f:
                    tree = json.load(f)
                for entry in tree:
                    pid = entry.get("PointID")
                    aid = entry.get("AvatarID")
                    atype = entry.get("AnchorType")
                    if pid and aid and atype:
                        try:
                            anchor = int(atype.replace("Point", ""))
                            _POINT_TO_ANCHOR[pid] = (aid, anchor)
                        except ValueError:
                            pass
            except Exception:
                pass
    return _POINT_TO_ANCHOR.get(point_id)


@handler
async def on_unlock_skill_tree(c: Connection, pkt: Packet) -> None:
    req = UnlockSkillTreeCsReq.parse(pkt.body)
    info = _get_point_info(req.point_id)
    if info:
        aid, anchor = info
        if av := c.freesr_data.avatars.get(aid):
            av.data.skills[req.point_id] = req.level
            av.data.skills_by_anchor_type[anchor] = req.level
            asyncio.create_task(c.save_freesr())
    else:
        for av in c.freesr_data.avatars.values():
            if req.point_id in av.data.skills or str(req.point_id).startswith(str(av.avatar_id)):
                av.data.skills[req.point_id] = req.level
                asyncio.create_task(c.save_freesr())
                break

    await c.send_packet(
        UnlockSkillTreeScRsp(retcode=0, point_id=req.point_id, level=req.level)
    )
    await _safe_sync_player(c)


@handler
async def on_avatar_exp_up(c: Connection, pkt: Packet) -> None:
    req = AvatarExpUpCsReq.parse(pkt.body)
    if av := c.freesr_data.avatars.get(req.base_avatar_id):
        av.level = min(80, av.level + 10)
        asyncio.create_task(c.save_freesr())

    await c.send_packet(AvatarExpUpScRsp(retcode=0, return_item_list=[]))
    await _safe_sync_player(c)


@handler
async def on_promote_avatar(c: Connection, pkt: Packet) -> None:
    req = PromoteAvatarCsReq.parse(pkt.body)
    if av := c.freesr_data.avatars.get(req.base_avatar_id):
        av.promotion = min(6, av.promotion + 1)
        asyncio.create_task(c.save_freesr())

    await c.send_packet(PromoteAvatarScRsp(retcode=0))
    await _safe_sync_player(c)


@handler
async def on_rank_up_avatar(c: Connection, pkt: Packet) -> None:
    req = RankUpAvatarCsReq.parse(pkt.body)
    if av := c.freesr_data.avatars.get(req.avatar_id):
        av.data.rank = min(6, req.rank)
        asyncio.create_task(c.save_freesr())

    await c.send_packet(RankUpAvatarScRsp(retcode=0))
    await _safe_sync_player(c)


@handler
async def on_mark_avatar(c: Connection, pkt: Packet) -> None:
    req = MarkAvatarCsReq.parse(pkt.body)
    await c.send_packet(
        MarkAvatarScRsp(retcode=0, avatar_id=req.avatar_id, is_marked=req.is_marked)
    )


@handler
async def on_set_growth_target_avatar(c: Connection, pkt: Packet) -> None:
    req = SetGrowthTargetAvatarCsReq.parse(pkt.body)
    await c.send_packet(
        SetGrowthTargetAvatarScRsp(retcode=0, growth_avatar_id=getattr(req, "avatar_id", 0))
    )


@handler
async def on_dress_avatar_skin(c: Connection, pkt: Packet) -> None:
    req = c.decode_packet(pkt, DressAvatarSkinCsReq)
    aid = int(getattr(req, "avatar_id", 0))
    skin_id = int(getattr(req, "skin_id", 0))
    if aid in c.freesr_data.avatars:
        c.freesr_data.avatars[aid].dressed_skin_id = skin_id
        asyncio.create_task(c.save_freesr())
    await c.send_packet(DressAvatarSkinScRsp(retcode=0))
    await _safe_sync_player(c)


@handler
async def on_take_off_avatar_skin(c: Connection, pkt: Packet) -> None:
    req = c.decode_packet(pkt, TakeOffAvatarSkinCsReq)
    aid = int(getattr(req, "avatar_id", 0))
    if aid in c.freesr_data.avatars:
        c.freesr_data.avatars[aid].dressed_skin_id = 0
        asyncio.create_task(c.save_freesr())
    await c.send_packet(TakeOffAvatarSkinScRsp(retcode=0))
    await _safe_sync_player(c)


@handler
async def on_set_display_avatar(c: Connection, pkt: Packet) -> None:
    await c.send_packet(SetDisplayAvatarScRsp(retcode=0))


@handler
async def on_set_is_display_avatar_info(c: Connection, pkt: Packet) -> None:
    req = SetIsDisplayAvatarInfoCsReq.parse(pkt.body)
    await c.send_packet(
        SetIsDisplayAvatarInfoScRsp(retcode=0, is_display=req.is_display)
    )


@handler
async def on_set_assist_avatar(c: Connection, pkt: Packet) -> None:
    req = SetAssistAvatarCsReq.parse(pkt.body)
    await c.send_packet(SetAssistAvatarScRsp(retcode=0, avatar_id=req.avatar_id))



