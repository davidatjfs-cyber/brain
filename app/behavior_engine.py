def enforce_strategy(decision, constraints):
    original_confidence = decision.confidence
    must_use = constraints.get("must_use", [])
    must_avoid = constraints.get("must_avoid", [])

    used_good = []
    used_bad = []

    decision_text = decision.decision or ""

    for good in must_use:
        if good and good[:30] in decision_text:
            decision.confidence += 0.1
            used_good.append(good[:50])

    for bad in must_avoid:
        if bad and bad[:30] in decision_text:
            decision.confidence -= 0.2
            used_bad.append(bad[:50])

    decision.confidence = max(0.0, min(1.0, decision.confidence))

    adjustments = []
    if used_good:
        adjustments.append(f"复用高分策略(+0.1×{len(used_good)})")
    if used_bad:
        adjustments.append(f"触发低分策略(-0.2×{len(used_bad)})")

    adjustment_note = "; ".join(adjustments) if adjustments else "无策略调整"

    if decision.reasoning:
        decision.reasoning = f"[策略强化] {adjustment_note}。{decision.reasoning}"

    return {
        "original_confidence": original_confidence,
        "adjusted_confidence": decision.confidence,
        "adjustment": adjustment_note,
        "used_good": used_good,
        "used_bad": used_bad,
    }
