import json
import os
from typing import Dict, Any, List

from app.pattern_engine import get_all_patterns, save_patterns
from app.evolution import get_high_score_patterns, get_failed_patterns
from app.synapse.agent_manager import load_learned_patterns, save_learned_patterns, load_agents, update_agent_patterns


def synapse_to_brain() -> Dict[str, Any]:
    patterns = load_learned_patterns()
    effective = patterns.get("effective", [])
    anti = patterns.get("anti", [])

    brain_data = get_all_patterns()
    added = 0

    for ep in effective:
        triggers = ep.get("triggers", "")
        strategy = ep.get("what_worked", ep.get("description", ""))
        if not strategy:
            continue
        exists = any(p["strategy"][:60] == strategy[:60] for p in brain_data)
        if not exists:
            new_pattern = {
                "id": f"synapse_{len(brain_data) + 1:03d}",
                "conditions": {"source": "synapse", "triggers": triggers},
                "decision_type": ep.get("decision_type", "operation"),
                "strategy": strategy,
                "actions": ep.get("actions", []),
                "expected_impact": ep.get("expected_impact", ""),
                "score": 0.80,
                "usage_count": 0,
                "abstracted_from": "synapse_bridge",
            }
            brain_data.append(new_pattern)
            added += 1

    if added > 0:
        save_patterns({"patterns": brain_data, "meta": {"version": "1.0", "total_abstracted": len(brain_data)}})

    return {"added_to_brain": added, "effective_synced": len(effective), "anti_recorded": len(anti)}


def brain_to_synapse() -> Dict[str, Any]:
    high_score = get_high_score_patterns()
    failed = get_failed_patterns()

    synapse_patterns = load_learned_patterns()

    high_added = 0
    for h in high_score:
        exists = any(
            p.get("description", "")[:60] == str(h)[:60]
            for p in synapse_patterns.get("effective", [])
        )
        if not exists:
            synapse_patterns.setdefault("effective", []).append({
                "triggers": h.get("decision_type", "operation"),
                "description": str(h)[:200],
                "what_worked": str(h)[:200],
                "decision_type": h.get("decision_type", "operation"),
                "source": "brain_bridge",
            })
            high_added += 1

    fail_added = 0
    for f in failed:
        exists = any(
            p.get("description", "")[:60] == str(f)[:60]
            for p in synapse_patterns.get("anti", [])
        )
        if not exists:
            synapse_patterns.setdefault("anti", []).append({
                "triggers": f.get("decision_type", "operation"),
                "description": str(f)[:200],
                "the_mistake": str(f)[:200],
                "decision_type": f.get("decision_type", "operation"),
                "source": "brain_bridge",
            })
            fail_added += 1

    save_learned_patterns(synapse_patterns)

    return {
        "high_score_synced": high_added,
        "failed_synced": fail_added,
        "total_effective": len(synapse_patterns.get("effective", [])),
        "total_anti": len(synapse_patterns.get("anti", [])),
    }


def sync_agent_patterns_from_brain():
    agents = load_agents()
    high_score = get_high_score_patterns()
    failed = get_failed_patterns()

    results = []
    for agent in agents:
        dt = agent.get("decision_type", "")
        relevant_high = [h for h in high_score if h.get("decision_type") == dt]
        relevant_fail = [f for f in failed if f.get("decision_type") == dt]

        for h in relevant_high[:3]:
            update_agent_patterns(agent["name"], "effective", {
                "triggers": dt,
                "what_worked": str(h)[:200],
                "source": "brain_bridge",
            })

        for f in relevant_fail[:3]:
            update_agent_patterns(agent["name"], "anti", {
                "triggers": dt,
                "the_mistake": str(f)[:200],
                "source": "brain_bridge",
            })

        results.append({
            "agent": agent["name"],
            "high_synced": len(relevant_high[:3]),
            "fail_synced": len(relevant_fail[:3]),
        })

    return results


def full_sync() -> Dict[str, Any]:
    s2b = synapse_to_brain()
    b2s = brain_to_synapse()
    agent_sync = sync_agent_patterns_from_brain()
    return {
        "synapse_to_brain": s2b,
        "brain_to_synapse": b2s,
        "agent_sync": agent_sync,
    }