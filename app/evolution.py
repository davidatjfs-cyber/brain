import json
import os
from typing import List, Dict, Any
from app.pattern_engine import add_or_update_pattern
from app.pattern_scorer import update_pattern_score
from app.debug_logger import log_evaluation


STRATEGY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "strategy_patterns.json"
)


def _load_patterns() -> Dict[str, List[Dict[str, Any]]]:
    os.makedirs(os.path.dirname(STRATEGY_FILE), exist_ok=True)
    if not os.path.exists(STRATEGY_FILE):
        init = {"high_score_patterns": [], "failed_patterns": []}
        with open(STRATEGY_FILE, "w", encoding="utf-8") as f:
            json.dump(init, f, ensure_ascii=False, indent=2)
        return init
    with open(STRATEGY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_patterns(data: Dict):
    with open(STRATEGY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def evolve_from_evaluation(decision_record) -> str:
    if not decision_record.evaluation:
        return "尚无评估结果，无需进化"

    score = decision_record.evaluation.score
    d = decision_record.decision

    pattern_result = add_or_update_pattern(decision_record)

    used_ids = d.used_pattern_ids if hasattr(d, "used_pattern_ids") else []
    score_results = []
    for pid in used_ids:
        r = update_pattern_score(pid, score)
        if "✅" in r:
            score_results.append(r)

    patterns = _load_patterns()

    entry = {
        "decision_type": d.decision_type,
        "problem": d.problem[:100],
        "decision": d.decision[:150],
        "actions": d.actions,
        "score": score,
        "final_judgement": decision_record.evaluation.final_judgement,
    }

    saved = None

    if score >= 0.3:
        existing = [
            i
            for i, p in enumerate(patterns["high_score_patterns"])
            if p["decision_type"] == d.decision_type
        ]
        if existing:
            idx = existing[0]
            old = patterns["high_score_patterns"][idx]
            patterns["high_score_patterns"][idx] = (
                entry if score > old.get("score", -999) else old
            )
            saved = "更新成功策略"
        else:
            patterns["high_score_patterns"].append(entry)
            saved = "新增成功策略"

    elif score <= -0.2:
        existing = [
            i
            for i, p in enumerate(patterns["failed_patterns"])
            if p["decision_type"] == d.decision_type
        ]
        if existing:
            idx = existing[0]
            old = patterns["failed_patterns"][idx]
            patterns["failed_patterns"][idx] = (
                entry if score < old.get("score", 999) else old
            )
            saved = "更新失败策略"
        else:
            patterns["failed_patterns"].append(entry)
            saved = "新增失败策略"

    _save_patterns(patterns)

    if saved:
        judgement = decision_record.evaluation.final_judgement
        parts = [
            f"✅ {saved}（{d.decision_type} | score={score:.3f} | {judgement}）",
            f"🔄 {pattern_result}",
        ]
        if score_results:
            parts.append("📊 " + " | ".join(score_results))
        result = "\n".join(parts)
        log_evaluation(decision_record.decision.decision_id, score, score_results)
        return result

    log_evaluation(decision_record.decision.decision_id, score, [])
    return f"⏭️ score={score:.3f}，未达沉淀阈值（≥0.3为成功，≤-0.2为失败）"


def get_high_score_patterns() -> List[Dict]:
    return _load_patterns().get("high_score_patterns", [])


def get_failed_patterns() -> List[Dict]:
    return _load_patterns().get("failed_patterns", [])


def build_patterns_summary() -> str:
    high = get_high_score_patterns()
    failed = get_failed_patterns()

    lines = []
    if high:
        lines.append("【成功策略库】")
        for p in high[:5]:
            lines.append(
                f"  ✅ [{p['decision_type']}] score:{p.get('score', 0):.2f} | "
                f"{p.get('decision', '')[:80]}"
            )

    if failed:
        lines.append("\n【失败策略库】")
        for p in failed[:5]:
            lines.append(
                f"  ❌ [{p['decision_type']}] score:{p.get('score', 0):.2f} | "
                f"{p.get('problem', '')[:80]}"
            )

    return "\n".join(lines) if lines else "策略库为空"


def auto_evolve(records):
    """
    自动识别：
    - 高频成功策略：同一 decision_type 出现多次高分
    - 高频失败模式：同一 decision_type 出现多次低分
    - 返回进化建议
    """
    if not records:
        return {
            "suggestion": "暂无足够数据，建议积累20条以上决策后再分析",
            "high_freq": [],
            "low_freq": [],
        }

    type_scores = {}
    for r in records:
        if not r.evaluation:
            continue
        t = r.decision.decision_type
        if t not in type_scores:
            type_scores[t] = []
        type_scores[t].append(r.evaluation.score)

    high_freq = []
    low_freq = []

    for t, scores in type_scores.items():
        if len(scores) < 2:
            continue
        avg = sum(scores) / len(scores)
        if avg >= 0.7 and len(scores) >= 2:
            high_freq.append(
                {"type": t, "avg_score": round(avg, 3), "count": len(scores)}
            )
        elif avg <= 0.5 and len(scores) >= 2:
            low_freq.append(
                {"type": t, "avg_score": round(avg, 3), "count": len(scores)}
            )

    suggestion = ""
    if high_freq:
        types = "/".join(f["type"] for f in high_freq)
        suggestion += f"✅ 高频成功类型：{types}，应优先复用。"

    if low_freq:
        types = "/".join(f["type"] for f in low_freq)
        suggestion += f"❌ 高频失败类型：{types}，应减少使用。"

    return {
        "suggestion": suggestion or "数据分布正常，继续观察",
        "high_freq": high_freq,
        "low_freq": low_freq,
    }
