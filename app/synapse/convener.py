import json
import time
from typing import Dict, Any, List

from app.llm_client import call_llm
from app.synapse.agent_manager import (
    find_agent_by_trigger,
    find_agent_by_decision_type,
    load_agents,
)
from app.synapse.config import MAX_DEBATE_ROUNDS, MAX_AGENTS_IN_DEBATE


def identify_perspectives(question: str) -> List[dict]:
    all_agents = load_agents()
    relevant = []
    for agent in all_agents:
        triggers = [t.strip().lower() for t in agent.get("triggers", "").split(",")]
        question_lower = question.lower()
        if any(t in question_lower for t in triggers):
            relevant.append(agent)
    if not relevant:
        relevant = all_agents[:MAX_AGENTS_IN_DEBATE]
    return relevant[:MAX_AGENTS_IN_DEBATE]


def _build_debate_prompt(agent: dict, question: str, round_num: int, previous_statements: List[str]) -> str:
    prev_text = ""
    if previous_statements:
        prev_text = "\n\n【前几轮发言】\n" + "\n".join(previous_statements[-4:])

    round_instruction = ""
    if round_num == 1:
        round_instruction = "请给出你的立场和核心观点。"
    elif round_num < MAX_DEBATE_ROUNDS:
        round_instruction = "请回应其他专家的观点，指出你同意或不同意的地方，并补充论据。"
    else:
        round_instruction = "请做最终总结，清晰说明你的主张和让步条件。"

    return f"""你是{agent['emoji']} {agent['description']}。

你的专长领域: {agent.get('domain', '')}
核心技术: {agent.get('techniques', '')}
行为规范: {json.dumps(agent.get('guidelines', []), ensure_ascii=False)}

{prev_text}

辩论问题: {question}

{round_instruction}

要求：
- 用{agent['emoji']}开头
- 150字以内
- 必须具体，禁止空话
- 如果同意其他专家，明确说明；如果不同意，给出理由"""


def _run_debate_round(agents: List[dict], question: str, round_num: int, all_statements: List[str]) -> List[dict]:
    round_statements = []
    for agent in agents:
        statements_for_agent = [s["text"] for s in all_statements[-4:]] if all_statements else []
        prompt = _build_debate_prompt(agent, question, round_num, statements_for_agent)
        try:
            response = call_llm(prompt)
        except Exception:
            response = f"{agent['emoji']}: 因网络问题暂时无法发言"
        statement = {
            "agent_name": agent["name"],
            "agent_emoji": agent["emoji"],
            "agent_description": agent["description"],
            "text": response[:500],
            "round": round_num,
        }
        round_statements.append(statement)
        all_statements.append(statement)
    return round_statements


def _synthesize_debate(question: str, all_statements: List[dict]) -> str:
    statements_text = ""
    for s in all_statements:
        statements_text += f"{s['agent_emoji']}({s['agent_name']}): {s['text'][:200]}\n"

    prompt = f"""你是🧙🏾‍♂️ Professor Synapse，你刚主持了一场专家辩论。

辩论问题: {question}

各专家发言:
{statements_text}

请综合辩论内容：
1. 列出所有专家的共识点
2. 列出核心分歧
3. 给出2-3个可选方案，每个方案标注利弊
4. 如果有明确推荐方案，说明理由

保持在300字以内。"""

    try:
        return call_llm(prompt)
    except Exception:
        return "辩论综合分析暂时不可用，请根据以上各专家发言自行判断。"


def simulate_stance(agents: List[dict], question: str, store_data: dict = None) -> List[dict]:
    from app.simulator import simulate
    from app.outcome_predictor import predict_outcome

    results = []
    for agent in agents:
        stance_prompt = f"""作为{agent['emoji']} {agent['description']}，
针对问题: {question}
给出你的核心立场（一句话，30字以内）。"""
        try:
            stance = call_llm(stance_prompt)
        except Exception:
            stance = "无法获取立场"
        results.append({
            "agent_name": agent["name"],
            "agent_emoji": agent["emoji"],
            "stance": stance[:100],
        })
    return results


def debate(question: str, store_data: dict = None) -> Dict[str, Any]:
    agents = identify_perspectives(question)
    if len(agents) < 2:
        return {
            "mode": "single_agent",
            "agent": agents[0] if agents else None,
            "reason": "问题只涉及单一领域，无需辩论",
        }

    all_statements = []
    rounds = []

    for r in range(1, MAX_DEBATE_ROUNDS + 1):
        round_result = _run_debate_round(agents, question, r, all_statements)
        rounds.append({
            "round": r,
            "statements": round_result,
        })

    synthesis = _synthesize_debate(question, all_statements)

    agreement_points = []
    disagreement_points = []

    for statement in all_statements:
        text = statement["text"]
        if any(kw in text for kw in ["同意", "认同", "赞同"]):
            agreement_points.append(f"{statement['agent_emoji']}: {text[:100]}")
        if any(kw in text for kw in ["不同意", "反对", "但是", "然而"]):
            disagreement_points.append(f"{statement['agent_emoji']}: {text[:100]}")

    return {
        "mode": "debate",
        "question": question,
        "agents": [{"name": a["name"], "emoji": a["emoji"], "description": a["description"]} for a in agents],
        "rounds": rounds,
        "synthesis": synthesis,
        "agreement_points": agreement_points[:5],
        "disagreement_points": disagreement_points[:5],
        "total_rounds": MAX_DEBATE_ROUNDS,
        "total_llm_calls": len(agents) * MAX_DEBATE_ROUNDS + 1,
    }