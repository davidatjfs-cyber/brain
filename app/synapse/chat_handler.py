import json
import time
from typing import Dict, Any

from app.synapse.session_manager import get_session, update_session, clear_session
from app.synapse.orchestrator import classify_intent, extract_store_input
from app.synapse.synapse_engine import (
    greet,
    summon_agent,
    learn_from_interaction,
)
from app.synapse.convener import debate
from app.synapse.agent_manager import (
    find_agent_by_trigger,
    find_agent_by_decision_type,
    load_agents,
)
from app.synapse.pattern_bridge import full_sync
from app.synapse.feedback_loop import auto_learn_from_decision_result

STATES = {
    "GREET": "greet",
    "GATHER": "gather",
    "CONFIRM": "confirm",
    "EXECUTE": "execute",
    "DEBATE": "debate",
    "FOLLOWUP": "followup",
}

GATHER_QUESTIONS = {
    "marketing": [
        "当前日均营收大约多少？",
        "主要客流来源是什么（堂食/外卖/团购）？",
        "有没有做过引流活动，效果如何？",
    ],
    "pricing": [
        "目前客单价大概多少？",
        "整体毛利率大概多少？",
        "有没有在用套餐组合？效果如何？",
    ],
    "menu": [
        "当前菜单SKU大约有多少？",
        "出餐速度如何（平均几分钟）？",
        "哪些菜品是招牌/引流/高毛利？",
    ],
    "operation": [
        "翻台率目前多少？",
        "员工有多少人？流失率高吗？",
        "有没有收到过差评？主要问题是什么？",
    ],
    "general": [
        "你门店目前最头疼的问题是什么？",
        "日均营收和翻台率大概多少？",
        "有没有已经尝试过的改进措施？",
    ],
}


def _detect_domain_from_message(message: str) -> str:
    from app.synapse.orchestrator import DECISION_TYPE_KEYWORDS
    msg_lower = message.lower()
    for dt, keywords in DECISION_TYPE_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            return dt
    return "general"


def _build_gather_questions(domain: str) -> str:
    questions = GATHER_QUESTIONS.get(domain, GATHER_QUESTIONS["general"])
    q_text = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(questions[:3]))
    return f"🧙🏾‍♂️: 在我召唤专家之前，我需要了解一些情况，这样专家才能给出真正适合你的建议——\n\n{q_text}\n\n请回答以上问题，或者直接描述你的具体情况。"


