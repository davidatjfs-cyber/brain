import re
from typing import Dict, Any


def predict_outcome(
    decision: Dict[str, Any], input_data: Dict[str, Any]
) -> Dict[str, float]:
    from app.model_corrector import get_current_factors
    from app.parameter_store import load_params

    factors = get_current_factors()
    params = load_params()

    rf = factors.get("revenue_factor", 1.0) * params.get("revenue_factor", 1.0)
    pf = factors.get("profit_factor", 1.0) * params.get("profit_factor", 1.0)
    tf = factors.get("turnover_factor", 1.0) * params.get("turnover_factor", 1.0)
    text = (
        decision.get("decision", "")
        + " "
        + decision.get("problem", "")
        + " "
        + " ".join(decision.get("actions", []))
    )
    m = input_data.get("metrics", {})
    scenario = input_data.get("scenario", "")

    revenue_change = 0.0
    turnover_change = 0.0
    profit_change = 0.0

    revenue = m.get("revenue", 0) or 0
    turnover = (
        m.get("turnover", 0) or m.get("turnover_rate", 0) or m.get("翻台率", 0) or 0
    )
    private_room = m.get("包房使用率", 0) or m.get("private_room", 0) or 0

    if "套餐" in text or "套餐" in scenario:
        revenue_change += 0.08
        if "高毛利" in text:
            profit_change += 0.05
        if "引流" in text or "吸引" in text:
            revenue_change += 0.05

    if "翻台" in text or "翻台" in scenario:
        turnover_change += 0.10
        revenue_change += 0.05

    if "降价" in text or "折扣" in text or "优惠" in text:
        revenue_change += 0.03
        profit_change -= 0.05

    if "包房" in text or "包房" in scenario:
        revenue_change += 0.06
        profit_change += 0.03
        if private_room < 0.22:
            revenue_change += 0.08
            profit_change += 0.05

    if "午市" in text or "午餐" in text or "午市" in scenario:
        turnover_change += 0.07
        revenue_change += 0.04

    if "晚市" in text or "晚餐" in text:
        profit_change += 0.04
        revenue_change += 0.05

    if "服务" in text or "差评" in text or "投诉" in scenario:
        revenue_change += 0.05
        profit_change += 0.03

    if "引流" in text or "获客" in text:
        revenue_change += 0.06

    if "预点餐" in text or "快速" in text:
        turnover_change += 0.08

    if "限时" in text or "促销" in text:
        revenue_change += 0.05
        profit_change -= 0.02

    if "会员" in text or "积分" in text:
        revenue_change += 0.03
        profit_change += 0.02

    if "新品" in text or "季节" in text:
        revenue_change += 0.04

    if revenue < 10000:
        revenue_change += 0.03
    if turnover < 1.5:
        turnover_change += 0.03
    if private_room < 0.25:
        revenue_change += 0.02

    revenue_change = round(revenue_change * rf, 4)
    turnover_change = round(turnover_change * tf, 4)
    profit_change = round(profit_change * pf, 4)

    return {
        "revenue_change": revenue_change,
        "turnover_change": turnover_change,
        "profit_change": profit_change,
    }
