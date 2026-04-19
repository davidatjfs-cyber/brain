import os
import json
import uuid
import re
from typing import List, Dict, Any, Optional

PATTERNS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "patterns.json"
)


def _ensure_file():
    os.makedirs(os.path.dirname(PATTERNS_FILE), exist_ok=True)
    if not os.path.exists(PATTERNS_FILE):
        with open(PATTERNS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "patterns": [],
                    "meta": {
                        "version": "1.0",
                        "created": "2026-04-11",
                        "total_abstracted": 0,
                    },
                },
                f,
                ensure_ascii=False,
                indent=2,
            )


def load_patterns() -> Dict[str, Any]:
    _ensure_file()
    with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_patterns(data: Dict):
    with open(PATTERNS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _generate_id() -> str:
    data = load_patterns()
    n = len(data["patterns"]) + 1
    return f"pattern_{n:03d}"


def extract_conditions(record) -> Dict[str, str]:
    if hasattr(record, "model_dump"):
        record = record.model_dump()
    m = record["input"]["metrics"]
    feedback_list = record["input"].get("feedback", [])
    scenario_text = record["input"].get("scenario", "")

    conditions = {}

    revenue = m.get("revenue") or m.get("营收") or m.get("日营收", 0)
    if isinstance(revenue, str):
        revenue = float(re.sub(r"[^\d.]", "", revenue)) if revenue else 0
    target_revenue = m.get("target_revenue") or m.get("目标营收", 15000)
    if revenue < target_revenue * 0.8:
        conditions["revenue_trend"] = "down"
    elif revenue > target_revenue * 1.1:
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

    complaint_keywords = {
        "service": ["服务", "态度", "服务员", "服务差"],
        "quality": ["质量", "味道", "口感", "不新鲜", "变质"],
        "environment": ["环境", "太冷", "太热", "脏", "吵", "噪音"],
        "price": ["价格", "贵", "性价比", "不值"],
    }
    matched_complaints = []
    for fb in feedback_list:
        content = str(fb.get("content", "")) + str(fb.get("type", ""))
        for ctype, keywords in complaint_keywords.items():
            if any(kw in content for kw in keywords):
                matched_complaints.append(ctype)
    if matched_complaints:
        conditions["complaint_type"] = matched_complaints[0]
    else:
        conditions["complaint_type"] = "none"

    if "包房" in scenario_text or "包房" in str(m):
        conditions["has_private_room_issue"] = "true"
    if any(kw in scenario_text for kw in ["客流量", "客流", "人少", "没人"]):
        conditions["customer_flow"] = "low"
    if any(kw in scenario_text for kw in ["客单价", "人均", "单价"]):
        conditions["avg_price"] = "concern"

    return conditions


def extract_pattern(record) -> Optional[Dict[str, Any]]:
    if hasattr(record, "model_dump"):
        record = record.model_dump()
    score = record.get("evaluation", {}).get("score", 0)
    if score < 0.75:
        return None

    conditions = extract_conditions(record)
    d = record["decision"]

    pattern = {
        "id": _generate_id(),
        "conditions": conditions,
        "decision_type": d.get("decision_type", "operation"),
        "strategy": d.get("decision", ""),
        "actions": d.get("actions", []),
        "expected_impact": d.get("expected_impact", ""),
        "score": round(score, 3),
        "usage_count": 1,
        "abstracted_from": d.get("decision_id", ""),
    }

    return pattern


def _conditions_match(c1: Dict, c2: Dict) -> bool:
    common_keys = set(c1.keys()) & set(c2.keys())
    if not common_keys:
        return False
    matches = sum(1 for k in common_keys if c1[k] == c2[k])
    return matches >= max(1, int(len(common_keys) * 0.6))


def add_or_update_pattern(record) -> str:
    pattern = extract_pattern(record)
    if not pattern:
        return "未达到抽象阈值(score<0.75)"

    data = load_patterns()
    pattern_id = None

    for i, p in enumerate(data["patterns"]):
        if _conditions_match(pattern["conditions"], p["conditions"]):
            if pattern["score"] > p["score"]:
                data["patterns"][i] = pattern
                pattern_id = pattern["id"]
                data["meta"]["total_abstracted"] += 1
                save_patterns(data)
                return f"✅ 更新策略规律 {pattern['id']} (score {p['score']:.3f}→{pattern['score']:.3f})"
            else:
                data["patterns"][i]["usage_count"] += 1
                pattern_id = p["id"]
                save_patterns(data)
                return f"⏭️ 匹配已有规律 {p['id']} (usage_count={data['patterns'][i]['usage_count']})"

    data["patterns"].append(pattern)
    data["meta"]["total_abstracted"] += 1
    save_patterns(data)
    return f"✅ 新增策略规律 {pattern['id']} (conditions={list(pattern['conditions'].keys())})"


def get_all_patterns() -> List[Dict[str, Any]]:
    return load_patterns().get("patterns", [])


def get_patterns_summary() -> str:
    patterns = get_all_patterns()
    if not patterns:
        return "策略规律库为空，暂无抽象出的规律。"

    lines = ["【策略规律库】"]
    for p in patterns:
        cond_str = " | ".join(f"{k}={v}" for k, v in p["conditions"].items())
        lines.append(
            f"  {p['id']} | {p['decision_type']} | score:{p['score']:.2f} | 使用:{p['usage_count']}次"
        )
        lines.append(f"    条件: {cond_str}")
        lines.append(f"    策略: {p['strategy'][:60]}")
        lines.append("")
    return "\n".join(lines)
