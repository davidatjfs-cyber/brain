from typing import Dict, Any, Tuple


def rule_score(decision: Dict[str, Any]) -> float:
    score = 0.0

    if len(decision.get("actions", [])) >= 2:
        score += 0.15
    if len(decision.get("actions", [])) >= 3:
        score += 0.05

    used_ids = decision.get("used_pattern_ids", [])
    if used_ids:
        score += 0.2

    reasoning = decision.get("reasoning", "")
    if len(reasoning) > 30:
        score += 0.1
    if len(reasoning) > 80:
        score += 0.1

    risk = decision.get("risk_level", "medium")
    if risk == "low":
        score += 0.15
    elif risk == "medium":
        score += 0.05

    decision_text = decision.get("decision", "")
    if len(decision_text) > 20:
        score += 0.1
    if len(decision_text) > 50:
        score += 0.05

    confidence = decision.get("confidence", 0.5)
    if 0.6 <= confidence <= 0.9:
        score += 0.1

    return min(score, 1.0)


def llm_score(decision: Dict[str, Any], store_input=None) -> float:
    return 0.65


def auto_evaluate(decision: Dict[str, Any], store_input=None) -> Dict[str, Any]:
    r = rule_score(decision)
    l = llm_score(decision, store_input)

    final = round(r * 0.6 + l * 0.4, 4)

    if decision.get("is_exploration"):
        final = round(final + 0.05, 4)
        final = min(final, 0.95)

    components = {
        "rule_score": round(r, 4),
        "llm_score": round(l, 4),
        "final_score": final,
        "passed_rule_threshold": r >= 0.5,
        "is_exploration": decision.get("is_exploration", False),
        "exploration_bonus": 0.05 if decision.get("is_exploration") else 0.0,
    }

    return components
