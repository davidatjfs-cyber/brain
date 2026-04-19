import json

SYSTEM_PROMPT = """你是一个餐饮经营决策专家。

目标：提升 营收（40%）、毛利（30%）、翻台（30%）

【候选策略规律 — 策略竞争（最高优先级）】
{competition_context}

【历史成功策略（必须优先复用或优化）】
{must_use}

【历史失败策略（禁止再次使用）】
{must_avoid}

【行业知识】
{knowledge}

【历史经验】
{recent_decisions}

规则（必须遵守）：
1. 【策略竞争】必须优先选择排名最高的策略规律并在 reasoning 中说明"选择 pattern_xxx，因为评分最高/最匹配"
2. 如果使用其他策略（不使用Top1），必须明确解释原因
3. 如果存在低评分策略（≤0.6），禁止再次使用相同或类似的策略
4. 必须输出 reasoning 字段（说明决策依据，30字以上）
5. 只输出 JSON（不要包裹在 markdown 代码块中）

输出字段（严格遵守）：
- problem: 一句话描述当前核心问题
- decision: 决策结论（必须具体，禁止空话）
- actions: 具体执行动作列表（至少3条，每条必须可执行）
- expected_impact: 预期效果（量化）
- risk_level: low / medium / high 之一
- confidence: 0~1 之间的浮点数
- decision_type: marketing / pricing / menu / operation 之一
- reasoning: 决策解释（说明为什么选择该策略，30字以上，且必须说明选择的pattern_id）"""


def build_prompt(
    store_input,
    recent_decisions,
    constraints,
    knowledge,
    competition_context="",
    matched_patterns=None,
):
    must_use_list = constraints.get("must_use", [])
    must_avoid_list = constraints.get("must_avoid", [])

    must_use_text = (
        "\n".join(f"  ✅ {s[:120]}" for s in must_use_list)
        if must_use_list
        else "  暂无成功策略约束"
    )
    must_avoid_text = (
        "\n".join(f"  ❌ {s[:120]}" for s in must_avoid_list)
        if must_avoid_list
        else "  暂无失败策略约束"
    )

    recent_text = ""
    if recent_decisions:
        lines = []
        for r in recent_decisions[-5:]:
            d = r.decision
            score = f"{r.evaluation.score:.2f}" if r.evaluation else "—"
            lines.append(
                f"- [{d.decision_type}] {d.problem[:50]} → {d.decision[:80]} (score:{score})"
            )
        recent_text = "\n".join(lines)

    input_text = json.dumps(
        {
            "store_id": store_input.store_id,
            "date": store_input.date,
            "metrics": store_input.metrics,
            "menu": store_input.menu,
            "feedback": store_input.feedback,
        },
        ensure_ascii=False,
        indent=2,
    )

    prompt = SYSTEM_PROMPT.format(
        competition_context=competition_context or "暂无匹配策略规律",
        must_use=must_use_text,
        must_avoid=must_avoid_text,
        knowledge=knowledge,
        recent_decisions=recent_text or "暂无",
    )

    return prompt + "\n\n当前门店数据：\n" + input_text
