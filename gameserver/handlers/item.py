import asyncio

from common.materials import get_all_materials
from common.util import FreesrUtils
from proto import GetBagScRsp
from proto import (
    AddRelicFilterPlanCsReq,
    AddRelicFilterPlanScRsp,
    BatchRankUpEquipmentCsReq,
    BatchRankUpEquipmentScRsp,
    ComposeSelectedRelicCsReq,
    ComposeSelectedRelicScRsp,
    DeleteRelicFilterPlanCsReq,
    DeleteRelicFilterPlanScRsp,
    DiscardRelicCsReq,
    DiscardRelicScRsp,
    ExpUpEquipmentCsReq,
    ExpUpEquipmentScRsp,
    ExpUpRelicCsReq,
    ExpUpRelicScRsp,
    GetBagScRsp,
    GetRelicFilterPlanCsReq,
    GetRelicFilterPlanScRsp,
    LockEquipmentCsReq,
    LockEquipmentScRsp,
    LockRelicCsReq,
    LockRelicScRsp,
    MarkRelicFilterPlanCsReq,
    MarkRelicFilterPlanScRsp,
    ModifyRelicFilterPlanCsReq,
    ModifyRelicFilterPlanScRsp,
    PromoteEquipmentCsReq,
    PromoteEquipmentScRsp,
    RankUpEquipmentCsReq,
    RankUpEquipmentScRsp,
    RelicPresetAddPlanCsReq,
    RelicPresetAddPlanScRsp,
    RelicPresetDeletePlanCsReq,
    RelicPresetDeletePlanScRsp,
    RelicPresetGetPlanCsReq,
    RelicPresetGetPlanScRsp,
    RelicPresetUpdatePlanCsReq,
    RelicPresetUpdatePlanScRsp,
    RelicReforgeConfirmCsReq,
    RelicReforgeConfirmScRsp,
    RelicReforgeCsReq,
    RelicReforgeScRsp,
    RelicSmartWearAddPlanCsReq,
    RelicSmartWearAddPlanScRsp,
    RelicSmartWearDeletePlanCsReq,
    RelicSmartWearDeletePlanScRsp,
    RelicSmartWearGetPinRelicCsReq,
    RelicSmartWearGetPinRelicScRsp,
    RelicSmartWearGetPlanCsReq,
    RelicSmartWearGetPlanScRsp,
    RelicSmartWearUpdatePlanCsReq,
    RelicSmartWearUpdatePlanScRsp,
)

from ..connection import Connection
from ..handler import handler
from ..packet import Packet


async def _safe_sync_player(c: Connection) -> None:
    try:
        from .player import sync_player

        await sync_player(c)
    except Exception:
        pass


@handler
async def on_get_bag(c: Connection, pkt: Packet) -> None:
    rsp = GetBagScRsp(
        relic_list=[
            FreesrUtils.relic_to_relic_proto(relic) for relic in c.freesr_data.relics
        ],
        equipment_list=[
            FreesrUtils.lightcone_to_equipment_proto(lightcone)
            for lightcone in c.freesr_data.lightcones
        ],
        material_list=get_all_materials(),
    )

    await c.send_packet(rsp)


@handler
async def on_exp_up_equipment(c: Connection, pkt: Packet) -> None:
    req = ExpUpEquipmentCsReq.parse(pkt.body)
    for lc in c.freesr_data.lightcones:
        if lc.internal_uid == req.equipment_unique_id:
            lc.level = min(80, lc.level + 10)
            asyncio.create_task(c.save_freesr())
            break

    await c.send_packet(ExpUpEquipmentScRsp(retcode=0, return_item_list=[]))
    await _safe_sync_player(c)


@handler
async def on_rank_up_equipment(c: Connection, pkt: Packet) -> None:
    req = RankUpEquipmentCsReq.parse(pkt.body)
    for lc in c.freesr_data.lightcones:
        if lc.internal_uid == req.equipment_unique_id:
            lc.rank = min(5, lc.rank + 1)
            asyncio.create_task(c.save_freesr())
            break

    await c.send_packet(RankUpEquipmentScRsp(retcode=0))
    await _safe_sync_player(c)


@handler
async def on_batch_rank_up_equipment(c: Connection, pkt: Packet) -> None:
    await c.send_packet(BatchRankUpEquipmentScRsp(retcode=0))
    await _safe_sync_player(c)


@handler
async def on_promote_equipment(c: Connection, pkt: Packet) -> None:
    req = PromoteEquipmentCsReq.parse(pkt.body)
    for lc in c.freesr_data.lightcones:
        if lc.internal_uid == req.equipment_unique_id:
            lc.promotion = min(6, lc.promotion + 1)
            asyncio.create_task(c.save_freesr())
            break

    await c.send_packet(PromoteEquipmentScRsp(retcode=0))
    await _safe_sync_player(c)


@handler
async def on_lock_equipment(c: Connection, pkt: Packet) -> None:
    await c.send_packet(LockEquipmentScRsp(retcode=0))


