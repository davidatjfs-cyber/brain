import os
import json
from typing import Dict, Any
from app.eval_logger import get_eval_history, _load as _load_evals


BIAS_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "bias_log.json"
)


def _load_bias_log() -> Dict[str, Any]:
    if not os.path.exists(BIAS_LOG_PATH):
        return {"consecutive_high": 0, "high_score_streak": 0, "last_pattern_id": None}
    try:
        with open(BIAS_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"consecutive_high": 0, "high_score_streak": 0, "last_pattern_id": None}


def _save_bias_log(data: Dict[str, Any]):
    with open(BIAS_LOG_PATH, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)


def anti_bias_check(decision: Dict[str, Any], score: float) -> float:
    bias = _load_bias_log()
    used_ids = decision.get("used_pattern_ids", [])
    current_pattern = used_ids[0] if used_ids else None
    eval_history = get_eval_history(limit=10)

    if decision.get("is_exploration") and score > 0.85:
        score = 0.80

    if score > 0.9:
        score = 0.88
    current_pattern = used_ids[0] if used_ids else None
    eval_history = get_eval_history(limit=10)

    if score > 0.9:
        score = 0.88

    if not used_ids and score > 0.75:
        score = min(score, 0.72)

    if used_ids:
        from app.pattern_engine import get_all_patterns

        patterns = get_all_patterns()
        for p in patterns:
            if p["id"] == current_pattern:
                if p.get("usage_count", 0) > 15:
                    score -= 0.05
                break

    recent_high = [e for e in eval_history if e["score"] >= 0.8]
    if len(recent_high) >= 3:
        score -= 0.08
        bias["consecutive_high"] += 1
    else:
        bias["consecutive_high"] = max(0, bias["consecutive_high"] - 1)

    if score >= 0.7:
        bias["high_score_streak"] += 1
    else:
        bias["high_score_streak"] = 0

    if bias["high_score_streak"] >= 5:
        score -= 0.1

    if (
        bias["last_pattern_id"] == current_pattern
        and bias["high_score_streak"] >= 3
        and score >= 0.7
    ):
        score -= 0.05

    bias["last_pattern_id"] = current_pattern
    _save_bias_log(bias)

    return round(max(0.0, min(score, 1.0)), 4)


def get_bias_status() -> Dict[str, Any]:
    bias = _load_bias_log()
    eval_history = get_eval_history(limit=10)
    recent_high = sum(1 for e in eval_history if e["score"] >= 0.8)
    return {
        "consecutive_high_count": bias.get("consecutive_high", 0),
        "high_score_streak": bias.get("high_score_streak", 0),
        "recent_high_scores": recent_high,
        "last_pattern": bias.get("last_pattern_id"),
        "warnings": _get_warnings(bias, recent_high),
    }


def _get_warnings(bias: Dict[str, Any], recent_high: int) -> list:
    warnings = []
    if bias.get("consecutive_high", 0) >= 3:
        warnings.append("⚠️ 连续高分过多，可能存在自我强化")
    if bias.get("high_score_streak", 0) >= 5:
        warnings.append("⚠️ 高分连续5次以上，已降权")
    if recent_high >= 3:
        warnings.append("⚠️ 近10次评估中3次以上≥0.8")
    return warnings
