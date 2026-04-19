import re
from typing import Dict, Any, Optional, List


def format_decision_debug(
    store_input,
    matched_patterns: List[Dict],
    ranked_patterns: List[Dict],
    top_pattern_ids: List[str],
    constraints: Dict,
    raw_llm_output: str,
    decision_result: Dict,
    enforcement_result: Dict,
    simulation_data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    top_pattern = None
    if ranked_patterns and top_pattern_ids:
        for item in ranked_patterns:
            if item["pattern"]["id"] == top_pattern_ids[0]:
                top_pattern = item["pattern"]
                break

    chosen_reason = ""
    if top_pattern:
        chosen_reason = f"选择 {top_pattern['id']}，因为其综合评分最高"
    elif matched_patterns:
        chosen_reason = "无匹配策略，从头生成决策"
    else:
        chosen_reason = "策略规律库为空"

    return {
        "_type": "decision",
        "decision_id": decision_result.get("decision_id"),
        "store_id": store_input.store_id,
        "date": store_input.date,
        "input_summary": _summarize_input(store_input),
        "constraints": {
            "must_use_count": len(constraints.get("must_use", [])),
            "must_avoid_count": len(constraints.get("must_avoid", [])),
        },
        "pattern_candidates": [
            {
                "rank": item["rank"],
                "id": item["pattern"]["id"],
                "base_score": item["base_score"],
                "final_score": item["final_score"],
                "usage_count": item["usage_count"],
                "conditions": item["pattern"].get("conditions", {}),
                "strategy_preview": item["pattern"]["strategy"][:60],
            }
            for item in ranked_patterns
        ],
        "chosen_pattern": (
            {
                "id": top_pattern["id"],
                "score": top_pattern["score"],
                "final_score": ranked_patterns[0]["final_score"]
                if ranked_patterns
                else None,
                "strategy": top_pattern["strategy"][:80],
            }
            if top_pattern
            else None
        ),
        "choose_reason": chosen_reason,
        "llm_output_length": len(raw_llm_output),
        "confidence_before_calibration": decision_result.get("decision", {}).get(
            "confidence"
        ),
        "confidence_final": decision_result.get("decision", {}).get("confidence"),
        "status": decision_result.get("status"),
        "enforcement": {
            "adjustment": enforcement_result.get("adjustment"),
            "used_good_patterns": enforcement_result.get("used_good", []),
            "used_bad_patterns": enforcement_result.get("used_bad", []),
        },
        "check": decision_result.get("check", {}),
        "simulation": simulation_data or {},
    }


def _summarize_input(store_input) -> Dict[str, Any]:
    m = store_input.metrics
    summary = {}

    revenue = m.get("revenue") or m.get("营收", 0)
    if isinstance(revenue, str):
        revenue = float(re.sub(r"[^\d.]", "", revenue)) if revenue else 0
    summary["revenue"] = revenue

    turnover = m.get("turnover_rate") or m.get("翻台率") or m.get("turnover", 0)
    if isinstance(turnover, str):
        turnover = float(re.sub(r"[^\d.]", "", turnover)) if turnover else 0
    summary["turnover_rate"] = turnover

    pr = m.get("包房使用率") or m.get("private_room", 0)
    if isinstance(pr, str):
        pr = float(re.sub(r"[^\d.]", "", pr)) if pr else 0
    summary["private_room_usage"] = pr

    summary["feedback_count"] = len(store_input.feedback or [])
    summary["scenario"] = (store_input.scenario or "")[:80]

    return summary


def format_score_change(old_score: float, new_score: float, result_score: float) -> str:
    delta = new_score - old_score
    direction = "↑" if delta > 0.001 else ("↓" if delta < -0.001 else "→")
    return f"{old_score:.4f} {direction} {new_score:.4f} (result={result_score:.2f})"


def format_log_entry(entry: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"  🏪 {entry.get('store_id', '?')} | {entry.get('_ts', '')}")
    lines.append(f"  📋 决策ID: {entry.get('decision_id', '')[:20]}...")

    inp = entry.get("input_summary", {})
    lines.append(
        f"  📊 数据: 营收={inp.get('revenue', '?')} | "
        f"翻台={inp.get('turnover_rate', '?')} | "
        f"包房={inp.get('private_room_usage', '?')} | "
        f"差评={inp.get('feedback_count', 0)}条"
    )

    candidates = entry.get("pattern_candidates", [])
    if candidates:
        lines.append(f"  🏆 策略竞争 ({len(candidates)}个候选):")
        medals = ["🥇", "🥈", "🥉"]
        for c in candidates:
            medal = medals[c["rank"] - 1] if c["rank"] <= 3 else f" {c['rank']}."
            lines.append(
                f"    {medal} {c['id']}: 综合={c['final_score']:.3f} "
                f"(原始={c['base_score']:.2f}, 使用={c['usage_count']}次)"
            )
    else:
        lines.append("  🏆 策略竞争: 无匹配")

    chosen = entry.get("chosen_pattern")
    if chosen:
        lines.append(f"  ✅ 选择: {chosen['id']} (score={chosen['final_score']:.3f})")
    else:
        lines.append("  ✅ 选择: 无 (从头生成)")

    lines.append(f"  📝 原因: {entry.get('choose_reason', '')}")
    lines.append(
        f"  🎯 置信度: {entry.get('confidence_final', 0):.2f} → {entry.get('status', '')}"
    )

    sim = entry.get("simulation", {})
    if sim:
        ranking = sim.get("ranking", [])
        if ranking:
            lines.append(f"  🔮 模拟预测 ({len(ranking)}个候选):")
            for r in ranking:
                pid = r.get("pattern_id") or (
                    "exploration" if r.get("is_exploration") else "?"
                )
                outcome = r.get("outcome", {})
                rev = outcome.get("revenue_change", 0)
                tur = outcome.get("turnover_change", 0)
                pro = outcome.get("profit_change", 0)
                medal = (
                    ["🥇", "🥈", "🥉"][r["rank"] - 1]
                    if r["rank"] <= 3
                    else f" {r['rank']}."
                )
                lines.append(
                    f"    {medal} {pid}: 预测分={r.get('simulated_score', 0):.4f} "
                    f"(营收{'+' if rev > 0 else ''}{rev:.2f} "
                    f"翻台{'+' if tur > 0 else ''}{tur:.2f} "
                    f"毛利{'+' if pro > 0 else ''}{pro:.2f})"
                )
            lines.append(f"  🔮 模拟说明: {sim.get('explanation', '')}")

    ev = entry.get("_evaluation")
    if ev:
        lines.append(
            f"  📈 评估: score={ev['score']:.2f} | {ev.get('evaluated_at', '')}"
        )

    return "\n".join(lines)
