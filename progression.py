"""Persistent player progress, currency and skill upgrades for SEF."""
import json
import os
from game_paths import progress_path

PROGRESS_FILE = progress_path()
DEFAULT_PROGRESS = {
    "coins": 0,
    "unlocked_stage": 1,
    "completed_stages": [],
    "sword_level": 0,
    "shield_unlocked": False,
    "spear_unlocked": False,
    "extra_jump_level": 0,
    "berserk_level": 0,
}


def load_progress():
    data = dict(DEFAULT_PROGRESS)
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            data.update(saved)
    except (OSError, ValueError, TypeError):
        pass
    data["coins"] = max(0, int(data.get("coins", 0)))
    data["unlocked_stage"] = max(1, min(12, int(data.get("unlocked_stage", 1))))
    data["completed_stages"] = sorted({int(x) for x in data.get("completed_stages", []) if 1 <= int(x) <= 12})
    for key in ("sword_level", "extra_jump_level", "berserk_level"):
        data[key] = max(0, int(data.get(key, 0)))
    data["shield_unlocked"] = bool(data.get("shield_unlocked", False))
    data["spear_unlocked"] = bool(data.get("spear_unlocked", False))
    return data


def save_progress(data):
    folder = os.path.dirname(PROGRESS_FILE)
    os.makedirs(folder, exist_ok=True)
    tmp = PROGRESS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PROGRESS_FILE)


def add_coins(data, amount):
    data["coins"] = max(0, int(data.get("coins", 0)) + int(amount))
    save_progress(data)


def complete_stage(data, stage):
    stage = int(stage)
    completed = set(data.get("completed_stages", []))
    completed.add(stage)
    data["completed_stages"] = sorted(completed)
    data["unlocked_stage"] = max(int(data.get("unlocked_stage", 1)), min(12, stage + 1))
    save_progress(data)
