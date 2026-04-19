import os
import json
import time
from typing import Dict, Any, List

LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "debug_logs.json"
)

MAX_LOG_ENTRIES = 500


def _load_logs() -> List[Dict[str, Any]]:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_logs(data: List[Dict[str, Any]]):
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_decision(debug_info: Dict[str, Any]):
    debug_info["timestamp"] = time.time()
    debug_info["_ts"] = time.strftime("%Y-%m-%d %H:%M:%S")

    data = _load_logs()
    data.append(debug_info)

    if len(data) > MAX_LOG_ENTRIES:
        data = data[-MAX_LOG_ENTRIES:]

    _save_logs(data)


def log_evaluation(decision_id: str, score: float, pattern_updates: List[str]):
    data = _load_logs()
    for entry in reversed(data):
        if entry.get("decision_id") == decision_id and entry.get("_type") == "decision":
            entry["_evaluation"] = {
                "score": score,
                "pattern_updates": pattern_updates,
                "evaluated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            break

    _save_logs(data)


def get_logs(limit: int = 50) -> List[Dict[str, Any]]:
    data = _load_logs()
    return data[-limit:]


def get_latest_log() -> Dict[str, Any]:
    data = _load_logs()
    return data[-1] if data else {}


def clear_logs():
    _save_logs([])


def get_decision_log(decision_id: str) -> Dict[str, Any]:
    data = _load_logs()
    for entry in data:
        if entry.get("decision_id") == decision_id:
            return entry
    return {}
