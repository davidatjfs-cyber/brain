from typing import Dict, List, Optional
from app.learning_rate_manager import (
    get_adaptive_rate,
    should_adjust,
)
from app.trend_analyzer import record_trend, get_recent_changes

DIRECTION_MEMORY: Dict[str, List[int]] = {}


def stabilize(
    params: Dict, param_name: str, proposed_change: float, reason: str = ""
) -> Dict:
    current_value = params.get(param_name, 0)

    should_fix, clamped_change = should_adjust(
        param_name, current_value, proposed_change
    )

    if not should_fix:
        return {
            "applied": False,
            "reason": "boundary_limit",
            "params": params,
            "change": 0,
        }

    recent_changes = get_recent_changes(param_name)
    adaptive_rate = get_adaptive_rate(param_name, current_value, recent_changes)

    change = clamped_change * adaptive_rate

    prev_direction = (
        DIRECTION_MEMORY.get(param_name, [0])[-1]
        if param_name in DIRECTION_MEMORY
        else 0
    )
    current_direction = 1 if change > 0.001 else (-1 if change < -0.001 else 0)

    if (
        prev_direction != 0
        and current_direction != 0
        and prev_direction != current_direction
    ):
        change *= 0.3
        reason = f"{reason} (oscillation_dampened)"

    new_value = current_value + change

    params[param_name] = round(new_value, 6)

    record_trend(param_name, new_value, reason=reason, change=change)

    if param_name not in DIRECTION_MEMORY:
        DIRECTION_MEMORY[param_name] = []
    DIRECTION_MEMORY[param_name].append(current_direction)
    if len(DIRECTION_MEMORY[param_name]) > 10:
        DIRECTION_MEMORY[param_name] = DIRECTION_MEMORY[param_name][-10:]

    return {
        "applied": True,
        "params": params,
        "change": round(change, 6),
        "adaptive_rate": round(adaptive_rate, 4),
        "reason": reason,
        "prev_direction": prev_direction,
        "new_direction": current_direction,
    }


def stabilize_batch(params: Dict, fixes: List[Dict]) -> Dict:
    results = []

    for fix in fixes:
        param_name = fix.get("param")
        proposed_change = fix.get("delta")
        direction = fix.get("direction", "increase")
        reason = fix.get("reason", "")

        if direction == "decrease":
            proposed_change = -abs(proposed_change)

        result = stabilize(params, param_name, proposed_change, reason)
        results.append(
            {
                "param": param_name,
                "result": result,
            }
        )

    return {
        "updated_params": params,
        "fix_results": results,
        "all_applied": all(r["result"]["applied"] for r in results),
    }


def get_stability_report() -> Dict:
    from app.trend_analyzer import get_convergence_status, get_all_trends

    convergence = get_convergence_status()
    trends = get_all_trends()

    oscillating = convergence.get("oscillating_params", [])
    if oscillating:
        suggestions = [f"参数 {p} 存在震荡，建议降低调整幅度" for p in oscillating]
    elif convergence.get("is_stable"):
        suggestions = ["系统已稳定收敛"]
    else:
        suggestions = ["系统仍在调整中"]

    return {
        "convergence": convergence,
        "trends": trends,
        "suggestions": suggestions,
        "is_healthy": convergence.get("is_stable", False),
    }


def reset_direction_memory():
    global DIRECTION_MEMORY
    DIRECTION_MEMORY = {}
