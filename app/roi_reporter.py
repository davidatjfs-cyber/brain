import json
import os
import time
from typing import Dict, List, Optional

PATH = "data/roi_logs.json"


def init_roi_logs():
    os.makedirs("data", exist_ok=True)
    try:
        with open(PATH, "r") as f:
            json.load(f)
    except:
        with open(PATH, "w") as f:
            json.dump([], f)


def record_roi_entry(
    shadow_log_id: str, value_result: Dict, roi_result: Dict, real_outcome: Dict = None
) -> str:
    init_roi_logs()

    try:
        with open(PATH, "r") as f:
            data = json.load(f)
    except:
        data = []

    entry = {
        "shadow_log_id": shadow_log_id,
        "timestamp": time.time(),
        "value": value_result,
        "roi": roi_result,
        "real_outcome": real_outcome,
    }

    data.append(entry)

    with open(PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return f"roi_{len(data)}"


def get_roi_entries(limit: int = 100) -> List[Dict]:
    init_roi_logs()
    try:
        with open(PATH, "r") as f:
            data = json.load(f)
        return data[-limit:] if limit > 0 else data
    except:
        return []


def get_roi_stats() -> Dict:
    entries = get_roi_entries(limit=0)

    if not entries:
        return {
            "total_runs": 0,
            "brain_win_count": 0,
            "brain_win_rate": 0.0,
            "avg_revenue_impact": 0.0,
            "total_revenue_gain": 0.0,
            "avg_net_value": 0.0,
            "total_net_value": 0.0,
            "recommendation": "暂无数据",
        }

    total = len(entries)
    wins = sum(1 for e in entries if e.get("value", {}).get("brain_better", False))

    revenue_impacts = [e.get("roi", {}).get("revenue_impact", 0) for e in entries]
    net_values = [e.get("roi", {}).get("net_value", 0) for e in entries]

    avg_revenue = sum(revenue_impacts) / len(revenue_impacts) if revenue_impacts else 0
    total_revenue = sum(revenue_impacts)
    avg_net = sum(net_values) / len(net_values) if net_values else 0
    total_net = sum(net_values)

    recent_10 = entries[-10:] if len(entries) >= 10 else entries
    recent_wins = sum(
        1 for e in recent_10 if e.get("value", {}).get("brain_better", False)
    )
    recent_win_rate = recent_wins / len(recent_10) if recent_10 else 0

    older_10 = entries[:10] if len(entries) >= 10 else entries
    older_wins = sum(
        1 for e in older_10 if e.get("value", {}).get("brain_better", False)
    )
    older_win_rate = older_wins / len(older_10) if older_10 else 0

    if recent_win_rate > older_win_rate + 0.1:
        trend = "improving"
    elif recent_win_rate < older_win_rate - 0.1:
        trend = "declining"
    else:
        trend = "stable"

    verdict_counts = {}
    for e in entries:
        v = e.get("value", {}).get("verdict", "unknown")
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    annualized = total_net * (365 / max(1, len(entries)))

    if annualized > 100000:
        recommendation = "强烈推荐接入生产环境"
        confidence = "high"
    elif annualized > 30000:
        recommendation = "推荐接入，建议持续监控"
        confidence = "medium"
    elif annualized > 0:
        recommendation = "可以小规模试点"
        confidence = "medium"
    else:
        recommendation = "需要优化后再评估"
        confidence = "low"

    return {
        "total_runs": total,
        "brain_win_count": wins,
        "brain_win_rate": round(wins / total, 4) if total > 0 else 0,
        "avg_revenue_impact": round(avg_revenue, 2),
        "total_revenue_gain": round(total_revenue, 2),
        "avg_net_value": round(avg_net, 2),
        "total_net_value": round(total_net, 2),
        "annualized_gain": round(annualized, 2),
        "trend": trend,
        "recent_win_rate": round(recent_win_rate, 4),
        "older_win_rate": round(older_win_rate, 4),
        "verdict_distribution": verdict_counts,
        "recommendation": recommendation,
        "confidence": confidence,
    }


def get_monthly_report() -> Dict:
    entries = get_roi_entries(limit=0)

    if not entries:
        return {
            "month": "N/A",
            "decisions": 0,
            "gain": 0,
            "roi": 0,
        }

    entries_by_day = {}
    for e in entries:
        ts = e.get("timestamp", 0)
        day = time.strftime("%Y-%m", time.localtime(ts))
        if day not in entries_by_day:
            entries_by_day[day] = []
        entries_by_day[day].append(e)

    months = sorted(entries_by_day.keys(), reverse=True)[:3]

    monthly_data = []
    for month in months:
        month_entries = entries_by_day[month]
        net_values = [e.get("roi", {}).get("net_value", 0) for e in month_entries]
        total_gain = sum(net_values)
        decisions = len(month_entries)
        roi = (total_gain / (decisions * 0.5) * 100) if decisions > 0 else 0

        monthly_data.append(
            {
                "month": month,
                "decisions": decisions,
                "gain": round(total_gain, 2),
                "roi": round(roi, 2),
            }
        )

    return {
        "monthly_reports": monthly_data,
        "current_month": monthly_data[0] if monthly_data else None,
    }


def clear_roi_logs():
    with open(PATH, "w") as f:
        json.dump([], f)


def get_roi_summary() -> Dict:
    stats = get_roi_stats()

    return {
        "summary": {
            "total_value": f"{stats.get('total_net_value', 0):,.0f} 元",
            "monthly_value": f"{stats.get('annualized_gain', 0) / 12:,.0f} 元/月"
            if stats.get("annualized_gain", 0) > 0
            else "待积累",
            "win_rate": f"{stats.get('brain_win_rate', 0) * 100:.1f}%",
            "recommendation": stats.get("recommendation", "暂无数据"),
        },
        "stats": stats,
    }
