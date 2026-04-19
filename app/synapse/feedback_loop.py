import json
import time
import os
from typing import Dict, Any, Optional

from app.synapse.config import FEEDBACK_FILE, SYNAPSE_DIR


def _load_feedback() -> list:
    if not os.path.exists(FEEDBACK_FILE):
        return []
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_feedback(feedback: list):
    os.makedirs(SYNAPSE_DIR, exist_ok=True)
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(feedback, f, ensure_ascii=False, indent=2)


def record_feedback(
    agent_name: str,
    feedback_type: str,
    user_message: str = "",
    agent_response: str = "",
    user_rating: str = "",
) -> Dict[str, Any]:
    entry = {
        "agent_name": agent_name,
        "feedback_type": feedback_type,
        "user_message": user_message[:500],
        "agent_response": agent_response[:500],
        "user_rating": user_rating,
        "timestamp": time.time(),
    }
    feedback = _load_feedback()
    feedback.append(entry)
    if len(feedback) > 1000:
        feedback = feedback[-1000:]
    _save_feedback(feedback)

    if feedback_type == "thumbs_up" and agent_name:
        from app.synapse.synapse_engine import learn_from_interaction
        learn_from_interaction(agent_name, "effective", {
            "triggers": agent_name,
            "what_worked": f"用户认可: {user_message[:100]}",
            "source": "feishu_feedback",
        })

    elif feedback_type == "thumbs_down" and agent_name:
        from app.synapse.synapse_engine import learn_from_interaction
        learn_from_interaction(agent_name, "anti", {
            "triggers": agent_name,
            "the_mistake": f"用户不满意: {user_message[:100]}",
            "source": "feishu_feedback",
        })

    return {"status": "recorded", "entry": entry}


def get_agent_score(agent_name: str, window: int = 50) -> Dict[str, Any]:
    feedback = _load_feedback()
    relevant = [f for f in feedback if f.get("agent_name") == agent_name]
    if window:
        relevant = relevant[-window:]

    total = len(relevant)
    thumbs_up = sum(1 for f in relevant if f.get("feedback_type") == "thumbs_up")
    thumbs_down = sum(1 for f in relevant if f.get("feedback_type") == "thumbs_down")

    score = 0.5
    if total > 0:
        score = 0.3 + 0.7 * (thumbs_up / total) if total > 0 else 0.5

    return {
        "agent_name": agent_name,
        "total_feedback": total,
        "thumbs_up": thumbs_up,
        "thumbs_down": thumbs_down,
        "score": round(score, 3),
    }


def get_all_agent_scores() -> Dict[str, Any]:
    from app.synapse.agent_manager import load_agents
    agents = load_agents()
    results = []
    for agent in agents:
        score_data = get_agent_score(agent["name"])
        score_data["description"] = agent["description"]
        score_data["emoji"] = agent["emoji"]
        results.append(score_data)
    return {"agents": results}


def auto_learn_from_decision_result(decision_id: str, eval_score: float, decision_type: str):
    from app.synapse.agent_manager import find_agent_by_decision_type, update_agent_patterns

    agent = find_agent_by_decision_type(decision_type)
    if not agent:
        return {"status": "no_agent", "decision_type": decision_type}

    if eval_score >= 0.7:
        update_agent_patterns(agent["name"], "effective", {
            "triggers": decision_type,
            "what_worked": f"决策得分{eval_score:.2f}，高评分验证",
            "score": eval_score,
            "source": "auto_learn",
        })
        from app.synapse.synapse_engine import learn_from_interaction
        learn_from_interaction(agent["name"], "effective", {
            "triggers": decision_type,
            "what_worked": f"决策得分{eval_score:.2f}",
            "source": "auto_learn_decision",
        })
    elif eval_score < 0.3:
        update_agent_patterns(agent["name"], "anti", {
            "triggers": decision_type,
            "the_mistake": f"决策得分{eval_score:.2f}，低分警告",
            "score": eval_score,
            "source": "auto_learn",
        })
        from app.synapse.synapse_engine import learn_from_interaction
        learn_from_interaction(agent["name"], "anti", {
            "triggers": decision_type,
            "the_mistake": f"决策得分{eval_score:.2f}",
            "source": "auto_learn_decision",
        })

    return {"status": "learned", "agent": agent["name"], "eval_score": eval_score}