import os
import json
from typing import Dict, Any, Optional


PATTERNS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "patterns.json"
)


def _load() -> Dict[str, Any]:
    if not os.path.exists(PATTERNS_FILE):
        return {
            "patterns": [],
            "meta": {"version": "1.0", "created": "2026-04-11", "total_abstracted": 0},
        }
    with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: Dict[str, Any]):
    with open(PATTERNS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_pattern_score(pattern_id: str, result_score: float) -> str:
    data = _load()
    found = False

    for p in data["patterns"]:
        if p["id"] == pattern_id:
            old_score = p["score"]
            p["score"] = round(p["score"] * 0.7 + result_score * 0.3, 4)
            p["usage_count"] = p.get("usage_count", 0) + 1
            _save(data)
            found = True

            delta = p["score"] - old_score
            direction = "↑" if delta > 0 else ("↓" if delta < 0 else "→")
            return (
                f"✅ 更新 {pattern_id} 评分: {old_score:.3f}{direction}{p['score']:.3f} "
                f"(result={result_score:.2f}, usage={p['usage_count']}次)"
            )

    if not found:
        return f"⚠️ 未找到 pattern_id: {pattern_id}"


def get_pattern_by_id(pattern_id: str) -> Optional[Dict[str, Any]]:
    data = _load()
    for p in data["patterns"]:
        if p["id"] == pattern_id:
            return p
    return None


def update_pattern_usage(pattern_id: str) -> str:
    data = _load()
    for p in data["patterns"]:
        if p["id"] == pattern_id:
            p["usage_count"] = p.get("usage_count", 0) + 1
            _save(data)
            return f"✅ {pattern_id} usage_count → {p['usage_count']}"
    return f"⚠️ 未找到 {pattern_id}"
