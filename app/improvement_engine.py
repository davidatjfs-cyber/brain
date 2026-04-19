from typing import Optional

SUGGESTION_MAP = {
    "strategy_mismatch": {
        "suggestion": "增强 pattern 匹配能力",
        "module": "pattern_matcher.py",
        "action": "调整 pattern 匹配阈值或增加场景特征提取",
        "priority": "high",
    },
    "too_risky": {
        "suggestion": "提高 risk penalty",
        "module": "goal_engine.py",
        "action": "增加高风险决策的惩罚权重",
        "priority": "high",
    },
    "too_conservative": {
        "suggestion": "适度提高风险接受度",
        "module": "strategy_enforcer.py",
        "action": "降低保守策略的优先级",
        "priority": "medium",
    },
    "insufficient_actions": {
        "suggestion": "增加 action 生成能力",
        "module": "brain_core.py",
        "action": "要求 LLM 生成更多具体行动方案",
        "priority": "medium",
    },
    "too_many_actions": {
        "suggestion": "精简 action 生成",
        "module": "brain_core.py",
        "action": "限制行动方案数量在合理范围",
        "priority": "low",
    },
    "bad_prediction": {
        "suggestion": "优化 outcome predictor",
        "module": "outcome_predictor.py",
        "action": "调整预测模型参数或增加训练数据",
        "priority": "high",
    },
    "revenue_prediction_error": {
        "suggestion": "优化营收预测准确性",
        "module": "outcome_predictor.py",
        "action": "调整 revenue_factor 或重新训练预测模型",
        "priority": "high",
    },
    "profit_prediction_error": {
        "suggestion": "优化利润预测准确性",
        "module": "outcome_predictor.py",
        "action": "调整 profit_factor 或增加成本因素考虑",
        "priority": "high",
    },
    "no_action_overlap": {
        "suggestion": "参考人类行动模式",
        "module": "self_reflection.py",
        "action": "在决策时更多参考历史成功案例的具体行动",
        "priority": "medium",
    },
    "low_action_overlap": {
        "suggestion": "提高行动方案相似度",
        "module": "pattern_engine.py",
        "action": "增加相似场景的行动方案学习",
        "priority": "medium",
    },
    "low_confidence": {
        "suggestion": "提高决策置信度",
        "module": "confidence.py",
        "action": "增强场景识别或增加参考信息",
        "priority": "low",
    },
}


def suggest_improvement(reasons: list) -> list:
    suggestions = []
    seen = set()

    for reason in reasons:
        if reason in SUGGESTION_MAP and reason not in seen:
            info = SUGGESTION_MAP[reason]
            suggestions.append(
                {
                    "reason": reason,
                    "suggestion": info["suggestion"],
                    "module": info["module"],
                    "action": info["action"],
                    "priority": info["priority"],
                }
            )
            seen.add(reason)

    suggestions.sort(
        key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 3)
    )

    return suggestions


def get_top_improvements(stats: dict, limit: int = 3) -> list:
    top_reasons = stats.get("top_failure_reasons", [])[:limit]
    return suggest_improvement(top_reasons)


def get_priority_improvements() -> dict:
    all_improvements = []
    for reason, info in SUGGESTION_MAP.items():
        if info["priority"] == "high":
            all_improvements.append(
                {
                    "reason": reason,
                    "suggestion": info["suggestion"],
                    "module": info["module"],
                    "action": info["action"],
                    "priority": info["priority"],
                }
            )

    return {
        "priority_improvements": all_improvements,
        "count": len(all_improvements),
    }


def translate_reason(reason: str) -> str:
    translations = {
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
    return translations.get(reason, reason)
