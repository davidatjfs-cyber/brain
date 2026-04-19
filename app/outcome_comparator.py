from typing import Dict, Any, Tuple


def compare(
    predicted: Dict[str, float],
    real: Dict[str, float],
) -> Dict[str, float]:
    return {
        "revenue_error": real.get("revenue_change", real.get("revenue", 0))
        - predicted.get("revenue_change", 0),
        "profit_error": real.get("profit_change", real.get("profit", 0))
        - predicted.get("profit_change", 0),
        "turnover_error": real.get("turnover_change", real.get("turnover", 0))
        - predicted.get("turnover_change", 0),
    }


def compute_error_stats(errors: list) -> Dict[str, Any]:
    if not errors:
        return {"count": 0, "avg": {}, "trend": "no_data"}

    rev_errors = [e.get("revenue_error", 0) for e in errors if "revenue_error" in e]
    pro_errors = [e.get("profit_error", 0) for e in errors if "profit_error" in e]
    tur_errors = [e.get("turnover_error", 0) for e in errors if "turnover_error" in e]

    avg_rev = sum(rev_errors) / len(rev_errors) if rev_errors else 0
    avg_pro = sum(pro_errors) / len(pro_errors) if pro_errors else 0
    avg_tur = sum(tur_errors) / len(tur_errors) if tur_errors else 0

    if len(errors) >= 4:
        first_half = errors[: len(errors) // 2]
        second_half = errors[len(errors) // 2 :]
        first_avg = sum(e.get("revenue_error", 0) for e in first_half) / len(first_half)
        second_avg = sum(e.get("revenue_error", 0) for e in second_half) / len(
            second_half
        )
        trend = (
            "improving"
            if abs(second_avg) < abs(first_avg)
            else ("worsening" if abs(second_avg) > abs(first_avg) * 1.1 else "stable")
        )
    else:
        trend = "insufficient_data"

    return {
        "count": len(errors),
        "avg_revenue_error": round(avg_rev, 4),
        "avg_profit_error": round(avg_pro, 4),
        "avg_turnover_error": round(avg_tur, 4),
        "revenue_overestimate": avg_rev < 0,
        "revenue_underestimate": avg_rev > 0,
        "trend": trend,
        "first_half_avg": round(
            sum(e.get("revenue_error", 0) for e in errors[: len(errors) // 2])
            / max(len(errors[: len(errors) // 2]), 1),
            4,
        )
        if len(errors) >= 2
        else 0,
        "second_half_avg": round(
            sum(e.get("revenue_error", 0) for e in errors[len(errors) // 2 :])
            / max(len(errors[len(errors) // 2 :]), 1),
            4,
        )
        if len(errors) >= 2
        else 0,
    }


def is_significant_error(error: float, threshold: float = 0.1) -> bool:
    return abs(error) > threshold


def get_direction(error: float) -> str:
    if error > 0.05:
        return "underestimate"
    elif error < -0.05:
        return "overestimate"
    return "accurate"
