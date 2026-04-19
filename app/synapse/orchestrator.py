import re
from typing import Dict, Any, Optional


SYNAPSE_KEYWORDS = [
    "帮我分析", "帮我看看", "我需要", "帮我想", "请教", "指导",
    "专家", "怎么看", "建议", "如何", "怎么办", "怎么办呢",
    "分析一下", "评估", "有什么建议", "帮我决策", "帮忙决策",
    "哪个更好", "选哪个", "应该怎么", "怎样", "怎样做",
    "你好", "嗨", "hello", "hi",
]

DEBATE_KEYWORDS = [
    "比较", "对比", "辩论", "权衡", "纠结", "两难",
    "A还是B", "哪个好", "怎么选", "选择困难", "取舍",
    "冲突", "矛盾", "平衡",
]

BRAIN_KEYWORDS = [
    "门店数据", "输入数据", "做决策", "决策数据",
    "metrics", "menu", "feedback", "store_id",
    "生成决策", "给我方案", "出决策",
]

DECISION_TYPE_KEYWORDS = {
    "marketing": ["营销", "引流", "拉新", "促销", "获客", "团购", "会员", "推广", "广告", "曝光", "客流"],
    "pricing": ["定价", "价格", "折扣", "优惠", "套餐价", "毛利", "成本", "涨价", "降价", "性价比"],
    "menu": ["菜单", "SKU", "菜品", "出品", "上新", "季节", "淘汰", "推荐菜", "招牌"],
    "operation": ["运营", "翻台", "流程", "员工", "培训", "差评", "投诉", "服务", "排班", "管理", "效率"],
}


def classify_intent(message: str) -> Dict[str, Any]:
    msg_lower = message.lower().strip()

    is_json = False
    try:
        import json
        parsed = json.loads(message)
        if isinstance(parsed, dict) and "store_id" in parsed:
            is_json = True
    except (json.JSONDecodeError, ValueError):
        pass

    if is_json:
        return {"intent": "brain_decision", "confidence": 1.0, "data_type": "json"}

    if any(kw in msg_lower for kw in BRAIN_KEYWORDS):
        return {"intent": "brain_decision", "confidence": 0.8, "data_type": "text"}

    for kw in DEBATE_KEYWORDS:
        if kw in msg_lower:
            return {"intent": "debate", "confidence": 0.85, "question": message}

    matched_types = []
    for dt, keywords in DECISION_TYPE_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            matched_types.append(dt)

    if any(kw in msg_lower for kw in SYNAPSE_KEYWORDS):
        if len(matched_types) >= 2:
            return {"intent": "debate", "confidence": 0.7, "question": message}
        elif len(matched_types) == 1:
            return {"intent": "single_agent", "confidence": 0.8, "decision_type": matched_types[0]}
        else:
            return {"intent": "clarify", "confidence": 0.5}

    if matched_types:
        if len(matched_types) >= 2:
            return {"intent": "debate", "confidence": 0.6, "question": message}
        return {"intent": "single_agent", "confidence": 0.6, "decision_type": matched_types[0]}

    return {"intent": "synapse_general", "confidence": 0.3}


def extract_store_input(message: str) -> Optional[Dict[str, Any]]:
    import json
    try:
        parsed = json.loads(message)
        if isinstance(parsed, dict) and "store_id" in parsed:
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    metrics = {}
    revenue_match = re.search(r'营收[：:\s]*(\d+)', message)
    if revenue_match:
        metrics["revenue"] = float(revenue_match.group(1))
    turnover_match = re.search(r'翻台[率]?[：:\s]*(\d+\.?\d*)', message)
    if turnover_match:
        metrics["turnover"] = float(turnover_match.group(1))
    private_match = re.search(r'包房[使用率]*[：:\s]*(\d+\.?\d*)%?', message)
    if private_match:
        metrics["private_room"] = float(private_match.group(1)) / 100 if float(private_match.group(1)) > 1 else float(private_match.group(1))

    if metrics:
        return {
            "store_id": "feishu_user",
            "date": "today",
            "metrics": metrics,
            "menu": [],
            "feedback": [],
            "scenario": message,
        }
    return None