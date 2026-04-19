from typing import List, Dict, Any


def build_pattern_context(patterns: List[Dict[str, Any]]) -> str:
    if not patterns:
        return "暂无匹配策略规律（策略规律库为空）"

    lines = ["【匹配到的策略规律】"]
    for p in patterns:
        cond_str = " | ".join(f"{k}={v}" for k, v in p["conditions"].items())
        actions_short = " | ".join(a[:40] for a in p.get("actions", [])[:2])
        lines.append(
            f"\n📌 {p['id']} | 类型:{p['decision_type']} | 评分:{p['score']:.2f} | 使用:{p['usage_count']}次"
        )
        lines.append(f"   条件: {cond_str}")
        lines.append(f"   策略: {p['strategy'][:80]}")
        lines.append(f"   执行: {actions_short}")

    return "\n".join(lines)


def build_pattern_constraint_text(patterns: List[Dict[str, Any]]) -> str:
    if not patterns:
        return ""

    lines = ["【必须遵守的策略规律】"]
    for p in patterns:
        lines.append(
            f"  ✅ {p['id']}: 当{_cond_text(p['conditions'])}时，使用「{p['strategy'][:60]}」"
        )

    return "\n".join(lines)


def _cond_text(conditions: Dict[str, str]) -> str:
    return " 且 ".join(f"{k}={v}" for k, v in conditions.items())
