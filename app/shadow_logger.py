import json
import time
import os

PATH = "data/shadow_logs.json"


def log_shadow(data: dict) -> str:
    os.makedirs("data", exist_ok=True)

    try:
        with open(PATH, "r") as f:
            logs = json.load(f)
    except:
        logs = []

    data["timestamp"] = time.time()
    data["log_id"] = f"shadow_{len(logs) + 1}"
    logs.append(data)

    with open(PATH, "w") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

    return data["log_id"]


def get_shadow_logs(limit: int = 50) -> list:
    try:
        with open(PATH, "r") as f:
            logs = json.load(f)
        return logs[-limit:] if limit > 0 else logs
    except:
        return []


def get_shadow_by_id(log_id: str) -> dict:
    logs = get_shadow_logs(limit=0)
    for log in logs:
        if log.get("log_id") == log_id:
            return log
    return None


def get_shadow_stats() -> dict:
    logs = get_shadow_logs(limit=0)

    if not logs:
        return {
            "total_runs": 0,
            "same_strategy_count": 0,
            "same_strategy_rate": 0.0,
            "avg_brain_confidence": 0.0,
            "avg_action_overlap": 0.0,
            "convergence_trend": "no_data",
        }

    same_count = sum(
        1 for log in logs if log.get("comparison", {}).get("same_strategy", False)
    )
    confidences = [log.get("comparison", {}).get("brain_confidence", 0) for log in logs]
    overlaps = [log.get("comparison", {}).get("action_overlap", 0) for log in logs]

    recent_10 = logs[-10:] if len(logs) >= 10 else logs
    older_10 = logs[:10] if len(logs) >= 10 else logs

    recent_same_rate = sum(
        1 for log in recent_10 if log.get("comparison", {}).get("same_strategy", False)
    ) / len(recent_10)
    older_same_rate = (
        sum(
            1
            for log in older_10
            if log.get("comparison", {}).get("same_strategy", False)
        )
        / len(older_10)
        if older_10
        else 0
    )

    if recent_same_rate > older_same_rate + 0.1:
        trend = "converging"
    elif recent_same_rate < older_same_rate - 0.1:
        trend = "diverging"
    else:
        trend = "stable"

    return {
        "total_runs": len(logs),
        "same_strategy_count": same_count,
        "same_strategy_rate": same_count / len(logs),
        "avg_brain_confidence": sum(confidences) / len(confidences)
        if confidences
        else 0,
        "avg_action_overlap": sum(overlaps) / len(overlaps) if overlaps else 0,
        "convergence_trend": trend,
        "recent_same_rate": recent_same_rate,
        "older_same_rate": older_same_rate,
    }


def update_shadow_outcome(log_id: str, outcome: dict) -> bool:
    logs = get_shadow_logs(limit=0)
    for log in logs:
        if log.get("log_id") == log_id:
            log["real_outcome"] = outcome
            with open(PATH, "w") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            return True
    return False
