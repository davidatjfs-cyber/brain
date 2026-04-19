from typing import Dict, Optional

PARAM_BOUNDS = {
    "risk_penalty": {"min": 0.0, "max": 1.0, "center": 0.5},
    "revenue_factor": {"min": 0.5, "max": 1.5, "center": 1.0},
    "profit_factor": {"min": 0.5, "max": 1.5, "center": 1.0},
    "turnover_factor": {"min": 0.5, "max": 1.5, "center": 1.0},
    "explore_rate": {"min": 0.05, "max": 0.3, "center": 0.175},
    "confidence_threshold": {"min": 0.5, "max": 0.9, "center": 0.7},
    "pattern_match_threshold": {"min": 0.4, "max": 0.8, "center": 0.6},
}

BASE_LEARNING_RATES = {
    "risk_penalty": 0.1,
    "revenue_factor": 0.05,
    "profit_factor": 0.05,
    "turnover_factor": 0.05,
    "explore_rate": 0.15,
    "confidence_threshold": 0.1,
    "pattern_match_threshold": 0.15,
}


def get_learning_rate(param_name: str, current_value: float) -> float:
    if param_name not in BASE_LEARNING_RATES:
        return 0.05

    base_rate = BASE_LEARNING_RATES[param_name]

    if param_name not in PARAM_BOUNDS:
        return base_rate

    bounds = PARAM_BOUNDS[param_name]
    min_val = bounds["min"]
    max_val = bounds["max"]
    center = bounds["center"]

    distance_to_edge = min(
        abs(current_value - min_val) / (center - min_val) if center != min_val else 1,
        abs(current_value - max_val) / (max_val - center) if max_val != center else 1,
    )

    distance_to_edge = max(0.1, min(1.0, distance_to_edge))

    if distance_to_edge < 0.3:
        return base_rate * 0.3
    elif distance_to_edge < 0.5:
        return base_rate * 0.5
    elif distance_to_edge < 0.7:
        return base_rate * 0.75
    else:
        return base_rate


def get_momentum(param_name: str, recent_changes: list) -> float:
    if len(recent_changes) < 2:
        return 1.0

    directions = []
    for change in recent_changes[-5:]:
        if change > 0.001:
            directions.append(1)
        elif change < -0.001:
            directions.append(-1)
        else:
            directions.append(0)

    if len(directions) < 2:
        return 1.0

    oscillating = sum(
        1 for i in range(len(directions) - 1) if directions[i] * directions[i + 1] < 0
    )

    if oscillating >= 2:
        return 0.3
    elif oscillating == 1:
        return 0.5

    return 1.0


def get_adaptive_rate(
    param_name: str, current_value: float, recent_changes: list = None
) -> float:
    base_rate = get_learning_rate(param_name, current_value)

    if recent_changes is None:
        recent_changes = []

    momentum = get_momentum(param_name, recent_changes)

    return base_rate * momentum


def should_adjust(
    param_name: str, current_value: float, proposed_change: float
) -> tuple:
    if param_name not in PARAM_BOUNDS:
        return True, proposed_change

    bounds = PARAM_BOUNDS[param_name]
    min_val = bounds["min"]
    max_val = bounds["max"]

    new_value = current_value + proposed_change

    if new_value < min_val:
        return False, min_val - current_value
    elif new_value > max_val:
        return False, max_val - current_value

    return True, proposed_change
