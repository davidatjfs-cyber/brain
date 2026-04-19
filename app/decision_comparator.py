def compare_decisions(real: dict, brain: dict) -> dict:
    real_decision = (
        real.get("decision", real) if isinstance(real.get("decision"), str) else real
    )
    brain_decision = (
        brain.get("decision", brain)
        if isinstance(brain.get("decision"), dict)
        else brain
    )

    real_actions = (
        real_decision.get("actions", [])
        if isinstance(real_decision, dict)
        else real.get("actions", [])
    )
    brain_actions = (
        brain_decision.get("actions", []) if isinstance(brain_decision, dict) else []
    )

    real_strategy = (
        real_decision
        if isinstance(real_decision, str)
        else real_decision.get("decision", "") or real_decision.get("strategy", "")
    )
    brain_strategy = (
        brain_decision.get("decision", "")
        if isinstance(brain_decision, dict)
        else (brain_decision if isinstance(brain_decision, str) else "")
    )

    same_strategy = (
        real_strategy
        and brain_strategy
        and (
            real_strategy.strip().lower() == brain_strategy.strip().lower()
            or any(
                word in brain_strategy.lower()
                for word in real_strategy.lower().split()
                if len(word) > 3
            )
        )
    )

    action_overlap = (
        len(set(real_actions) & set(brain_actions))
        if real_actions and brain_actions
        else 0
    )
    action_diff = abs(len(brain_actions) - len(real_actions))

    real_risk = (
        real_decision.get("risk_level", "medium")
        if isinstance(real_decision, dict)
        else "medium"
    )
    brain_risk = (
        brain_decision.get("risk_level", "medium")
        if isinstance(brain_decision, dict)
        else "medium"
    )
    risk_match = real_risk == brain_risk

    brain_confidence = (
        brain_decision.get("confidence", 0.5)
        if isinstance(brain_decision, dict)
        else 0.5
    )

    real_expected = (
        real_decision.get("expected_impact", "")
        if isinstance(real_decision, dict)
        else ""
    )
    brain_expected = (
        brain_decision.get("expected_impact", "")
        if isinstance(brain_decision, dict)
        else ""
    )
    impact_similarity = (
        0.5
        if not real_expected or not brain_expected
        else (
            1.0
            if real_expected == brain_expected
            else 0.8
            if any(
                word in brain_expected.lower()
                for word in real_expected.lower().split()
                if len(word) > 4
            )
            else 0.3
        )
    )

    return {
        "same_strategy": same_strategy,
        "strategy_similarity": _calc_similarity(real_strategy, brain_strategy),
        "action_overlap": action_overlap,
        "action_count_diff": action_diff,
        "risk_match": risk_match,
        "brain_confidence": brain_confidence,
        "real_risk": real_risk,
        "brain_risk": brain_risk,
        "impact_similarity": impact_similarity,
        "real_vs_brain_diff": len(brain_actions) - len(real_actions),
    }


def _calc_similarity(a: str, b: str) -> float:
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


def evaluate_brain_value(comparison: dict, real_outcome: dict = None) -> dict:
    score = 0.0
    reasons = []

    same_strategy = comparison.get("same_strategy", False)
    action_overlap = comparison.get("action_overlap", 0)
    risk_match = comparison.get("risk_match", False)
    impact_similarity = comparison.get("impact_similarity", 0.5)
    brain_confidence = comparison.get("brain_confidence", 0.5)

    if same_strategy:
        score += 0.3
        reasons.append("策略一致")
    else:
        reasons.append("策略不同")

    if action_overlap > 0:
        score += 0.2 * min(action_overlap, 3)
        reasons.append(f"行动重叠: {action_overlap}项")

    if risk_match:
        score += 0.15
        reasons.append("风险等级匹配")

    if impact_similarity > 0.6:
        score += 0.2
        reasons.append("预期影响相似")

    if brain_confidence >= 0.7 and same_strategy:
        score += 0.15
        reasons.append("高置信度 + 策略一致")

    if real_outcome:
        actual_result = real_outcome.get("result", "")
        if actual_result in ["success", "positive", "good"]:
            score += 0.2
            reasons.append("实际结果正向")
        elif actual_result in ["failure", "negative", "bad"]:
            if same_strategy:
                reasons.append("实际失败但Brain策略与人一致")
        score += real_outcome.get("actual_score", 0) * 0.2

    verdict = (
        "优秀"
        if score >= 0.7
        else "良好"
        if score >= 0.5
        else "一般"
        if score >= 0.3
        else "待改进"
    )

    return {
        "score": min(1.0, score),
        "verdict": verdict,
        "reasons": reasons,
        "brain_better_than_human": score >= 0.6 and not comparison["same_strategy"],
    }
