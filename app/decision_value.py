from typing import Dict, Optional


def calculate_value(
    real_outcome: Dict, brain_decision: Dict, shadow_log: Dict = None
) -> Dict:
    actual_score = real_outcome.get("actual_score", 0.5)
    real_result = real_outcome.get("result", "")

    brain_confidence = (
        brain_decision.get("confidence", 0.5)
        if isinstance(brain_decision, dict)
        else 0.5
    )
    brain_strategy = (
        brain_decision.get("decision", "") if isinstance(brain_decision, dict) else ""
    )
    brain_actions = (
        brain_decision.get("actions", []) if isinstance(brain_decision, dict) else []
    )

    if shadow_log:
        comparison = shadow_log.get("comparison", {})
        evaluation = shadow_log.get("evaluation", {})
    else:
        comparison = {}
        evaluation = {}

    same_strategy = comparison.get("same_strategy", False)
    action_overlap = comparison.get("action_overlap", 0)
    verdict = evaluation.get("verdict", "未知")

    if real_result in ["success", "positive", "good"]:
        actual_score = max(actual_score, 0.6)
    elif real_result in ["failure", "negative", "bad"]:
        actual_score = min(actual_score, 0.4)

    if same_strategy:
        predicted_score = 0.7
    elif action_overlap > 0:
        predicted_score = 0.5 + (action_overlap * 0.05)
    else:
        predicted_score = 0.4

    delta_score = predicted_score - actual_score

    if actual_score >= 0.7:
        verdict_label = "excellent"
        value_category = "high_positive"
    elif actual_score >= 0.5:
        verdict_label = "good"
        value_category = "positive"
    elif actual_score >= 0.3:
        verdict_label = "neutral"
        value_category = "neutral"
    else:
        verdict_label = "poor"
        value_category = "negative"

    if verdict_label == "excellent" or verdict_label == "good":
        brain_better = same_strategy or action_overlap >= 2
    else:
        brain_better = not same_strategy and action_overlap == 0

    quality_score = actual_score
    if same_strategy:
        quality_score += 0.1
    if action_overlap >= 2:
        quality_score += 0.1
    quality_score = min(quality_score, 1.0)

    return {
        "delta_score": round(delta_score, 4),
        "actual_score": round(actual_score, 4),
        "predicted_score": round(predicted_score, 4),
        "brain_better": brain_better,
        "verdict": verdict_label,
        "value_category": value_category,
        "quality_score": round(quality_score, 4),
        "metrics": {
            "same_strategy": same_strategy,
            "action_overlap": action_overlap,
            "brain_confidence": brain_confidence,
        },
    }


def calculate_decision_roi(
    value_result: Dict, base_revenue: float = 10000, period_days: int = 1
) -> Dict:
    delta_score = value_result.get("delta_score", 0)
    actual_score = value_result.get("actual_score", 0.5)
    quality_score = value_result.get("quality_score", 0.5)

    if delta_score > 0:
        roi_multiplier = 1 + delta_score
    else:
        roi_multiplier = 1 + (delta_score * 0.5)

    revenue_impact = base_revenue * roi_multiplier - base_revenue

    profit_margin = 0.35
    profit_impact = revenue_impact * profit_margin

    cost_per_decision = 0.5
    net_value = profit_impact - cost_per_decision

    annualized_gain = net_value * (365 / period_days) if period_days > 0 else net_value

    return {
        "revenue_impact": round(revenue_impact, 2),
        "profit_impact": round(profit_impact, 2),
        "cost_per_decision": cost_per_decision,
        "net_value": round(net_value, 2),
        "annualized_gain": round(annualized_gain, 2),
        "roi_percentage": round(
            (net_value / cost_per_decision * 100) if cost_per_decision > 0 else 0, 2
        ),
        "quality_adjusted": quality_score > 0.6,
    }


def estimate_brain_value_per_month(
    shadow_stats: Dict, avg_revenue_per_decision: float = 10000
) -> Dict:
    total_runs = shadow_stats.get("total_runs", 0)
    brain_win_rate = shadow_stats.get("brain_win_rate", 0)

    if total_runs == 0:
        return {
            "monthly_decisions": 0,
            "estimated_wins": 0,
            "estimated_gain": 0,
            "recommendation": "需要更多数据",
        }

    decisions_per_month = max(total_runs, 30)

    estimated_wins = int(decisions_per_month * brain_win_rate)
    estimated_losses = decisions_per_month - estimated_wins

    avg_win_value = avg_revenue_per_decision * 0.1
    avg_loss_value = avg_revenue_per_decision * 0.05

    estimated_gain = (estimated_wins * avg_win_value) - (
        estimated_losses * avg_loss_value
    )

    roi = (
        (estimated_gain / (decisions_per_month * 0.5)) * 100
        if decisions_per_month > 0
        else 0
    )

    if estimated_gain > 50000:
        recommendation = "强烈推荐接入"
    elif estimated_gain > 10000:
        recommendation = "推荐接入"
    elif estimated_gain > 0:
        recommendation = "可以接入，需持续优化"
    else:
        recommendation = "暂不推荐，需大幅改进"

    return {
        "monthly_decisions": decisions_per_month,
        "estimated_wins": estimated_wins,
        "estimated_losses": estimated_losses,
        "estimated_gain": round(estimated_gain, 2),
        "roi_percentage": round(roi, 2),
        "recommendation": recommendation,
        "confidence": min(1.0, total_runs / 50),
    }
