import json
import os
import time
from typing import Dict, List, Optional

PATH = "data/trend_logs.json"


def init_trend_logs():
    os.makedirs("data", exist_ok=True)
    try:
        with open(PATH, "r") as f:
            json.load(f)
    except:
        with open(PATH, "w") as f:
            json.dump([], f)


def record_trend(param_name: str, value: float, reason: str = "", change: float = 0.0):
    init_trend_logs()

    try:
        with open(PATH, "r") as f:
            data = json.load(f)
    except:
        data = []

    entry = {
        "param": param_name,
        "value": round(value, 6),
        "change": round(change, 6),
        "reason": reason,
        "timestamp": time.time(),
    }

    data.append(entry)

    with open(PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_param_history(param_name: str, limit: int = 20) -> List[Dict]:
    init_trend_logs()
    try:
        with open(PATH, "r") as f:
            data = json.load(f)
        return [e for e in data if e.get("param") == param_name][-limit:]
    except:
        return []


def get_recent_changes(param_name: str, limit: int = 10) -> List[float]:
    history = get_param_history(param_name, limit)
    return [e.get("change", 0) for e in history if e.get("change", 0) != 0]


def analyze_trend(param_name: str) -> Dict:
    history = get_param_history(param_name, limit=20)

    if len(history) < 2:
        return {
            "trend": "unknown",
            "direction": None,
            "stability": 1.0,
            "suggestion": "insufficient_data",
        }

    values = [e.get("value", 0) for e in history]

    first_half = values[: len(values) // 2]
    second_half = values[len(values) // 2 :]

    avg_first = sum(first_half) / len(first_half) if first_half else 0
    avg_second = sum(second_half) / len(second_half) if second_half else 0

    direction = (
        "increasing"
        if avg_second > avg_first + 0.02
        else "decreasing"
        if avg_second < avg_first - 0.02
        else "stable"
    )

    changes = [e.get("change", 0) for e in history]
    non_zero_changes = [c for c in changes if abs(c) > 0.001]

    if len(non_zero_changes) < 2:
        stability = 1.0
    else:
        oscillating = sum(
            1
            for i in range(len(non_zero_changes) - 1)
            if non_zero_changes[i] * non_zero_changes[i + 1] < 0
        )
        stability = 1.0 - (oscillating / max(1, len(non_zero_changes) - 1))

    if direction == "stable" and stability > 0.8:
        suggestion = "converged"
    elif stability < 0.5:
        suggestion = "oscillating"
    elif abs(values[-1] - values[0]) > 0.3:
        suggestion = "still_adjusting"
    else:
        suggestion = "near_optimal"

    return {
        "trend": direction,
        "direction": direction,
        "stability": round(stability, 3),
        "suggestion": suggestion,
        "current_value": values[-1] if values else None,
        "first_avg": round(avg_first, 4),
        "second_avg": round(avg_second, 4),
        "change_count": len(non_zero_changes),
    }


def get_all_trends() -> Dict[str, Dict]:
    all_params = [
        "risk_penalty",
        "revenue_factor",
        "profit_factor",
        "turnover_factor",
        "explore_rate",
        "confidence_threshold",
        "pattern_match_threshold",
    ]

    return {param: analyze_trend(param) for param in all_params}


def is_converged(param_name: str, threshold: float = 0.05) -> bool:
    analysis = analyze_trend(param_name)
    return analysis["stability"] > (1 - threshold) and analysis["trend"] in [
        "stable",
        "converged",
    ]


def is_oscillating(param_name: str) -> bool:
    analysis = analyze_trend(param_name)
    return analysis["stability"] < 0.5


def get_convergence_status() -> Dict:
    trends = get_all_trends()

    converged = [p for p, a in trends.items() if a.get("suggestion") == "converged"]
    oscillating = [p for p, a in trends.items() if a.get("suggestion") == "oscillating"]
    adjusting = [
        p for p, a in trends.items() if a.get("suggestion") == "still_adjusting"
    ]

    overall_stability = (
        sum(a.get("stability", 0) for a in trends.values()) / len(trends)
        if trends
        else 0
    )

    return {
        "converged_params": converged,
        "oscillating_params": oscillating,
        "adjusting_params": adjusting,
        "overall_stability": round(overall_stability, 3),
        "is_stable": overall_stability > 0.7 and len(oscillating) == 0,
    }


def clear_trend_logs():
    with open(PATH, "w") as f:
        json.dump([], f)
