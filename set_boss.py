import json
import sys
from pathlib import Path

from common.boss_config import BOSS_PRESETS, apply_boss, list_bosses
from common.srtools import FreesrData

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_PATH = Path(__file__).resolve().parent / "freesr-data.json"


def main():
    if len(sys.argv) < 2 or sys.argv[1].lower() in ("help", "-h", "--help"):
        print("Usage: python set_boss.py <boss_name_or_id> [level]")
        print("\nAvailable Presets:")
        for k, v in BOSS_PRESETS.items():
            print(f"  {k:12} : {v['name']} (Stage {v['stage_id']})")
        return

    query = sys.argv[1]
    if query.lower() == "list":
        print("Available Bosses:")
        for k, v in BOSS_PRESETS.items():
            print(f"  {k:12} : {v['name']}")
        return

    level = 95
    if len(sys.argv) > 2:
        try:
            level = int(sys.argv[2])
        except ValueError:
            pass

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    data = FreesrData.model_validate(raw)
    ok, msg = apply_boss(data, query, level)
    if not ok:
        print(f"[ERROR] {msg}")
        return

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        f.write(data.model_dump_json(indent=2))

    print(f"[OK] Successfully switched boss to: {msg}")


if __name__ == "__main__":
    main()
