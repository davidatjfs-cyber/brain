from app.memory import load_all
from app.evolution import get_high_score_patterns, get_failed_patterns


def extract_patterns_from_history():
    records = load_all()
    evaluated = [r for r in records if r.evaluation is not None]

    evaluated.sort(key=lambda r: r.evaluation.score, reverse=True)

    high = []
    low = []

    for r in evaluated:
        score = r.evaluation.score
        decision_text = r.decision.decision
        decision_type = r.decision.decision_type
        actions = r.decision.actions or []

        entry = {
            "decision": decision_text,
            "decision_type": decision_type,
            "actions": actions,
            "score": score,
            "judgement": r.evaluation.final_judgement,
        }

        if score >= 0.75 and len(high) < 3:
            high.append(entry)
        elif score <= 0.6 and len(low) < 3:
            low.append(entry)

    return high, low


def build_constraints():
    from_patterns = {
        "high": get_high_score_patterns(),
        "low": get_failed_patterns(),
    }

    from_history_high, from_history_low = extract_patterns_from_history()

    all_high = []
    seen_decisions = set()

    for p in from_patterns["high"] + from_history_high:
        key = p.get("decision", "")[:50]
        if key and key not in seen_decisions:
            seen_decisions.add(key)
            all_high.append(p)

    all_low = []
    seen_low = set()
    for p in from_patterns["low"] + from_history_low:
        key = p.get("decision", "")[:50]
        if key and key not in seen_low:
            seen_low.add(key)
            all_low.append(p)

    must_use = [p["decision"][:150] for p in all_high[:3] if p.get("decision")]
    must_avoid = [p["decision"][:150] for p in all_low[:3] if p.get("decision")]

    return {
        "must_use": must_use,
        "must_avoid": must_avoid,
        "high_patterns": all_high,
        "low_patterns": all_low,
    }
