from typing import Dict, Any
from app.goal_config import GOAL


def compute_goal_score(outcome: Dict[str, float], decision: Dict[str, Any]) -> float:
    from app.parameter_store import load_params

    params = load_params()

    score = (
        outcome.get("revenue_change", 0) * GOAL["revenue_weight"]
        + outcome.get("profit_change", 0) * GOAL["profit_weight"]
        + outcome.get("turnover_change", 0) * GOAL["turnover_weight"]
    )

    if decision.get("risk_level") == "high":
        score -= params.get("risk_penalty", GOAL["risk_penalty"])

    return round(max(score, 0.0), 4)


def get_current_goal() -> Dict[str, float]:
    from app.parameter_store import load_params

    params = load_params()
    return {
        "revenue_weight": GOAL["revenue_weight"],
        "profit_weight": GOAL["profit_weight"],
        "turnover_weight": GOAL["turnover_weight"],
        "risk_penalty": params.get("risk_penalty", GOAL["risk_penalty"]),
    }


def reset_goal():
    from app.goal_config import DEFAULT_GOAL

    GOAL.update(DEFAULT_GOAL)


def update_goal(new_weights: Dict[str, float]):
    for key in ["revenue_weight", "profit_weight", "turnover_weight", "risk_penalty"]:
        if key in new_weights:
            GOAL[key] = new_weights[key]
