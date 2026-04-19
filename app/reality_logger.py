import json
import os
import time
from typing import Dict, List, Optional

PATH = "data/real_outcomes.json"


def init_real_outcomes():
    os.makedirs("data", exist_ok=True)
    try:
        with open(PATH, "r") as f:
            json.load(f)
    except:
        with open(PATH, "w") as f:
            json.dump([], f)


def log_real_outcome(
    decision_id: str,
    before_data: Dict,
    after_data: Dict,
    shadow_log_id: str = None,
    is_brain_decision: bool = None,
    real_decision: Dict = None,
) -> str:
    init_real_outcomes()

    try:
        with open(PATH, "r") as f:
            data = json.load(f)
    except:
        data = []

    entry = {
        "decision_id": decision_id,
        "shadow_log_id": shadow_log_id,
        "timestamp": time.time(),
        "before": before_data,
        "after": after_data,
        "is_brain_decision": is_brain_decision,
        "real_decision_summary": _summarize_decision(real_decision)
        if real_decision
        else None,
    }

    data.append(entry)

    with open(PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return f"real_{len(data)}"


def get_real_outcomes(limit: int = 100) -> List[Dict]:
    init_real_outcomes()
    try:
        with open(PATH, "r") as f:
            data = json.load(f)
        return data[-limit:] if limit > 0 else data
    except:
        return []


def get_real_outcome_by_id(decision_id: str) -> Optional[Dict]:
    outcomes = get_real_outcomes(limit=0)
    for outcome in outcomes:
        if outcome.get("decision_id") == decision_id:
            return outcome
    return None


def get_real_outcomes_stats() -> Dict:
    outcomes = get_real_outcomes(limit=0)

    if not outcomes:
        return {
            "total_records": 0,
            "brain_decisions": 0,
            "human_decisions": 0,
            "avg_revenue_gain": 0,
            "avg_profit_gain": 0,
        }

    brain_count = sum(1 for o in outcomes if o.get("is_brain_decision", False))
    human_count = sum(1 for o in outcomes if not o.get("is_brain_decision", True))

    revenue_gains = []
    profit_gains = []

    brain_revenue_gains = []
    brain_profit_gains = []
    human_revenue_gains = []
    human_profit_gains = []

    for outcome in outcomes:
        before = outcome.get("before", {})
        after = outcome.get("after", {})

        rev_gain = after.get("revenue", 0) - before.get("revenue", 0)
        profit_gain = after.get("profit", 0) - before.get("profit", 0)

        revenue_gains.append(rev_gain)
        profit_gains.append(profit_gain)

        if outcome.get("is_brain_decision", False):
            brain_revenue_gains.append(rev_gain)
            brain_profit_gains.append(profit_gain)
        else:
            human_revenue_gains.append(rev_gain)
            human_profit_gains.append(profit_gain)

    return {
        "total_records": len(outcomes),
        "brain_decisions": brain_count,
        "human_decisions": human_count,
        "avg_revenue_gain": sum(revenue_gains) / len(revenue_gains)
        if revenue_gains
        else 0,
        "avg_profit_gain": sum(profit_gains) / len(profit_gains) if profit_gains else 0,
        "brain_avg_revenue_gain": sum(brain_revenue_gains) / len(brain_revenue_gains)
        if brain_revenue_gains
        else 0,
        "brain_avg_profit_gain": sum(brain_profit_gains) / len(brain_profit_gains)
        if brain_profit_gains
        else 0,
        "human_avg_revenue_gain": sum(human_revenue_gains) / len(human_revenue_gains)
        if human_revenue_gains
        else 0,
        "human_avg_profit_gain": sum(human_profit_gains) / len(human_profit_gains)
        if human_profit_gains
        else 0,
    }


def clear_real_outcomes():
    with open(PATH, "w") as f:
        json.dump([], f)


def _summarize_decision(decision: Dict) -> Dict:
    if not decision:
        return {}
    return {
        "strategy": decision.get("decision", "")[:100]
        if isinstance(decision, dict)
        else str(decision)[:100],
        "actions": decision.get("actions", [])[:5]
        if isinstance(decision, dict)
        else [],
        "risk_level": decision.get("risk_level", "unknown")
        if isinstance(decision, dict)
        else "unknown",
    }


def compute_prediction_accuracy(window: int = 20) -> Dict:
    outcomes = get_real_outcomes(limit=window)

    if not outcomes:
        return {
            "accuracy": 0,
            "sample_size": 0,
            "avg_error": 0,
        }

    errors = []
    for outcome in outcomes:
        before = outcome.get("before", {})
        after = outcome.get("after", {})

        before_rev = before.get("revenue", 0)
        after_rev = after.get("revenue", 0)
        before_profit = before.get("profit", 0)
        after_profit = after.get("profit", 0)

        actual_rev_change = (
            (after_rev - before_rev) / before_rev if before_rev > 0 else 0
        )
        actual_profit_change = (
            (after_profit - before_profit) / before_profit if before_profit > 0 else 0
        )

        errors.append(
            {
                "revenue_error": abs(actual_rev_change),
                "profit_error": abs(actual_profit_change),
            }
        )

    avg_rev_error = sum(e["revenue_error"] for e in errors) / len(errors)
    avg_profit_error = sum(e["profit_error"] for e in errors) / len(errors)

    accuracy = max(0, 1 - (avg_rev_error + avg_profit_error) / 2)

    return {
        "accuracy": round(accuracy, 4),
        "sample_size": len(outcomes),
        "avg_error": round((avg_rev_error + avg_profit_error) / 2, 4),
        "avg_revenue_error": round(avg_rev_error, 4),
        "avg_profit_error": round(avg_profit_error, 4),
    }
