from typing import List, Dict, Any
import re
from app.pattern_engine import get_all_patterns, load_patterns


def _build_input_conditions(store_input) -> Dict[str, str]:
    m = store_input.metrics
    conditions = {}

    revenue = m.get("revenue") or m.get("营收") or m.get("日营收", 0)
    if isinstance(revenue, str):
        revenue = float(re.sub(r"[^\d.]", "", revenue)) if revenue else 0
    target = m.get("target_revenue") or m.get("目标营收", 15000)
    if revenue < target * 0.8:
        conditions["revenue_trend"] = "down"
    elif revenue > target * 1.1:
        conditions["revenue_trend"] = "up"
    else:
        conditions["revenue_trend"] = "normal"

    turnover = m.get("turnover") or m.get("turnover_rate") or m.get("翻台率", 0)
    if isinstance(turnover, str):
        turnover = float(re.sub(r"[^\d.]", "", turnover)) if turnover else 0
    if turnover < 1.5:
        conditions["turnover_rate"] = "low"
    elif turnover > 2.5:
        conditions["turnover_rate"] = "high"
    else:
        conditions["turnover_rate"] = "normal"

    private_room = m.get("private_room") or m.get("包房使用率", 0)
    if isinstance(private_room, str):
        private_room = float(re.sub(r"[^\d.]", "", private_room)) if private_room else 0
    if private_room < 0.22:
        conditions["private_room_usage"] = "low"
    elif private_room > 0.35:
        conditions["private_room_usage"] = "high"
    else:
        conditions["private_room_usage"] = "normal"

    feedback_list = store_input.feedback or []
    complaint_keywords = {
        "service": ["服务", "态度", "服务员", "服务差"],
        "quality": ["质量", "味道", "口感", "不新鲜"],
        "environment": ["环境", "太冷", "太热", "脏", "噪音"],
        "price": ["价格", "贵", "性价比"],
    }
    for fb in feedback_list:
        content = str(fb.get("content", "")) + str(fb.get("type", ""))
        for ctype, keywords in complaint_keywords.items():
            if any(kw in content for kw in keywords):
                conditions["complaint_type"] = ctype
                break
    if "complaint_type" not in conditions:
        conditions["complaint_type"] = "none"

    scenario = store_input.scenario or ""
    if "包房" in scenario:
        conditions["has_private_room_issue"] = "true"
    if any(kw in scenario for kw in ["客流量", "客流", "人少"]):
        conditions["customer_flow"] = "low"
    if any(kw in scenario for kw in ["客单价", "人均"]):
        conditions["avg_price"] = "concern"

    return conditions


def _score_match(input_cond: Dict[str, str], pattern_cond: Dict[str, str]) -> float:
    if not pattern_cond:
        return 0.0

    total = len(pattern_cond)
    matched = 0
    for key, pval in pattern_cond.items():
        ival = input_cond.get(key, "")
        if ival == pval:
            matched += 1.0
        elif key == "complaint_type" and pval != "none" and ival != "none":
            matched += 0.5
        elif key == "has_private_room_issue" and pval == "true" and ival == "true":
            matched += 1.0

    return matched / total if total > 0 else 0.0


def match_patterns(store_input, top_n: int = 3) -> List[Dict[str, Any]]:
    patterns = get_all_patterns()
    if not patterns:
        return []

    input_cond = _build_input_conditions(store_input)

    scored = []
    for p in patterns:
        score = _score_match(input_cond, p["conditions"])
        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: (x[0], x[1]["score"]), reverse=True)
    return [p for _, p in scored[:top_n]]


def get_matched_pattern_ids(store_input) -> List[str]:
    matched = match_patterns(store_input, top_n=3)
    return [p["id"] for p in matched]
