from typing import List


def reflect_on_history(recent_decisions: List) -> str:
    if not recent_decisions:
        return "暂无历史决策，请谨慎决策。"

    evaluated = [r for r in recent_decisions if r.evaluation]
    if not evaluated:
        return "历史决策尚无评估，请基于行业知识谨慎决策。"

    sorted_by_score = sorted(evaluated, key=lambda r: r.evaluation.score, reverse=True)

    high_score = sorted_by_score[:2]
    low_score = sorted_by_score[-2:] if len(sorted_by_score) >= 2 else []

    lines = []

    if high_score:
        lines.append("【成功的策略】")
        for r in high_score:
            d = r.decision
            s = r.evaluation.score
            lines.append(f"- {d.decision_type} | score:{s:.2f} | {d.decision[:60]}")

    if low_score:
        lines.append("\n【失败的策略 — 必须避免】")
        for r in low_score:
            d = r.decision
            s = r.evaluation.score
            lines.append(f"- {d.decision_type} | score:{s:.2f} | {d.decision[:60]}")

    successful_types = [
        r.decision.decision_type for r in high_score if r.evaluation.score >= 0.3
    ]
    failed_types = [
        r.decision.decision_type for r in low_score if r.evaluation.score <= -0.1
    ]

    lines.append("\n【策略倾向】")
    if successful_types:
        types = "/".join(set(successful_types))
        lines.append(f"✅ 优先使用: {types}")
    if failed_types:
        types = "/".join(set(failed_types))
        lines.append(f"❌ 尽量避免: {types}")

    return "\n".join(lines)


def self_check(decision) -> dict:
    issues = []
    warnings = []
    improved = None

    if not decision.problem.strip():
        issues.append("problem 为空")
    if not decision.decision.strip():
        issues.append("decision 为空")
    if not decision.actions or len(decision.actions) < 2:
        issues.append("actions 不足2条")

    vague_keywords = [
        "加强管理",
        "注意",
        "关注",
        "做好",
        "优化",
        "提升",
        "改善",
        "强化",
        "改进",
        "提高",
    ]
    if decision.decision:
        for kw in vague_keywords:
            if kw in decision.decision and len(decision.decision) < 30:
                issues.append(f"decision 疑似空话: '{kw}'")
                break

    action_vague = sum(
        1 for a in (decision.actions or []) if any(kw in a for kw in vague_keywords)
    )
    if action_vague == len(decision.actions or []):
        warnings.append("所有动作都是空话，无具体可执行步骤")

    if decision.risk_level == "high" and decision.confidence > 0.8:
        warnings.append("高风险+高置信度组合可疑，建议降低置信度")

    if decision.risk_level == "high" and decision.decision_type == "pricing":
        warnings.append("高风险 + 定价决策，建议增加验证步骤")

    if issues:
        improved = {
            "problem": decision.problem,
            "decision": f"[自检修正] {decision.decision}",
            "actions": decision.actions,
            "confidence": max(0.3, decision.confidence - 0.15),
            "risk_level": "high" if decision.risk_level == "high" else "medium",
        }

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "improved": improved,
    }
