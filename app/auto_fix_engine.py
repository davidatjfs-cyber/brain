import json
import time
from app.parameter_store import load_params, save_params
from app.stabilizer import stabilize, stabilize_batch, get_stability_report

FIX_RULES = {
    "too_risky": {
        "params": {"risk_penalty": 0.05},
        "direction": "increase",
    },
    "too_conservative": {
        "params": {"risk_penalty": 0.05},
        "direction": "decrease",
    },
    "bad_prediction": {
        "params": {
            "revenue_factor": 0.05,
            "profit_factor": 0.05,
            "turnover_factor": 0.05,
        },
        "direction": "decrease",
    },
    "revenue_prediction_error": {
        "params": {"revenue_factor": 0.05},
        "direction": "decrease",
    },
    "profit_prediction_error": {
        "params": {"profit_factor": 0.05},
        "direction": "decrease",
    },
    "insufficient_actions": {
        "params": {"explore_rate": 0.02},
        "direction": "increase",
    },
    "low_action_overlap": {
        "params": {"explore_rate": 0.01},
        "direction": "increase",
    },
    "strategy_mismatch": {
        "params": {"pattern_match_threshold": 0.05},
        "direction": "decrease",
    },
    "low_confidence": {
        "params": {"confidence_threshold": 0.05},
        "direction": "decrease",
    },
}

PARAM_LIMITS = {
    "risk_penalty": {"min": 0.0, "max": 1.0},
    "revenue_factor": {"min": 0.5, "max": 1.5},
    "profit_factor": {"min": 0.5, "max": 1.5},
    "turnover_factor": {"min": 0.5, "max": 1.5},
    "explore_rate": {"min": 0.05, "max": 0.3},
    "confidence_threshold": {"min": 0.5, "max": 0.9},
    "pattern_match_threshold": {"min": 0.4, "max": 0.8},
}


def apply_fix(reasons: list) -> dict:
    params = load_params()
    original_params = params.copy()

    raw_fixes = []
    for reason in reasons:
        if reason not in FIX_RULES:
            continue

        rule = FIX_RULES[reason]
        for param_name, delta in rule["params"].items():
            raw_fixes.append(
                {
                    "reason": reason,
                    "param": param_name,
                    "delta": delta,
                    "direction": rule["direction"],
                }
            )

    batch_result = stabilize_batch(params, raw_fixes)
    params = batch_result["updated_params"]

    applied = []
    for i, raw_fix in enumerate(raw_fixes):
        result = batch_result["fix_results"][i]["result"]
        if result["applied"]:
            applied.append(
                {
                    "reason": raw_fix["reason"],
                    "param": raw_fix["param"],
                    "direction": raw_fix["direction"],
                    "delta": raw_fix["delta"],
                    "actual_change": result["change"],
                    "adaptive_rate": result["adaptive_rate"],
                    "before": original_params.get(raw_fix["param"]),
                    "after": params.get(raw_fix["param"]),
                    "oscillation_dampened": "_oscillation_dampened"
                    in result.get("reason", ""),
                }
            )

    save_params(params)

    stability = get_stability_report()

    return {
        "applied_fixes": applied,
        "updated_params": params,
        "fix_count": len(applied),
        "stability": stability,
    }


def get_fix_history() -> list:
    try:
        with open("data/fix_history.json", "r") as f:
            return json.load(f)
    except:
        return []


def save_fix_record(applied_fixes: list, reasons: list) -> None:
    try:
        with open("data/fix_history.json", "r") as f:
            history = json.load(f)
    except:
        history = []

    history.append(
        {
            "timestamp": time.time(),
            "reasons": reasons,
            "fixes": applied_fixes,
        }
    )

    with open("data/fix_history.json", "w") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def get_fix_stats() -> dict:
    history = get_fix_history()

    if not history:
        return {
            "total_fixes": 0,
            "most_adjusted_param": None,
            "param_adjustments": {},
        }

    param_counts = {}
    for record in history:
        for fix in record.get("fixes", []):
            param = fix.get("param")
            param_counts[param] = param_counts.get(param, 0) + 1

    most_adjusted = (
        max(param_counts.items(), key=lambda x: x[1]) if param_counts else (None, 0)
    )

    return {
        "total_fixes": len(history),
        "most_adjusted_param": most_adjusted[0],
        "param_adjustments": param_counts,
        "recent_fixes": history[-5:] if len(history) >= 5 else history,
    }
