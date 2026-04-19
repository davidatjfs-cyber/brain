import os
import json
import random
import time
from typing import Dict, Any, Tuple

STATE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "exploration_state.json"
)


def _load_state() -> Dict[str, Any]:
    if not os.path.exists(STATE_FILE):
        return {
            "explore_count": 0,
            "total_decisions": 0,
            "exploration_rate": 0.15,
            "last_exploration_time": None,
        }
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "explore_count": 0,
            "total_decisions": 0,
            "exploration_rate": 0.15,
            "last_exploration_time": None,
        }


def _save_state(state: Dict[str, Any]):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def should_explore(explore_rate: float = None) -> Tuple[bool, str]:
    from app.parameter_store import load_params

    state = _load_state()
    params = load_params()

    if explore_rate is None:
        explore_rate = params.get("explore_rate", state["exploration_rate"])

    state["total_decisions"] += 1

    triggered = random.random() < explore_rate

    if triggered:
        state["explore_count"] += 1
        state["last_exploration_time"] = time.strftime("%Y-%m-%d %H:%M:%S")

    _save_state(state)
    reason = (
        f"探索触发 (rate={explore_rate:.2f})"
        if triggered
        else f"复用模式 (rate={explore_rate:.2f})"
    )
    return triggered, reason


def get_exploration_stats() -> Dict[str, Any]:
    from app.parameter_store import load_params

    state = _load_state()
    params = load_params()
    total = state["total_decisions"]
    explore = state["explore_count"]
    rate = params.get("explore_rate", state["exploration_rate"])

    if total == 0:
        explore_rate_actual = 0
    else:
        explore_rate_actual = explore / total

    return {
        "total_decisions": total,
        "exploration_count": explore,
        "reuse_count": total - explore,
        "target_rate": rate,
        "actual_rate": round(explore_rate_actual, 4),
        "last_exploration": state.get("last_exploration_time"),
        "from_params": True,
    }


def adjust_exploration_rate(performance: float) -> float:
    state = _load_state()
    current = state["exploration_rate"]

    if performance > 0.65:
        new_rate = max(0.05, current - 0.02)
    elif performance < 0.40:
        new_rate = min(0.30, current + 0.02)
    else:
        new_rate = current

    state["exploration_rate"] = new_rate
    _save_state(state)
    return new_rate


def reset_exploration_state():
    _save_state(
        {
            "explore_count": 0,
            "total_decisions": 0,
            "exploration_rate": 0.15,
            "last_exploration_time": None,
        }
    )
