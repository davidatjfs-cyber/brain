import json
import time
from typing import Dict, Any

from app.synapse.orchestrator import classify_intent, extract_store_input
from app.synapse.synapse_engine import (
    greet,
    gather_context_and_route,
    handle_single_agent,
    handle_brain_decision,
)
from app.synapse.convener import debate
from app.synapse.agent_manager import find_agent_by_decision_type, load_agents
from app.synapse.pattern_bridge import full_sync
from app.synapse.feedback_loop import auto_learn_from_decision_result


def process_message(message: str, user_id: str = "") -> Dict[str, Any]:
    intent = classify_intent(message)

    if intent["intent"] in ("synapse_general", "clarify") and intent["confidence"] < 0.4:
        return {
            "type": "greeting",
            "text": greet(user_id),
            "suggestions": _get_suggestion_buttons(),
        }

    if intent["intent"] == "brain_decision":
        store_input = extract_store_input(message)
        if store_input:
            result = handle_brain_decision(store_input, message)
            return {
                "type": "brain_decision",
                "text": _format_brain_result(result),
                "brain_result": result.get("brain_result"),
                "synapse_commentary": result.get("synapse_commentary"),
            }
        else:
            return {
                "type": "need_data",
                "text": "🧙🏾‍♂️: 请提供门店数据以便做出决策。你可以发送JSON格式的数据，或描述你的门店情况（如：营收xxx，翻台率x.x，包房使用率xx%）。",
            }

    if intent["intent"] == "debate":
        debate_result = debate(message)
        if debate_result.get("mode") == "single_agent":
            agent = debate_result.get("agent")
            if agent:
                single_result = handle_single_agent(message, agent)
                return {
                    "type": "single_agent",
                    "text": single_result["response"],
                    "agent_name": single_result["agent_name"],
                }
            return {
                "type": "no_agent",
                "text": "🧙🏾‍♂️: 我暂时没有找到合适的专家，请描述更具体的需求。",
            }
        return {
            "type": "debate",
            "text": _format_debate_result(debate_result),
            "debate_data": debate_result,
        }

    if intent["intent"] == "single_agent":
        dt = intent.get("decision_type")
        agent = find_agent_by_decision_type(dt) if dt else None
        if not agent:
            route = gather_context_and_route(message)
            agent = route.get("agent")
        if agent:
            result = handle_single_agent(message, agent)
            return {
                "type": "single_agent",
                "text": result["response"],
                "agent_name": result["agent_name"],
                "agent_emoji": result["agent_emoji"],
            }
        return {
            "type": "clarify",
            "text": "🧙🏾‍♂️: 请告诉我你具体需要哪个方面的帮助？",
            "suggestions": _get_suggestion_buttons(),
        }

    if intent["intent"] == "clarify":
        return {
            "type": "clarify",
            "text": "🧙🏾‍♂️: 我需要更好地理解你的需求。请描述你遇到的具体问题。",
            "suggestions": _get_suggestion_buttons(),
        }

    return {
        "type": "greeting",
        "text": greet(user_id),
        "suggestions": _get_suggestion_buttons(),
    }


def _get_suggestion_buttons() -> list:
    agents = load_agents()
    buttons = []
    for agent in agents:
        buttons.append({
            "text": f"{agent['emoji']} {agent['description']}",
            "value": f"我需要{agent['description']}的帮助",
        })
    buttons.append({
        "text": "📊 输入门店数据做决策",
        "value": "我有门店数据需要做决策",
    })
    buttons.append({
        "text": "⚖️ 多角度辩论分析",
        "value": "帮我从多个角度分析一下",
    })
    return buttons


def _format_brain_result(result: dict) -> str:
    brain = result.get("brain_result", {})
    decision = brain.get("decision", {})

    lines = [
        "🧙🏾‍♂️: Brain决策系统已生成方案——",
        f"\n📋 **决策**: {decision.get('decision', 'N/A')}",
        f"📌 **类型**: {decision.get('decision_type', 'N/A')}",
        f"⚡ **置信度**: {decision.get('confidence', 0):.2f}",
        f"⚠️ **风险**: {decision.get('risk_level', 'N/A')}",
        f"\n📝 **执行动作**:",
    ]
    for i, action in enumerate(decision.get("actions", []), 1):
        lines.append(f"  {i}. {action}")

    lines.append(f"\n🎯 **预期效果**: {decision.get('expected_impact', 'N/A')}")

    commentary = result.get("synapse_commentary", "")
    if commentary:
        lines.append(f"\n---\n\n{commentary}")

    return "\n".join(lines)


def _format_debate_result(debate_data: dict) -> str:
    lines = [
        f"🧙🏾‍♂️: 我召集了{len(debate_data.get('agents', []))}位专家进行辩论——",
    ]

    for agent in debate_data.get("agents", []):
        lines.append(f"\n{agent['emoji']} **{agent['description']}**")

    for round_data in debate_data.get("rounds", []):
        lines.append(f"\n--- 轮次 {round_data['round']} ---")
        for stmt in round_data.get("statements", []):
            lines.append(f"{stmt['agent_emoji']}: {stmt['text'][:200]}")

    lines.append(f"\n--- 综合分析 ---")
    lines.append(debate_data.get("synthesis", ""))

    return "\n".join(lines)


def handle_evaluation_feedback(decision_id: str, eval_score: float, decision_type: str) -> Dict[str, Any]:
    learn_result = auto_learn_from_decision_result(decision_id, eval_score, decision_type)
    try:
        sync_result = full_sync()
    except Exception:
        sync_result = {"error": "sync failed"}
    return {
        "learning": learn_result,
        "sync": sync_result,
    }