from __future__ import annotations

from typing import Any
from common.srtools import FreesrData, Monster

BOSS_PRESETS: dict[str, dict[str, Any]] = {
    # 周本大 Boss
    "sunday": {
        "name": "「齐响诗班」神主日",
        "stage_id": 1052056,
        "monster_id": 3025012,
        "aliases": ["神主日", "齐响诗班", "sunday", "szr"],
    },
    "cocolia": {
        "name": "可可利亚，虚妄之母",
        "stage_id": 1052026,
        "monster_id": 1005012,
        "aliases": ["可可利亚", "虚妄之母", "cocolia", "kkly"],
    },
    "phantylia": {
        "name": "不死神实•幻胧",
        "stage_id": 1052036,
        "monster_id": 8015021,
        "aliases": ["幻胧", "不死神实", "phantylia", "hl"],
    },
    "bug": {
        "name": "碎星王虫•斯喀拉卡巴兹",
        "stage_id": 1052046,
        "monster_id": 8025010,
        "aliases": ["碎星王虫", "王虫", "大虫子", "bug", "skarakabaz"],
    },
    "feixiao": {
        "name": "「飞霄」之影",
        "stage_id": 1052066,
        "monster_id": 2035010,
        "aliases": ["飞霄", "飞霄之影", "影将军", "feixiao", "fx"],
    },
    "doomsday": {
        "name": "末日兽",
        "stage_id": 1052016,
        "monster_id": 8015010,
        "aliases": ["末日兽", "doomsday", "mrs"],
    },
    "castorice": {
        "name": "万色返空主，归寂",
        "stage_id": 1052096,
        "monster_id": 8015030,
        "aliases": ["归寂", "万色返空主", "castorice", "amphoreus"],
    },
    "sky": {
        "name": "天空的化身",
        "stage_id": 1052076,
        "monster_id": 4015011,
        "aliases": ["天空的化身", "sky"],
    },
    "hate": {
        "name": "反造物主，流溢之恨",
        "stage_id": 1052086,
        "monster_id": 4035010,
        "aliases": ["流溢之恨", "hate"],
    },

    # 精英强敌
    "aventurine": {
        "name": "「石心十人」诡弈砂金",
        "stage_id": 30103122,
        "monster_id": 8034010,
        "aliases": ["砂金", "诡弈砂金", "aventurine", "shajin", "sj"],
    },
    "sam": {
        "name": "「星核猎手」萨姆",
        "stage_id": 30101112,
        "monster_id": 3024020,
        "aliases": ["萨姆", "sam", "sm"],
    },
    "hoolay": {
        "name": "步离战首•呼雷",
        "stage_id": 312059,
        "monster_id": 2034010,
        "aliases": ["呼雷", "步离战首", "hoolay", "hl2"],
    },
    "argenti": {
        "name": "纯美骑士•银枝",
        "stage_id": 312129,
        "monster_id": 3024010,
        "aliases": ["银枝", "argenti", "yz"],
    },
    "deer": {
        "name": "丰饶玄鹿",
        "stage_id": 307331,
        "monster_id": 2024011,
        "aliases": ["玄鹿", "丰饶玄鹿", "鹿", "deer", "xl"],
    },
    "svarog": {
        "name": "史瓦罗",
        "stage_id": 307021,
        "monster_id": 1014011,
        "aliases": ["史瓦罗", "svarog", "swl"],
    },
    "kafka": {
        "name": "「星核猎手」卡芙卡",
        "stage_id": 307031,
        "monster_id": 2004011,
        "aliases": ["卡芙卡", "kafka", "kfk"],
    },
    "cirrus": {
        "name": "浮烟",
        "stage_id": 83005201,
        "monster_id": 2024020,
        "aliases": ["浮烟", "cirrus", "fy"],
    },
    "yanqing": {
        "name": "云骑骁卫•彦卿",
        "stage_id": 30123122,
        "monster_id": 2004020,
        "aliases": ["彦卿", "yanqing", "yq"],
    },
    "gepard": {
        "name": "杰帕德",
        "stage_id": 30123122,
        "monster_id": 1004020,
        "aliases": ["杰帕德", "gepard", "jpd"],
    },
    "bronya": {
        "name": "布洛妮娅",
        "stage_id": 30123122,
        "monster_id": 1004030,
        "aliases": ["布洛妮娅", "bronya", "blny"],
    },
}

# Fast lookup map
_LOOKUP: dict[str, dict[str, Any]] = {}
for key, preset in BOSS_PRESETS.items():
    _LOOKUP[key.lower()] = preset
    for alias in preset.get("aliases", []):
        _LOOKUP[alias.lower()] = preset


def get_boss_preset(query: str) -> dict[str, Any] | None:
    return _LOOKUP.get(query.strip().lower())


def apply_boss(
    freesr_data: FreesrData,
    query_or_id: str,
    level: int = 95,
) -> tuple[bool, str]:
    query_str = query_or_id.strip()

    # Case 1: Check preset
    preset = get_boss_preset(query_str)
    if preset:
        mid = preset["monster_id"]
        sid = preset["stage_id"]
        name = preset["name"]
        freesr_data.battle_config.stage_id = sid
        freesr_data.battle_config.monsters = [
            [
                Monster(
                    monster_id=mid,
                    amount=1,
                    level=level,
                    cur_hp=None,
                    max_hp=None,
                )
            ]
        ]
        return True, f"{name} (id:{mid} lv:{level} stage:{sid})"

    # Case 2: Integer Monster ID
    try:
        mid = int(query_str)
        sid = 30123122
        freesr_data.battle_config.stage_id = sid
        freesr_data.battle_config.monsters = [
            [
                Monster(
                    monster_id=mid,
                    amount=1,
                    level=level,
                    cur_hp=None,
                    max_hp=None,
                )
            ]
        ]
        return True, f"Boss ID: {mid} (lv:{level} stage:{sid})"
    except ValueError:
        pass

    return False, f"Unknown boss: {query_str}"


def list_bosses() -> str:
    keys = [f"{k}({v['name']})" for k, v in list(BOSS_PRESETS.items())[:8]]
    return ", ".join(keys)

