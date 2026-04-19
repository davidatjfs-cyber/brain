import os
import json
from typing import Dict, Any, Optional

STATE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "correction_state.json"
)

REVENUE_FACTOR = 1.0
PROFIT_FACTOR = 1.0
TURNOVER_FACTOR = 1.0

ADJUSTMENT_STEP = 0.05
MAX_FACTOR = 1.3
MIN_FACTOR = 0.5


def _load_state() -> Dict[str, Any]:
    if not os.path.exists(STATE_FILE):
        return {
            "revenue_factor": 1.0,
            "profit_factor": 1.0,
            "turnover_factor": 1.0,
            "corrections": 0,
            "total_adjustments": 0,
        }
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "revenue_factor": 1.0,
            "profit_factor": 1.0,
            "turnover_factor": 1.0,
            "corrections": 0,
            "total_adjustments": 0,
        }


def _save_state(state: Dict[str, Any]):
    with open(STATE_FILE, "w", encoding="utf-8") as fp:
        json.dump(state, fp, ensure_ascii=False, indent=2)


def get_current_factors() -> Dict[str, float]:
    state = _load_state()
    return {
        "revenue_factor": state.get("revenue_factor", 1.0),
        "profit_factor": state.get("profit_factor", 1.0),
        "turnover_factor": state.get("turnover_factor", 1.0),
    }


def adjust_prediction_rules(errors: Dict[str, float]) -> Dict[str, float]:
    state = _load_state()
    adjustments = {}

    rev_error = errors.get("revenue_error", 0)
    pro_error = errors.get("profit_error", 0)
    tur_error = errors.get("turnover_error", 0)

    rev_factor = state.get("revenue_factor", 1.0)
    pro_factor = state.get("profit_factor", 1.0)
    tur_factor = state.get("turnover_factor", 1.0)

    if rev_error < -0.05:
        rev_factor = max(MIN_FACTOR, rev_factor - ADJUSTMENT_STEP)
        adjustments["revenue_factor"] = round(rev_factor, 4)
    elif rev_error > 0.05:
        rev_factor = min(MAX_FACTOR, rev_factor + ADJUSTMENT_STEP)
        adjustments["revenue_factor"] = round(rev_factor, 4)

    if pro_error < -0.03:
        pro_factor = max(MIN_FACTOR, pro_factor - ADJUSTMENT_STEP)
        adjustments["profit_factor"] = round(pro_factor, 4)
    elif pro_error > 0.03:
        pro_factor = min(MAX_FACTOR, pro_factor + ADJUSTMENT_STEP)
        adjustments["profit_factor"] = round(pro_factor, 4)

    if abs(tur_error) > 0.05:
        if tur_error < 0:
            tur_factor = max(MIN_FACTOR, tur_factor - ADJUSTMENT_STEP)
        else:
            tur_factor = min(MAX_FACTOR, tur_factor + ADJUSTMENT_STEP)
        adjustments["turnover_factor"] = round(tur_factor, 4)

    if adjustments:
        state["revenue_factor"] = adjustments.get("revenue_factor", rev_factor)
        state["profit_factor"] = adjustments.get("profit_factor", pro_factor)
        state["turnover_factor"] = adjustments.get("turnover_factor", tur_factor)
        state["corrections"] += 1
        state["total_adjustments"] += len(adjustments)
        _save_state(state)

    return adjustments


def apply_adjustments(adjustments: Dict[str, float]):
    global REVENUE_FACTOR, PROFIT_FACTOR, TURNOVER_FACTOR
    if "revenue_factor" in adjustments:
        REVENUE_FACTOR = adjustments["revenue_factor"]
    if "profit_factor" in adjustments:
        PROFIT_FACTOR = adjustments["profit_factor"]
    if "turnover_factor" in adjustments:
        TURNOVER_FACTOR = adjustments["turnover_factor"]


def get_correction_status() -> Dict[str, Any]:
    state = _load_state()
    factors = get_current_factors()
    return {
        "current_factors": factors,
        "corrections": state.get("corrections", 0),
        "total_adjustments": state.get("total_adjustments", 0),
        "revenue_well_tuned": 0.85 <= factors["revenue_factor"] <= 1.15,
        "profit_well_tuned": 0.85 <= factors["profit_factor"] <= 1.15,
        "is_converged": state.get("corrections", 0) >= 3
        and abs(factors["revenue_factor"] - 1.0) < 0.1,
    }


def reset_factors():
    global REVENUE_FACTOR, PROFIT_FACTOR, TURNOVER_FACTOR
    REVENUE_FACTOR = 1.0
    PROFIT_FACTOR = 1.0
    TURNOVER_FACTOR = 1.0
    _save_state(
        {
            "revenue_factor": 1.0,
            "profit_factor": 1.0,
            "turnover_factor": 1.0,
            "corrections": 0,
            "total_adjustments": 0,
        }
    )
