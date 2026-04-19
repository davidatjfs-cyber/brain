import json
import os
import time
from typing import Optional

PATH = "data/failure_logs.json"


def init_failure_logs():
    os.makedirs("data", exist_ok=True)
    try:
        with open(PATH, "r") as f:
            json.load(f)
    except:
        with open(PATH, "w") as f:
            json.dump([], f)


def save_failure_pattern(
    shadow_log_id: str,
    reasons: list,
    details: dict,
    failure_score: float,
    summary: str,
    real_decision: dict = None,
    brain_decision: dict = None,
) -> str:
    init_failure_logs()

    try:
        with open(PATH, "r") as f:
            data = json.load(f)
    except:
        data = []

    entry = {
        "shadow_log_id": shadow_log_id,
        "reasons": reasons,
        "details": details,
        "failure_score": failure_score,
        "summary": summary,
        "timestamp": time.time(),
    }

    if real_decision:
        entry["real_decision"] = {
            "strategy": _get_strategy(real_decision),
            "actions": _get_actions(real_decision),
            "risk_level": _get_risk(real_decision),
        }

    if brain_decision:
        entry["brain_decision"] = {
            "strategy": _get_strategy(brain_decision),
            "actions": _get_actions(brain_decision),
            "risk_level": _get_risk(brain_decision),
            "confidence": _get_confidence(brain_decision),
        }

    data.append(entry)

    with open(PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return f"failure_{len(data)}"


def get_failure_logs(limit: int = 50) -> list:
    init_failure_logs()
    try:
        with open(PATH, "r") as f:
            data = json.load(f)
        return data[-limit:] if limit > 0 else data
    except:
        return []


def get_failure_by_id(failure_id: str) -> Optional[dict]:
    logs = get_failure_logs(limit=0)
    for log in logs:
        if log.get("failure_id") == failure_id or f"failure_{len(logs)}" == failure_id:
            return log
    for i, log in enumerate(logs):
        if f"failure_{i + 1}" == failure_id:
            return log
    return None


def get_failure_stats() -> dict:
    logs = get_failure_logs(limit=0)

    if not logs:
        return {
            "total_failures": 0,
            "top_failure_reasons": [],
            "reason_counts": {},
            "avg_failure_score": 0.0,
            "most_common_reason": None,
        }

    reason_counts = {}
    for log in logs:
        for reason in log.get("reasons", []):
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    sorted_reasons = sorted(reason_counts.items(), key=lambda x: -x[1])
    top_reasons = [r[0] for r in sorted_reasons[:5]]

    avg_score = sum(log.get("failure_score", 0) for log in logs) / len(logs)

    recent_logs = logs[-10:] if len(logs) >= 10 else logs
    recent_reason_counts = {}
    for log in recent_logs:
        for reason in log.get("reasons", []):
            recent_reason_counts[reason] = recent_reason_counts.get(reason, 0) + 1

    recent_top = sorted(recent_reason_counts.items(), key=lambda x: -x[1])[:3]
    emerging_reasons = [
        r[0] for r in recent_top if recent_reason_counts.get(r[0], 0) >= 2
    ]

    return {
        "total_failures": len(logs),
        "top_failure_reasons": top_reasons,
        "reason_counts": reason_counts,
        "avg_failure_score": avg_score,
        "most_common_reason": sorted_reasons[0][0] if sorted_reasons else None,
        "recent_trend": emerging_reasons,
    }


def get_failure_patterns_for_reason(reason: str) -> list:
    logs = get_failure_logs(limit=0)
    return [log for log in logs if reason in log.get("reasons", [])]


def clear_failure_logs():
    with open(PATH, "w") as f:
        json.dump([], f)


def _get_strategy(decision: dict) -> str:
    if isinstance(decision, dict):
        return decision.get("decision", "") or decision.get("strategy", "")
    return str(decision) if decision else ""


def _get_actions(decision: dict) -> list:
    if isinstance(decision, dict):
        return decision.get("actions", [])
    return []


def _get_risk(decision: dict) -> str:
    if isinstance(decision, dict):
        return decision.get("risk_level", "medium")
    return "medium"


def _get_confidence(decision: dict) -> float:
    if isinstance(decision, dict):
        return decision.get("confidence", 0.5)
    return 0.5
