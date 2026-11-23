"""progress.json persistence."""
import json
from datetime import datetime

from .core import PROGRESS_PATH


def now():
    return datetime.now().isoformat(timespec="seconds")


def load():
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    data.setdefault("version", 1)
    data.setdefault("started_at", now())
    data.setdefault("exercises", {})
    data.setdefault("checkpoints", {})
    data.setdefault("history", [])
    return data


def save(data):
    tmp = PROGRESS_PATH.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(PROGRESS_PATH)


def entry(data, key):
    return data["exercises"].setdefault(key, {
        "status": "not_started", "attempts": 0, "hints_revealed": 0,
        "solution_viewed": False, "first_attempt_at": None, "completed_at": None,
    })


def log(data, event, key=None, **extra):
    rec = {"at": now(), "event": event}
    if key:
        rec["exercise"] = key
    rec.update(extra)
    data["history"].append(rec)
    data["history"] = data["history"][-500:]


def is_complete(data, key):
    return data["exercises"].get(key, {}).get("status") == "completed"
