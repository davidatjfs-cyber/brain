from typing import Dict, Any, List, Optional
from app.simulator import simulate, simulate_multiple


def select_best_strategy(
    candidates: List[Dict[str, Any]],
    input_data: Dict[str, Any],
    top_k: int = 3,
) -> Dict[str, Any]:
    if not candidates:
        return {}

    simulated = simulate_multiple(candidates, input_data)
    simulated.sort(key=lambda x: x.get("simulated_score", -999), reverse=True)

    best = simulated[0] if simulated else {}

    return {
        "best": best,
        "candidates": simulated[:top_k],
        "all": simulated,
    }


def get_strategy_ranking(
    candidates: List[Dict[str, Any]],
    input_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    if not candidates:
        return []

    simulated = simulate_multiple(candidates, input_data)
    simulated.sort(key=lambda x: x.get("simulated_score", -999), reverse=True)

    for i, s in enumerate(simulated):
        s["rank"] = i + 1

    return simulated


def explain_selection(
    best: Dict[str, Any],
    runner_up: Optional[Dict[str, Any]] = None,
) -> str:
    if not best:
        return "无可用策略"

    outcome = best.get("simulated_outcome", {})
    score = best.get("simulated_score", 0)

    parts = []
    if outcome.get("revenue_change", 0) > 0:
        parts.append(f"营收↑{outcome['revenue_change']:.2f}")
    if outcome.get("turnover_change", 0) > 0:
        parts.append(f"翻台↑{outcome['turnover_change']:.2f}")
    if outcome.get("profit_change", 0) > 0:
        parts.append(f"毛利↑{outcome['profit_change']:.2f}")

    impact_str = " | ".join(parts) if parts else "无明显变化"

    reason = f"综合评分{score:.4f}，预期效果：{impact_str}"

    if runner_up and runner_up.get("simulated_score", 0) > 0:
        gap = score - runner_up["simulated_score"]
        if gap > 0.01:
            reason += f"，领先次优策略{gap:.4f}分"

    return reason
