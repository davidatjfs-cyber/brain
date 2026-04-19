from typing import Dict, Optional
from app.reality_logger import log_real_outcome, get_real_outcomes


def track_outcome(
    decision_id: str,
    before_data: Dict,
    after_data: Dict,
    shadow_log_id: str = None,
    is_brain_decision: bool = None,
    real_decision: Dict = None,
) -> Dict:
    roi = calculate_real_roi(before_data, after_data)

    result_id = log_real_outcome(
        decision_id=decision_id,
        before_data=before_data,
        after_data=after_data,
        shadow_log_id=shadow_log_id,
        is_brain_decision=is_brain_decision,
        real_decision=real_decision,
    )

    return {
        "decision_id": decision_id,
        "result_id": result_id,
        "roi": roi,
        "before": before_data,
        "after": after_data,
    }


def calculate_real_roi(before_data: Dict, after_data: Dict) -> Dict:
    revenue_before = before_data.get("revenue", 0)
    profit_before = before_data.get("profit", 0)
    turnover_before = before_data.get("turnover", 0)

    revenue_after = after_data.get("revenue", 0)
    profit_after = after_data.get("profit", 0)
    turnover_after = after_data.get("turnover", 0)

    revenue_diff = revenue_after - revenue_before
    profit_diff = profit_after - profit_before
    turnover_diff = turnover_after - turnover_before

    revenue_change_pct = (
        (revenue_diff / revenue_before * 100) if revenue_before > 0 else 0
    )
    profit_change_pct = (profit_diff / profit_before * 100) if profit_before > 0 else 0

    is_winning = profit_diff > 0

    roi_percentage = (profit_diff / profit_before * 100) if profit_before > 0 else 0

    return {
        "revenue_gain": revenue_diff,
        "profit_gain": profit_diff,
        "turnover_gain": turnover_diff,
        "revenue_change_pct": round(revenue_change_pct, 2),
        "profit_change_pct": round(profit_change_pct, 2),
        "is_winning": is_winning,
        "roi_percentage": round(roi_percentage, 2),
    }


def compare_with_brain_decision(decision_id: str) -> Optional[Dict]:
    outcomes = get_real_outcomes(limit=0)

    target_outcome = None
    for outcome in reversed(outcomes):
        if outcome.get("decision_id") == decision_id:
            target_outcome = outcome
            break

    if not target_outcome:
        return None

    brain_decisions = [
        o
        for o in outcomes
        if o.get("is_brain_decision", False) and o.get("decision_id") != decision_id
    ]
    human_decisions = [
        o
        for o in outcomes
        if not o.get("is_brain_decision", True) and o.get("decision_id") != decision_id
    ]

    brain_avg_profit = 0
    human_avg_profit = 0

    if brain_decisions:
        brain_profits = [
            o.get("after", {}).get("profit", 0) - o.get("before", {}).get("profit", 0)
            for o in brain_decisions
        ]
        brain_avg_profit = sum(brain_profits) / len(brain_profits)

    if human_decisions:
        human_profits = [
            o.get("after", {}).get("profit", 0) - o.get("before", {}).get("profit", 0)
            for o in human_decisions
        ]
        human_avg_profit = sum(human_profits) / len(human_profits)

    target_roi = calculate_real_roi(
        target_outcome.get("before", {}), target_outcome.get("after", {})
    )

    brain_win_rate = (
        sum(
            1
            for o in brain_decisions
            if o.get("after", {}).get("profit", 0)
            > o.get("before", {}).get("profit", 0)
        )
        / len(brain_decisions)
        if brain_decisions
        else 0
    )
    human_win_rate = (
        sum(
            1
            for o in human_decisions
            if o.get("after", {}).get("profit", 0)
            > o.get("before", {}).get("profit", 0)
        )
        / len(human_decisions)
        if human_decisions
        else 0
    )

    return {
        "target_decision": decision_id,
        "target_roi": target_roi,
        "brain_avg_profit_gain": round(brain_avg_profit, 2),
        "human_avg_profit_gain": round(human_avg_profit, 2),
        "brain_win_rate": round(brain_win_rate, 4),
        "human_win_rate": round(human_win_rate, 4),
        "brain_better": brain_avg_profit > human_avg_profit,
        "comparison_summary": _generate_summary(
            target_roi, brain_avg_profit, human_avg_profit
        ),
    }


def _generate_summary(target_roi: Dict, brain_avg: float, human_avg: float) -> str:
    target_profit = target_roi.get("profit_gain", 0)
    target_winning = target_roi.get("is_winning", False)

    if target_winning:
        if brain_avg > human_avg:
            return f"Brain决策盈利{target_profit:.0f}元，超过人类平均{abs(brain_avg - human_avg):.0f}元"
        else:
            return f"Brain决策盈利{target_profit:.0f}元，人类平均盈利{human_avg:.0f}元"
    else:
        if brain_avg < human_avg:
            return f"Brain决策亏损{abs(target_profit):.0f}元，优于人类平均亏损"
        else:
            return f"Brain决策亏损{abs(target_profit):.0f}元，不如人类平均表现"
