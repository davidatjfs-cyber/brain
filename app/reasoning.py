from app.llm_client import call_llm


def build_reasoning(store_input, recent_decisions, knowledge, constraints) -> str:
    input_summary = (
        f"门店: {store_input.store_id} | 日期: {store_input.date} | "
        f"营收: {store_input.metrics.get('daily_revenue', 'N/A')}元 | "
        f"客流: {store_input.metrics.get('dine_traffic', 'N/A')}人 | "
        f"客单: {store_input.metrics.get('avg_ticket', 'N/A')}元"
    )

    history_lines = []
    for r in recent_decisions[-5:]:
        d = r.decision
        score = r.evaluation.score if r.evaluation else "未评估"
        history_lines.append(
            f"- [{d.decision_type}] {d.problem[:40]} → {d.decision[:60]} (score:{score})"
        )
    history_text = "\n".join(history_lines) or "暂无历史决策"

    high_patterns = constraints.get("high_patterns", [])
    low_patterns = constraints.get("low_patterns", [])

    prompt = f"""基于以下信息，生成一段简洁的决策解释（50字以内）：

当前数据：{input_summary}

历史经验：
{history_text}

成功策略参考：
{chr(10).join(f"- {p['decision'][:80]}" for p in high_patterns[:2]) if high_patterns else "暂无"}

本轮决策的核心理由是什么？请用一句话说明决策依据：
"""
    try:
        reasoning = call_llm(prompt).strip()
        if len(reasoning) > 200:
            reasoning = reasoning[:200]
        return reasoning if reasoning else "基于数据与历史经验综合分析得出"
    except Exception:
        return "基于历史经验与行业知识综合分析"
