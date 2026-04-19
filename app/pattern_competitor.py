import re
from typing import List, Dict, Any


def _calc_competition_score(pattern: Dict[str, Any], store_input) -> float:
    base = pattern["score"]
    m = store_input.metrics

    if m.get("turnover_rate", 0) < 1.2 or m.get("翻台率", 0) < 1.2:
        base += 0.05
    if m.get("revenue", 0) < 12000 or m.get("营收", 0) < 12000:
        base += 0.05
    if m.get("private_room", 0) < 0.22 or m.get("包房使用率", 0) < 0.22:
        base += 0.03
    if pattern.get("usage_count", 0) >= 3:
        base += 0.02

    if pattern.get("usage_count", 0) == 0:
        base -= 0.02

    return round(base, 4)


def rank_patterns(
    patterns: List[Dict[str, Any]], store_input, top_n: int = 3
) -> List[Dict[str, Any]]:
    if not patterns:
        return []

    scored = []
    for p in patterns:
        cs = _calc_competition_score(p, store_input)
        scored.append(
            {
                "pattern": p,
                "final_score": cs,
                "base_score": p["score"],
                "usage_count": p.get("usage_count", 0),
                "rank": 0,
            }
        )

    scored.sort(key=lambda x: (x["final_score"], x["usage_count"]), reverse=True)

    for i, item in enumerate(scored):
        item["rank"] = i + 1

    return scored[:top_n]


def get_top_patterns(
    patterns: List[Dict[str, Any]], store_input, top_n: int = 2
) -> List[Dict[str, Any]]:
    ranked = rank_patterns(patterns, store_input, top_n=top_n)
    return [item["pattern"] for item in ranked]


def build_competition_context(patterns: List[Dict[str, Any]], store_input) -> str:
    if not patterns:
        return "暂无匹配策略规律"

    ranked = rank_patterns(patterns, store_input, top_n=3)

    lines = ["【策略竞争 — 候选规律（按优先级排序）】"]
    medals = ["🥇", "🥈", "🥉"]
    for i, item in enumerate(ranked):
        p = item["pattern"]
        cond_str = " | ".join(f"{k}={v}" for k, v in p["conditions"].items())
        lines.append(
            f"\n{medals[i] if i < 3 else f'{i + 1}.'} {p['id']} (综合评分:{item['final_score']:.3f} | "
            f"原始:{item['base_score']:.2f} | 使用:{item['usage_count']}次)"
        )
        lines.append(f"   条件: {cond_str}")
        lines.append(f"   策略: {p['strategy'][:80]}")

    lines.append("\n规则：必须优先选择排名最高的策略并复用，如不选则需解释原因。")
    return "\n".join(lines)
