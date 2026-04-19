import re
import random
from typing import Dict, Any, List


MUTATION_TEMPLATES = [
    "针对本门店客群特征微调套餐定价，测试最优价格区间",
    "引入限时折扣机制作为试点，验证价格弹性",
    "尝试与周边商户异业合作，拓宽引流渠道",
    "针对午市/晚市分别设计差异化运营策略",
    "增加会员积分激励机制，测试复购提升效果",
    "试点预点餐+快速出品模式，验证翻台提升空间",
    "推出季节限定菜品，测试新品带动营收效果",
    "优化等位流程增加候座服务，测试满意度提升",
]


def _extract_metric_focus(decision: Dict[str, Any]) -> List[str]:
    reasoning = decision.get("reasoning", "") + decision.get("problem", "")
    focuses = []
    if any(kw in reasoning for kw in ["客流", "人少", "流量"]):
        focuses.append("客流")
    if any(kw in reasoning for kw in ["客单价", "人均", "单价"]):
        focuses.append("客单价")
    if any(kw in reasoning for kw in ["翻台", "效率", "周转"]):
        focuses.append("翻台率")
    if any(kw in reasoning for kw in ["毛利", "成本"]):
        focuses.append("毛利")
    if any(kw in reasoning for kw in ["包房", "私密"]):
        focuses.append("包房")
    if any(kw in reasoning for kw in ["差评", "投诉", "服务"]):
        focuses.append("服务")
    return focuses if focuses else ["综合经营"]


def mutate_strategy(
    decision: Dict[str, Any],
    store_input=None,
) -> Dict[str, Any]:
    actions = list(decision.get("actions", []))
    original_decision = decision.get("decision", "")
    focuses = _extract_metric_focus(decision)

    new_action_templates = [
        t for t in MUTATION_TEMPLATES if not any(t[:10] in a for a in actions)
    ]
    if not new_action_templates:
        new_action_templates = MUTATION_TEMPLATES

    num_new = random.choice([1, 2])
    random.shuffle(new_action_templates)
    new_actions = actions + new_action_templates[:num_new]

    mutation_desc = random.choice(
        [
            "（探索优化版）",
            "（试点测试版）",
            "（变异测试）",
            "（创新验证）",
        ]
    )

    new_decision = original_decision + mutation_desc

    new_reasoning = decision.get("reasoning", "")
    if len(new_reasoning) > 20:
        new_reasoning = f"[探索] 在原策略基础上增加{num_new}项试点测试，以验证新策略效果。{new_reasoning[:100]}"
    else:
        new_reasoning = f"[探索] 尝试新策略组合，增加试点测试以验证效果。"

    mutated = {
        **decision,
        "actions": new_actions,
        "decision": new_decision,
        "reasoning": new_reasoning,
        "is_exploration": True,
        "mutation_type": "exploration",
        "metric_focus": focuses,
    }

    return mutated


def mutate_by_weakness(
    decision: Dict[str, Any], low_score_areas: List[str] = None
) -> Dict[str, Any]:
    weakness_actions = {
        "客流": "通过限时团购+社交媒体投放，测试客流提升10%以上的可行性",
        "客单价": "通过套餐升级+加价购机制，测试客单价提升15%以上的可行性",
        "翻台率": "通过优化预点餐+快速收台流程，测试翻台率提升20%以上的可行性",
        "毛利": "通过调整菜品结构+高毛利菜推荐，测试毛利率提升5%以上的可行性",
        "服务": "通过增加服务人员培训+服务SOP优化，测试差评率降低50%以上的可行性",
        "包房": "通过包房专属套餐+增值服务，测试包房使用率提升30%以上的可行性",
    }

    actions = list(decision.get("actions", []))
    weaknesses = low_score_areas or []

    new_actions = []
    for area in weaknesses[:2]:
        if area in weakness_actions and weakness_actions[area] not in actions:
            new_actions.append(weakness_actions[area])

    mutated = mutate_strategy(decision)
    mutated["actions"] = actions + new_actions
    mutated["mutation_type"] = "weakness_focused"
    mutated["weakness_areas"] = weaknesses

    return mutated