@handler
async def on_exp_up_relic(c: Connection, pkt: Packet) -> None:
    req = ExpUpRelicCsReq.parse(pkt.body)
    for r in c.freesr_data.relics:
        if r.internal_uid == req.relic_unique_id:
            r.level = min(15, r.level + 3)
            asyncio.create_task(c.save_freesr())
            break

    await c.send_packet(ExpUpRelicScRsp(retcode=0, return_item_list=[]))
    await _safe_sync_player(c)


@handler
async def on_lock_relic(c: Connection, pkt: Packet) -> None:
    await c.send_packet(LockRelicScRsp(retcode=0))


@handler
async def on_discard_relic(c: Connection, pkt: Packet) -> None:
    req = DiscardRelicCsReq.parse(pkt.body)
    await c.send_packet(
        DiscardRelicScRsp(
            retcode=0,
            dkpcaigphno=req.dkpcaigphno,
            relic_ids=req.relic_ids,
            ifeejkmachf=req.ifeejkmachf,
        )
    )


@handler
async def on_compose_selected_relic(c: Connection, pkt: Packet) -> None:
    req = ComposeSelectedRelicCsReq.parse(pkt.body)
    await c.send_packet(
        ComposeSelectedRelicScRsp(retcode=0, compose_id=req.compose_id)
    )


@handler
async def on_relic_reforge(c: Connection, pkt: Packet) -> None:
    await c.send_packet(RelicReforgeScRsp(retcode=0))


@handler
async def on_relic_reforge_confirm(c: Connection, pkt: Packet) -> None:
    await c.send_packet(RelicReforgeConfirmScRsp(retcode=0))


@handler
async def on_get_relic_filter_plan(c: Connection, pkt: Packet) -> None:
    await c.send_packet(GetRelicFilterPlanScRsp(retcode=0, jckbeekbphf=[]))


@handler
async def on_add_relic_filter_plan(c: Connection, pkt: Packet) -> None:
    await c.send_packet(AddRelicFilterPlanScRsp(retcode=0))


@handler
async def on_modify_relic_filter_plan(c: Connection, pkt: Packet) -> None:
    await c.send_packet(ModifyRelicFilterPlanScRsp(retcode=0, nphajekcbkf=0, bncalamgioc=0))


@handler
async def on_delete_relic_filter_plan(c: Connection, pkt: Packet) -> None:
    await c.send_packet(DeleteRelicFilterPlanScRsp(retcode=0, ggigdjpfbbp=[], nppkabbjcmi=False))


@handler
async def on_mark_relic_filter_plan(c: Connection, pkt: Packet) -> None:
    await c.send_packet(MarkRelicFilterPlanScRsp(retcode=0, nppkabbjcmi=False, bijjojnjhdo=False, ggigdjpfbbp=[]))


@handler
async def on_relic_preset_get_plan(c: Connection, pkt: Packet) -> None:
    req = RelicPresetGetPlanCsReq.parse(pkt.body)
    await c.send_packet(RelicPresetGetPlanScRsp(retcode=0, avatar_id=req.avatar_id, relic_plan_list=[]))


@handler
async def on_relic_preset_add_plan(c: Connection, pkt: Packet) -> None:
    await c.send_packet(RelicPresetAddPlanScRsp(retcode=0))


@handler
async def on_relic_preset_delete_plan(c: Connection, pkt: Packet) -> None:
    req = RelicPresetDeletePlanCsReq.parse(pkt.body)
    await c.send_packet(RelicPresetDeletePlanScRsp(retcode=0, unique_id=req.unique_id))


@handler
async def on_relic_preset_update_plan(c: Connection, pkt: Packet) -> None:
    req = RelicPresetUpdatePlanCsReq.parse(pkt.body)
    await c.send_packet(RelicPresetUpdatePlanScRsp(retcode=0, unique_id=req.unique_id))


@handler
async def on_relic_smart_wear_get_plan(c: Connection, pkt: Packet) -> None:
    req = RelicSmartWearGetPlanCsReq.parse(pkt.body)
    await c.send_packet(RelicSmartWearGetPlanScRsp(retcode=0, avatar_id=req.avatar_id, relic_plan_list=[]))


@handler
async def on_relic_smart_wear_add_plan(c: Connection, pkt: Packet) -> None:
    await c.send_packet(RelicSmartWearAddPlanScRsp(retcode=0))


@handler
async def on_relic_smart_wear_update_plan(c: Connection, pkt: Packet) -> None:
    await c.send_packet(RelicSmartWearUpdatePlanScRsp(retcode=0))


@handler
async def on_relic_smart_wear_delete_plan(c: Connection, pkt: Packet) -> None:
    req = RelicSmartWearDeletePlanCsReq.parse(pkt.body)
    await c.send_packet(RelicSmartWearDeletePlanScRsp(retcode=0, unique_id=req.unique_id))


@handler
async def on_relic_smart_wear_get_pin_relic(c: Connection, pkt: Packet) -> None:
    req = RelicSmartWearGetPinRelicCsReq.parse(pkt.body)
    await c.send_packet(RelicSmartWearGetPinRelicScRsp(retcode=0, avatar_id=req.avatar_id, ojncaokpkib=[]))
