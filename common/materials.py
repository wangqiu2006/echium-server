import json
from pathlib import Path
import proto

_MATERIALS_CACHE: list[proto.Material] | None = None

def get_all_materials() -> list[proto.Material]:
    global _MATERIALS_CACHE
    if _MATERIALS_CACHE is not None:
        return _MATERIALS_CACHE

    item_config_path = Path("G:/sf/LunarCore/resources/ExcelOutput/ItemConfig.json")
    if not item_config_path.exists():
        return []

    try:
        with open(item_config_path, encoding="utf-8") as f:
            items = json.load(f)
    except Exception:
        return []

    item_ids = []
    seen = set()
    for it in items:
        mtype = it.get("ItemMainType")
        iid = it.get("ID")
        if mtype in ("Material", "Usable") and iid not in seen:
            seen.add(iid)
            item_ids.append(iid)

    # Key virtual currencies / items
    for v in [21, 22, 23, 24, 101, 102, 251, 252, 253]:
        if v not in seen:
            seen.add(v)
            item_ids.append(v)

    # Extra item configs: Skins, Disks, Cards, HeadIcons, Collaboration/LD
    extra_files = [
        "ItemConfigAvatarSkin.json",
        "ItemConfigDisk.json",
        "ItemPlayerCard.json",
        "ItemConfigAvatarPlayerIcon.json",
        "ItemConfigAvatarLD.json",
        "ItemConfigAvatarRankLD.json",
        "ItemConfigAvatarPlayerIcLD.json",
        "ItemConfigLD.json",
    ]
    for ef in extra_files:
        ef_path = Path("G:/sf/LunarCore/resources/ExcelOutput") / ef
        if ef_path.exists():
            try:
                with open(ef_path, encoding="utf-8") as f:
                    extra_items = json.load(f)
                for it in extra_items:
                    iid = it.get("ID")
                    if iid and iid not in seen:
                        seen.add(iid)
                        item_ids.append(iid)
            except Exception:
                pass

    _MATERIALS_CACHE = [proto.Material(tid=iid, num=9999 if iid < 1000000 else 1) for iid in item_ids]
    return _MATERIALS_CACHE

