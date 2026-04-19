import os
import json
from typing import Dict, Any, Optional

STATE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "goal_state.json"
)


def _load_state() -> Dict[str, Any]:
    if not os.path.exists(STATE_FILE):
        return {"adjustments": 0, "last_metrics": {}, "current_goal": {}}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"adjustments": 0, "last_metrics": {}, "current_goal": {}}


def _save_state(state: Dict[str, Any]):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def adjust_goal(
    current_metrics: Dict[str, float] = None,
    recent_evals: list = None,
) -> Optional[Dict[str, float]]:
    from app.goal_engine import GOAL

    current_goal = {
        "revenue_weight": GOAL["revenue_weight"],
        "profit_weight": GOAL["profit_weight"],
        "turnover_weight": GOAL["turnover_weight"],
    }

    state = _load_state()
    adjustments = 0

    if recent_evals and len(recent_evals) >= 3:
        recent_evals = recent_evals[-10:]
        avg_score = sum(e.get("score", 0) for e in recent_evals) / len(recent_evals)

        if avg_score < 0.35:
            current_goal["profit_weight"] = 0.5
            current_goal["revenue_weight"] = 0.3
            current_goal["turnover_weight"] = 0.2
            adjustments += 1

    if current_metrics:
        revenue = current_metrics.get("revenue", 15000)
        target_revenue = current_metrics.get("target_revenue", 15000)

        if revenue < target_revenue * 0.7:
            current_goal["revenue_weight"] = 0.5
            current_goal["profit_weight"] = 0.3
            current_goal["turnover_weight"] = 0.2
            adjustments += 1

        if revenue > target_revenue * 1.2:
            current_goal["revenue_weight"] = 0.2
            current_goal["profit_weight"] = 0.6
            current_goal["turnover_weight"] = 0.2
            adjustments += 1

    if adjustments == 0:
        current_goal = {
            "revenue_weight": 0.4,
            "profit_weight": 0.4,
            "turnover_weight": 0.2,
        }

    changed = False
    for k, v in current_goal.items():
        if GOAL.get(k, 0) != v:
            changed = True
            break

    if changed:
        from app.goal_engine import update_goal

        update_goal(current_goal)
        state["adjustments"] = state.get("adjustments", 0) + 1
        state["current_goal"] = current_goal
        state["last_metrics"] = current_metrics or {}
        _save_state(state)
        return current_goal

    return None


def get_goal_adjustment_status() -> Dict[str, Any]:
    state = _load_state()
    from app.goal_engine import get_current_goal

    current = get_current_goal()
    return {
        "total_adjustments": state.get("adjustments", 0),
        "current_goal": current,
        "last_metrics": state.get("last_metrics", {}),
        "default_goal": {
            "revenue_weight": 0.4,
            "profit_weight": 0.4,
            "turnover_weight": 0.2,
        },
        "is_adjusted": current
        != {
            "revenue_weight": 0.4,
            "profit_weight": 0.4,
            "turnover_weight": 0.2,
            "risk_penalty": 0.2,
        },
    }
