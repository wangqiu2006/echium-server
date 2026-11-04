import json
from pathlib import Path

RES_DIR = Path("G:/sf/LunarCore/resources/ExcelOutput")

ALL_AVATAR_SKINS: list[int] = [1100101, 1130301, 1131001, 1141501, 1140701, 1150101]
ALL_PAM_SKINS: list[int] = [252000, 252001, 252002, 252003, 252004]
ALL_PHONE_THEMES: list[int] = [
    221000, 221001, 221002, 221003, 221004, 221005, 221006, 221007,
    221008, 221009, 221010, 221011, 221012, 221013,
]
ALL_CHAT_BUBBLES: list[int] = [
    220000, 220001, 220002, 220003, 220004, 220005, 220006, 220007,
    220008, 220009, 220010, 220012,
]
ALL_PHONE_CASES: list[int] = [254000, 254001]
ALL_HEAD_FRAMES: list[int] = [226001, 226002, 226003, 226004, 226005]
ALL_PLAYER_OUTFITS: list[int] = [
    1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010,
    1012, 1013, 1016, 2000, 2100, 2200, 2300, 2400, 3000, 3001, 4000, 4001,
]

_HEAD_ICONS_CACHE: list[int] | None = None
_PLAYER_CARDS_CACHE: list[int] | None = None


def get_all_head_icons() -> list[int]:
    global _HEAD_ICONS_CACHE
    if _HEAD_ICONS_CACHE is not None:
        return _HEAD_ICONS_CACHE
    icons = set()
    for fname in ("PlayerIcon.json", "AvatarPlayerIcon.json", "AvatarPlayerIconLD.json"):
        p = RES_DIR / fname
        if p.exists():
            try:
                with open(p, encoding="utf-8") as f:
                    for x in json.load(f):
                        if "ID" in x:
                            icons.add(x["ID"])
            except Exception:
                pass
    if not icons:
        icons = {200143}
    _HEAD_ICONS_CACHE = sorted(icons)
    return _HEAD_ICONS_CACHE


def get_all_player_cards() -> list[int]:
    global _PLAYER_CARDS_CACHE
    if _PLAYER_CARDS_CACHE is not None:
        return _PLAYER_CARDS_CACHE
    p = RES_DIR / "PlayerPersonalCard.json"
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                _PLAYER_CARDS_CACHE = [x["CardID"] for x in json.load(f) if "CardID" in x]
                return _PLAYER_CARDS_CACHE
        except Exception:
            pass
    _PLAYER_CARDS_CACHE = [253000, 253001, 253002, 253003, 253004, 253005]
    return _PLAYER_CARDS_CACHE

