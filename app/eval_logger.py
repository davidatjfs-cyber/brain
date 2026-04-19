import os
import json
import time
from typing import Dict, Any, List

PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "eval_logs.json"
)


def _load() -> List[Dict[str, Any]]:
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    try:
        with open(PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save(data: List[Dict[str, Any]]):
    with open(PATH, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def log_eval(
    decision_id: str, score: float, meta: Dict[str, Any] = None
) -> Dict[str, Any]:
    entry = {
        "decision_id": decision_id,
        "score": score,
        "timestamp": time.time(),
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if meta:
        entry["meta"] = meta

    data = _load()
    data.append(entry)

    if len(data) > 1000:
        data = data[-1000:]

    _save(data)
    return entry


def get_eval_history(limit: int = 100) -> List[Dict[str, Any]]:
    data = _load()
    return data[-limit:]


def get_avg_score(window: int = 20) -> float:
    data = _load()
    if not data:
        return 0.0
    recent = data[-window:]
    return round(sum(e["score"] for e in recent) / len(recent), 4)


def get_score_trend(window: int = 20) -> Dict[str, Any]:
    data = _load()
    if len(data) < 2:
        return {"trend": "unknown", "change": 0}

    recent = data[-window:] if len(data) >= window else data
    first_half = recent[: len(recent) // 2]
    second_half = recent[len(recent) // 2 :]

    avg_first = (
        sum(e["score"] for e in first_half) / len(first_half) if first_half else 0
    )
    avg_second = (
        sum(e["score"] for e in second_half) / len(second_half) if second_half else 0
    )
    change = avg_second - avg_first

    trend = (
        "improving" if change > 0.05 else ("declining" if change < -0.05 else "stable")
    )
    return {
        "trend": trend,
        "change": round(change, 4),
        "avg_first_half": round(avg_first, 4),
        "avg_second_half": round(avg_second, 4),
        "total_evals": len(data),
    }


def get_pattern_score_history(pattern_id: str) -> List[Dict[str, Any]]:
    from app.pattern_engine import get_all_patterns

    patterns = get_all_patterns()
    for p in patterns:
        if p["id"] == pattern_id:
            return [{"score": p["score"], "usage_count": p.get("usage_count", 0)}]
    return []


def clear_eval_logs():
    _save([])
