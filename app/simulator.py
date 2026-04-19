from typing import Dict, Any, Tuple
from app.outcome_predictor import predict_outcome
from app.goal_engine import compute_goal_score, get_current_goal


def simulate(
    decision: Dict[str, Any], input_data: Dict[str, Any]
) -> Tuple[float, Dict[str, float]]:
    outcome = predict_outcome(decision, input_data)
    score = compute_goal_score(outcome, decision)
    return score, outcome


def simulate_multiple(
    decisions: list[Dict[str, Any]], input_data: Dict[str, Any]
) -> list[Dict[str, Any]]:
    goal = get_current_goal()
    results = []
    for d in decisions:
        score, outcome = simulate(d, input_data)
        results.append(
            {
                **d,
                "simulated_score": score,
                "simulated_outcome": outcome,
                "goal_weights": goal,
            }
        )
    return results
