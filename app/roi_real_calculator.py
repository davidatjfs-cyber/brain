from typing import Dict, List
from app.reality_logger import get_real_outcomes, get_real_outcomes_stats


def calculate_real_roi_summary() -> Dict:
    outcomes = get_real_outcomes(limit=0)
    stats = get_real_outcomes_stats()

    if not outcomes:
        return {
            "total_records": 0,
            "total_revenue_gain": 0,
            "total_profit_gain": 0,
            "avg_gain": 0,
            "win_rate": 0,
            "recommendation": "暂无真实数据",
        }

    total_revenue_gain = 0
    total_profit_gain = 0
    winning_count = 0

    brain_outcomes = []
    human_outcomes = []

    for outcome in outcomes:
        before = outcome.get("before", {})
        after = outcome.get("after", {})

        rev_gain = after.get("revenue", 0) - before.get("revenue", 0)
        profit_gain = after.get("profit", 0) - before.get("profit", 0)

        total_revenue_gain += rev_gain
        total_profit_gain += profit_gain

        if profit_gain > 0:
            winning_count += 1

        if outcome.get("is_brain_decision", False):
            brain_outcomes.append(outcome)
        else:
            human_outcomes.append(outcome)

    total = len(outcomes)
    win_rate = winning_count / total if total > 0 else 0
    avg_gain = total_profit_gain / total if total > 0 else 0

    brain_wins = sum(
        1
        for o in brain_outcomes
        if (o.get("after", {}).get("profit", 0) - o.get("before", {}).get("profit", 0))
        > 0
    )
    human_wins = sum(
        1
        for o in human_outcomes
        if (o.get("after", {}).get("profit", 0) - o.get("before", {}).get("profit", 0))
        > 0
    )

    brain_win_rate = brain_wins / len(brain_outcomes) if brain_outcomes else 0
    human_win_rate = human_wins / len(human_outcomes) if human_outcomes else 0

    brain_total_gain = sum(
        o.get("after", {}).get("profit", 0) - o.get("before", {}).get("profit", 0)
        for o in brain_outcomes
    )
    human_total_gain = sum(
        o.get("after", {}).get("profit", 0) - o.get("before", {}).get("profit", 0)
        for o in human_outcomes
    )

    if brain_outcomes:
        brain_avg_gain = brain_total_gain / len(brain_outcomes)
    else:
        brain_avg_gain = 0

    if human_outcomes:
        human_avg_gain = human_total_gain / len(human_outcomes)
    else:
        human_avg_gain = 0

    brain_total_revenue = sum(
        o.get("after", {}).get("revenue", 0) - o.get("before", {}).get("revenue", 0)
        for o in brain_outcomes
    )
    human_total_revenue = sum(
        o.get("after", {}).get("revenue", 0) - o.get("before", {}).get("revenue", 0)
        for o in human_outcomes
    )

    monthly_estimate = avg_gain * 30
    yearly_estimate = avg_gain * 365

    recommendation = _generate_recommendation(
        win_rate=win_rate,
        avg_gain=avg_gain,
        brain_win_rate=brain_win_rate,
        human_win_rate=human_win_rate,
        brain_avg_gain=brain_avg_gain,
        human_avg_gain=human_avg_gain,
    )

    return {
        "total_records": total,
        "total_revenue_gain": round(total_revenue_gain, 2),
        "total_profit_gain": round(total_profit_gain, 2),
        "avg_gain": round(avg_gain, 2),
        "win_rate": round(win_rate, 4),
        "brain": {
            "count": len(brain_outcomes),
            "win_count": brain_wins,
            "win_rate": round(brain_win_rate, 4),
            "total_gain": round(brain_total_gain, 2),
            "avg_gain": round(brain_avg_gain, 2),
            "total_revenue_gain": round(brain_total_revenue, 2),
        },
        "human": {
            "count": len(human_outcomes),
            "win_count": human_wins,
            "win_rate": round(human_win_rate, 4),
            "total_gain": round(human_total_gain, 2),
            "avg_gain": round(human_avg_gain, 2),
            "total_revenue_gain": round(human_total_revenue, 2),
        },
        "comparison": {
            "brain_better": brain_avg_gain > human_avg_gain,
            "brain_vs_human_gain": round(brain_avg_gain - human_avg_gain, 2),
            "brain_vs_human_win_rate": round(brain_win_rate - human_win_rate, 4),
        },
        "estimates": {
            "monthly_gain": round(monthly_estimate, 2),
            "yearly_gain": round(yearly_estimate, 2),
        },
        "recommendation": recommendation,
    }


def get_top_performers(limit: int = 5) -> List[Dict]:
    outcomes = get_real_outcomes(limit=0)

    performers = []
    for outcome in outcomes:
        before = outcome.get("before", {})
        after = outcome.get("after", {})

        profit_gain = after.get("profit", 0) - before.get("profit", 0)
        revenue_gain = after.get("revenue", 0) - before.get("revenue", 0)

        performers.append(
            {
                "decision_id": outcome.get("decision_id"),
                "profit_gain": profit_gain,
                "revenue_gain": revenue_gain,
                "is_brain": outcome.get("is_brain_decision", False),
                "timestamp": outcome.get("timestamp"),
            }
        )

    performers.sort(key=lambda x: x["profit_gain"], reverse=True)
    return performers[:limit]


def _generate_recommendation(
    win_rate: float,
    avg_gain: float,
    brain_win_rate: float,
    human_win_rate: float,
    brain_avg_gain: float,
    human_avg_gain: float,
) -> str:
    if win_rate < 0.3:
        return "⚠️ 整体胜率过低，建议暂停使用 Brain，全面复盘问题"

    if brain_avg_gain > human_avg_gain and brain_win_rate > human_win_rate:
        if brain_avg_gain - human_avg_gain > 1000:
            return "🟢 Brain显著优于人类，建议全面接管决策"
        else:
            return "🟢 Brain优于人类，建议逐步扩大使用范围"

    if brain_avg_gain > human_avg_gain:
        return "🟡 Brain盈利能力略优，建议扩大试点"

    if brain_win_rate > human_win_rate:
        return "🟡 Brain胜率略高，建议继续观察"

    if brain_avg_gain < human_avg_gain:
        if brain_win_rate >= human_win_rate:
            return "🟠 Brain胜率相当但盈利略低，建议优化策略"
        else:
            return "🔴 Brain表现不如人类，建议暂缓接入"

    return "🟡 数据不足，建议继续积累数据"


def calculate_decision_roi(before: Dict, after: Dict) -> Dict:
    revenue_before = before.get("revenue", 0)
    profit_before = before.get("profit", 0)
    turnover_before = before.get("turnover", 0)

    revenue_after = after.get("revenue", 0)
    profit_after = after.get("profit", 0)
    turnover_after = after.get("turnover", 0)

    revenue_diff = revenue_after - revenue_before
    profit_diff = profit_after - profit_before
    turnover_diff = turnover_after - turnover_before

    roi = (profit_diff / profit_before * 100) if profit_before > 0 else 0

    return {
        "revenue_gain": revenue_diff,
        "profit_gain": profit_diff,
        "turnover_gain": turnover_diff,
        "roi_percentage": round(roi, 2),
        "is_profitable": profit_diff > 0,
    }
