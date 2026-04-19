import json
import re
import time
from typing import Dict, Any, List, Optional

from app.llm_client import call_llm, extract_json
from app.synapse.agent_manager import (
    find_agent_by_trigger,
    find_agent_by_decision_type,
    load_agents,
    load_learned_patterns,
    add_global_pattern,
    create_agent,
)
from app.synapse.config import MAX_DEBATE_ROUNDS


def _build_agent_system_prompt(agent: dict) -> str:
    patterns = load_learned_patterns()
    effective_global = patterns.get("effective", [])
    anti_global = patterns.get("anti", [])
    agent_effective = agent.get("learned_patterns", {}).get("effective", [])
    agent_anti = agent.get("learned_patterns", {}).get("anti", [])

    ep_text = ""
    for p in (effective_global + agent_effective)[:5]:
        ep_text += f"- {p.get('what_worked', p.get('description', ''))}\n"
    ap_text = ""
    for p in (anti_global + agent_anti)[:5]:
        ap_text += f"- {p.get('the_mistake', p.get('description', ''))}\n"

    return f"""你是{agent['emoji']} {agent['description']}。

## 你的专长
- 领域: {agent.get('domain', '')}
- 核心技术: {agent.get('techniques', '')}
- 关键框架: {agent.get('frameworks', '')}

## 背景理解
{agent.get('context', '')}

## 你的使命
{agent.get('mission', '')}

## 行动步骤
{json.dumps(agent.get('instructions', []), ensure_ascii=False)}

## 行为规范
{json.dumps(agent.get('guidelines', []), ensure_ascii=False)}

## 有效模式（已验证可行）
{ep_text or '暂无'}

## 反模式（必须避免）
{ap_text or '暂无'}

## 回答要求
- 用{agent['emoji']}开头
- 必须给出具体可执行的建议，禁止空话
- 量化预期效果
- 如果不确定，明确说明不确定性
- 保持在200字以内"""


def summon_agent(agent: dict, user_task: str, store_data: dict = None) -> str:
    system = _build_agent_system_prompt(agent)
    user_msg = f"用户需求: {user_task}"
    if store_data:
        user_msg += f"\n\n门店数据:\n{json.dumps(store_data, ensure_ascii=False)[:2000]}"

    prompt = f"{system}\n\n---\n\n{user_msg}"
    return call_llm(prompt)


def greet(user_name: str = "") -> str:
    return f"🧙🏾‍♂️: 你好{' ' + user_name if user_name else ''}！我是Professor Synapse，你的专家向导。\n\n我可以为你召唤餐饮经营的专业Agent来帮助你。告诉我，你今天需要什么帮助？"


def gather_context_and_route(user_message: str, store_data: dict = None) -> dict:
    agent = find_agent_by_trigger(user_message)

    if not agent:
        agents = load_agents()
        agent_names = ", ".join(f"{a['emoji']} {a['description']}" for a in agents)
        return {
            "path": "clarify",
            "response": f"🧙🏾‍♂️: 我需要更好地理解你的需求。你是在问关于以下哪个方面？\n\n{agent_names}\n\n请告诉我更具体的需求。",
            "agent": None,
        }

    return {
        "path": "single_agent",
        "agent": agent,
    }


def handle_single_agent(user_message: str, agent: dict, store_data: dict = None) -> dict:
    response = summon_agent(agent, user_message, store_data)

    return {
        "path": "single_agent",
        "agent_name": agent["name"],
        "agent_emoji": agent["emoji"],
        "agent_description": agent["description"],
        "response": f"🧙🏾‍♂️: 我为你召唤了{agent['emoji']} {agent['description']}。\n\n---\n\n{response}",
    }


def handle_brain_decision(store_input_dict: dict, user_message: str = "") -> dict:
    from app.brain_core import make_decision
    from app.models import StoreInput

    agent = find_agent_by_trigger(user_message)
    decision_type = None
    if agent:
        decision_type = agent.get("decision_type")

    store_input = StoreInput(**store_input_dict)
    result = make_decision(store_input)

    decision = result.get("decision", {})
    actual_type = decision.get("decision_type", "")

    synapse_agent = find_agent_by_decision_type(actual_type)
    agent_commentary = ""
    if synapse_agent:
        try:
            agent_commentary = summon_agent(
                synapse_agent,
                f"Brain决策系统给出了以下决策，请从你的专业角度点评：\n决策: {decision.get('decision', '')}\n动作: {decision.get('actions', [])}",
                store_input_dict,
            )
        except Exception:
            agent_commentary = ""

    emoji_prefix = f"{synapse_agent['emoji']}: " if synapse_agent else ""
    if agent_commentary:
        agent_commentary = f"\n\n---\n\n{emoji_prefix}{agent_commentary}"

    return {
        "path": "brain_decision",
        "brain_result": result,
        "synapse_commentary": agent_commentary,
        "matched_agent": synapse_agent.get("name") if synapse_agent else None,
    }


def learn_from_interaction(agent_name: str, interaction_type: str, insight: dict):
    if interaction_type == "effective":
        add_global_pattern("effective", insight)
        from app.synapse.agent_manager import update_agent_patterns
        update_agent_patterns(agent_name, "effective", insight)
    elif interaction_type == "anti":
        add_global_pattern("anti", insight)
        from app.synapse.agent_manager import update_agent_patterns
        update_agent_patterns(agent_name, "anti", insight)