def process_message(message: str, user_id: str = "") -> Dict[str, Any]:
    session = get_session(user_id)
    state = session.get("state", "")
    ctx = session.get("context", {})
    msg_stripped = message.strip()

    skip_commands = ["/save", "/reset", "/restart"]
    if msg_stripped.lower() in skip_commands:
        if msg_stripped.lower() == "/reset" or msg_stripped.lower() == "/restart":
            clear_session(user_id)
            return {
                "type": "greeting",
                "text": greet(user_id),
                "suggestions": _get_suggestion_buttons(),
            }
        if msg_stripped.lower() == "/save":
            summary = _summarize_context(ctx)
            return {
                "type": "save",
                "text": f"🧙🏾‍♂️: 好的，我记录一下我们的进展——\n\n{summary}\n\n继续告诉我你想了解什么？",
            }

    if state == STATES["GATHER"]:
        ctx["user_context"] = ctx.get("user_context", "") + "\n" + message
        domain = ctx.get("domain", "general")
        agent = find_agent_by_decision_type(domain)
        if not agent:
            agent = find_agent_by_trigger(message)
        if not agent:
            agents = load_agents()
            agent = agents[0] if agents else None

        if agent:
            update_session(user_id, STATES["EXECUTE"], {"agent_name": agent["name"]})
            response = summon_agent(agent, message, store_data=_parse_store_from_context(ctx))
            clear_session(user_id)
            return {
                "type": "single_agent",
                "text": f"🧙🏾‍♂️: 好的，基于你描述的情况，我召唤{agent['emoji']} {agent['description']}来帮你——\n\n---\n\n{response}",
                "agent_name": agent["name"],
                "agent_emoji": agent["emoji"],
            }
        clear_session(user_id)
        return {
            "type": "error",
            "text": "🧙🏾‍♂️: 抱歉，我暂时没有找到合适的专家。请重新描述你的需求。",
            "suggestions": _get_suggestion_buttons(),
        }

    if state == STATES["CONFIRM"]:
        if any(kw in msg_stripped for kw in ["好", "对", "是", "没错", "确认", "OK", "ok", "继续", "开始", "可以"]):
            domain = ctx.get("domain", "general")
            agent = find_agent_by_decision_type(domain)
            if agent:
                update_session(user_id, STATES["EXECUTE"], {"agent_name": agent["name"]})
                user_context = ctx.get("user_context", "")
                response = summon_agent(agent, user_context, store_data=_parse_store_from_context(ctx))
                clear_session(user_id)
                return {
                    "type": "single_agent",
                    "text": f"🧙🏾‍♂️: 好的！{agent['emoji']} {agent['description']}已就位——\n\n---\n\n{response}",
                    "agent_name": agent["name"],
                    "agent_emoji": agent["emoji"],
                }
        elif any(kw in msg_stripped for kw in ["不", "改", "换", "其他", "不对", "不是"]):
            clear_session(user_id)
            return {
                "type": "greeting",
                "text": "🧙🏾‍♂️: 没问题，我们重新来。请告诉我你具体需要什么帮助？",
                "suggestions": _get_suggestion_buttons(),
            }
        else:
            ctx["user_context"] = ctx.get("user_context", "") + "\n" + message
            domain = ctx.get("domain", "general")
            agent = find_agent_by_decision_type(domain)
            if agent:
                update_session(user_id, STATES["EXECUTE"], {"agent_name": agent["name"]})
                user_context = ctx.get("user_context", "")
                response = summon_agent(agent, user_context, store_data=_parse_store_from_context(ctx))
                clear_session(user_id)
                return {
                    "type": "single_agent",
                    "text": f"🧙🏾‍♂️: 收到补充信息，{agent['emoji']} {agent['description']}来帮你——\n\n---\n\n{response}",
                    "agent_name": agent["name"],
                    "agent_emoji": agent["emoji"],
                }
            clear_session(user_id)
            return {
                "type": "greeting",
                "text": "🧙🏾‍♂️: 让我们重新开始，请告诉我你需要什么帮助？",
                "suggestions": _get_suggestion_buttons(),
            }

    if state == STATES["DEBATE"]:
        debate_question = ctx.get("debate_question", message)
        debate_result = debate(debate_question)
        clear_session(user_id)
        if debate_result.get("mode") == "debate":
            return {
                "type": "debate",
                "text": _format_debate_result(debate_result),
                "debate_data": debate_result,
            }
        agent = debate_result.get("agent")
        if agent:
            response = summon_agent(agent, debate_question)
            return {
                "type": "single_agent",
                "text": f"🧙🏾‍♂️: {agent['emoji']} {agent['description']}来帮你——\n\n---\n\n{response}",
                "agent_name": agent["name"],
            }
        return {
            "type": "clarify",
            "text": "🧙🏾‍♂️: 请更详细描述你的问题。",
            "suggestions": _get_suggestion_buttons(),
        }

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
            return _handle_brain(store_input, message)
        else:
            return {
                "type": "need_data",
                "text": "🧙🏾‍♂️: 你想做数据驱动的决策？请提供门店数据，或者描述你的门店情况——\n\n比如：日均营收、翻台率、包房使用率、当前最大的经营问题。",
            }

    if intent["intent"] == "debate":
        question = intent.get("question", message)
        domain = _detect_domain_from_message(message)

        questions = GATHER_QUESTIONS.get("general", [])
        q_text = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(questions[:2]))

        update_session(user_id, STATES["DEBATE"], {
            "domain": domain,
            "debate_question": question,
            "user_context": message,
        })
        return {
            "type": "gather",
            "text": f"🧙🏾‍♂️: 这个问题需要多角度分析。在我召集专家辩论之前，能否告诉我——\n\n{q_text}\n\n直接回答，或者说\"跳过\"我直接开始辩论。",
        }

    if intent["intent"] in ("single_agent", "clarify"):
        domain = intent.get("decision_type") or _detect_domain_from_message(message)

        questions = GATHER_QUESTIONS.get(domain, GATHER_QUESTIONS["general"])
        q_text = "\n".join(f"  {i+1}. {q}" for i, q in enumerate(questions[:3]))

        agent = find_agent_by_decision_type(domain) if domain != "general" else find_agent_by_trigger(message)
        agent_desc = f"{agent['emoji']} {agent['description']}" if agent else "专家"

        update_session(user_id, STATES["GATHER"], {
            "domain": domain,
            "agent_name": agent.get("name", "") if agent else "",
            "user_context": message,
        })

        return {
            "type": "gather",
            "text": f"🧙🏾‍♂️: 我准备召唤{agent_desc}来帮你。在此之前，请告诉我——\n\n{q_text}\n\n回答这些问题后，专家才能给出**真正适合你门店**的建议，而不是泛泛而谈。\n\n你也可以直接详细描述你的情况，或者说\"跳过\"直接获取建议。",
        }

    return {
        "type": "greeting",
        "text": greet(user_id),
        "suggestions": _get_suggestion_buttons(),
    }


def _handle_brain(store_input_dict: dict, user_message: str = "") -> dict:
    from app.synapse.synapse_engine import handle_brain_decision
    result = handle_brain_decision(store_input_dict, user_message)
    return {
        "type": "brain_decision",
        "text": _format_brain_result(result),
        "brain_result": result.get("brain_result"),
        "synapse_commentary": result.get("synapse_commentary"),
    }


def _parse_store_from_context(ctx: dict) -> dict:
    import re
    text = ctx.get("user_context", "")
    metrics = {}
    rev = re.search(r'营收[：:\s]*(\d+)', text)
    if rev:
        metrics["revenue"] = float(rev.group(1))
    turn = re.search(r'翻台[率]?[：:\s]*(\d+\.?\d*)', text)
    if turn:
        metrics["turnover"] = float(turn.group(1))
    pr = re.search(r'包房[使用率]*[：:\s]*(\d+\.?\d*)%?', text)
    if pr:
        val = float(pr.group(1))
        metrics["private_room"] = val / 100 if val > 1 else val
    return metrics if metrics else None


def _summarize_context(ctx: dict) -> str:
    domain = ctx.get("domain", "")
    agent = ctx.get("agent_name", "")
    user_ctx = ctx.get("user_context", "")
    lines = []
    if domain:
        lines.append(f"领域: {domain}")
    if agent:
        lines.append(f"专家: {agent}")
    if user_ctx:
        lines.append(f"用户情况: {user_ctx[:200]}")
    return "\n".join(lines) if lines else "暂无上下文"


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