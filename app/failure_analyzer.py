def analyze_failure(
    real_decision: dict, brain_decision: dict, outcome: dict = None
) -> dict:
    reasons = []
    details = {}

    real_strategy = _get_strategy(real_decision)
    brain_strategy = _get_strategy(brain_decision)

    if not _strategies_match(real_strategy, brain_strategy):
        reasons.append("strategy_mismatch")
        details["strategy_mismatch"] = {
            "real": real_strategy[:50] if real_strategy else "",
            "brain": brain_strategy[:50] if brain_strategy else "",
            "similarity": _calc_text_similarity(real_strategy, brain_strategy),
        }

    brain_risk = _get_risk(brain_decision)
    real_risk = _get_risk(real_decision)
    if brain_risk == "high" and real_risk in ["low", "medium"]:
        reasons.append("too_risky")
        details["too_risky"] = {
            "brain_risk": brain_risk,
            "real_risk": real_risk,
        }

    if brain_risk == "low" and real_risk in ["medium", "high"]:
        reasons.append("too_conservative")
        details["too_conservative"] = {
            "brain_risk": brain_risk,
            "real_risk": real_risk,
        }

    real_actions = _get_actions(real_decision)
    brain_actions = _get_actions(brain_decision)

    if len(brain_actions) < len(real_actions) - 1:
        reasons.append("insufficient_actions")
        details["insufficient_actions"] = {
            "brain_count": len(brain_actions),
            "real_count": len(real_actions),
            "gap": len(real_actions) - len(brain_actions),
        }
    elif len(brain_actions) > len(real_actions) + 2:
        reasons.append("too_many_actions")
        details["too_many_actions"] = {
            "brain_count": len(brain_actions),
            "real_count": len(real_actions),
        }

    if outcome:
        predicted_score = outcome.get("predicted_score", 0.5)
        actual_score = outcome.get("actual_score", 0.5)
        score_error = abs(predicted_score - actual_score)

        if score_error > 0.3:
            reasons.append("bad_prediction")
            details["bad_prediction"] = {
                "predicted": predicted_score,
                "actual": actual_score,
                "error": score_error,
            }

        revenue_error = abs(outcome.get("revenue_error", 0))
        if revenue_error > 0.25:
            reasons.append("revenue_prediction_error")
            details["revenue_prediction_error"] = {
                "error": revenue_error,
            }

        profit_error = abs(outcome.get("profit_error", 0))
        if profit_error > 0.25:
            reasons.append("profit_prediction_error")
            details["profit_prediction_error"] = {
                "error": profit_error,
            }

    action_overlap = (
        len(set(real_actions) & set(brain_actions))
        if real_actions and brain_actions
        else 0
    )
    if action_overlap == 0 and len(real_actions) > 0:
        reasons.append("no_action_overlap")
        details["no_action_overlap"] = {
            "real_actions": real_actions[:3],
            "brain_actions": brain_actions[:3],
        }

    if real_actions and brain_actions:
        overlap_ratio = action_overlap / max(len(real_actions), len(brain_actions))
        if overlap_ratio < 0.3:
            reasons.append("low_action_overlap")
            details["low_action_overlap"] = {
                "overlap": action_overlap,
                "overlap_ratio": overlap_ratio,
            }

    confidence = _get_confidence(brain_decision)
    if confidence and confidence < 0.5:
        reasons.append("low_confidence")
        details["low_confidence"] = {
            "confidence": confidence,
        }

    return {
        "reasons": reasons,
        "details": details,
        "failure_score": _calculate_failure_score(reasons),
        "summary": _generate_summary(reasons, details),
    }


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


def _strategies_match(real: str, brain: str) -> bool:
    if not real or not brain:
        return False
    similarity = _calc_text_similarity(real, brain)
    return similarity > 0.4


def _calc_text_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    a_lower = a.lower()
    b_lower = b.lower()
    if a_lower == b_lower:
        return 1.0
    words_a = set(a_lower.split())
    words_b = set(b_lower.split())
    if not words_a or not words_b:
        return 0.0
    intersection = len(words_a & words_b)
    union = len(words_a | words_b)
    return intersection / union if union > 0 else 0.0


def _calculate_failure_score(reasons: list) -> float:
    weight_map = {
        "strategy_mismatch": 0.3,
        "too_risky": 0.15,
        "too_conservative": 0.1,
        "insufficient_actions": 0.1,
        "too_many_actions": 0.05,
        "bad_prediction": 0.2,
        "revenue_prediction_error": 0.1,
        "profit_prediction_error": 0.1,
        "no_action_overlap": 0.15,
        "low_action_overlap": 0.1,
        "low_confidence": 0.05,
    }
    return sum(weight_map.get(r, 0.05) for r in reasons)


def _generate_summary(reasons: list, details: dict) -> str:
    if not reasons:
        return "未知原因"

    summary_parts = []
    reason_labels = {
        "strategy_mismatch": "策略方向不匹配",
        "too_risky": "风险评估过于激进",
        "too_conservative": "风险评估过于保守",
        "insufficient_actions": "行动方案不足",
        "too_many_actions": "行动方案过多",
        "bad_prediction": "预测准确性差",
        "revenue_prediction_error": "营收预测偏差大",
        "profit_prediction_error": "利润预测偏差大",
        "no_action_overlap": "行动完全无重叠",
        "low_action_overlap": "行动重叠度低",
        "low_confidence": "决策置信度低",
    }

    for reason in reasons[:3]:
        label = reason_labels.get(reason, reason)
        summary_parts.append(label)

    return " | ".join(summary_parts) if summary_parts else "多种因素"
