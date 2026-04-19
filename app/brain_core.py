from app.models import StoreInput, Decision, DecisionRecord
from app.memory import get_recent_decisions, save
from app.llm_client import call_llm, extract_json
from app.system_prompt import build_prompt
from app.confidence import calibrate_confidence, assign_status
from app.contract import validate_decision, ContractError
from app.knowledge import retrieve_knowledge
from app.self_reflection import reflect_on_history, self_check
from app.evolution import (
    evolve_from_evaluation,
    get_high_score_patterns,
    get_failed_patterns,
)
from app.strategy_enforcer import build_constraints
from app.behavior_engine import enforce_strategy
from app.reasoning import build_reasoning
from app.pattern_matcher import match_patterns, get_matched_pattern_ids
from app.pattern_competitor import (
    rank_patterns,
    build_competition_context,
    get_top_patterns,
)
from app.pattern_scorer import update_pattern_usage
from app.debug_logger import log_decision, log_evaluation
from app.debug_formatter import format_decision_debug
from app.exploration_engine import should_explore, get_exploration_stats
from app.strategy_mutator import mutate_strategy
from app.simulator import simulate
from app.strategy_selector import (
    select_best_strategy,
    get_strategy_ranking,
    explain_selection,
)
from app.goal_adjuster import adjust_goal, get_goal_adjustment_status
from app.goal_engine import get_current_goal
from app.eval_logger import get_eval_history

GLOBAL_OBJECTIVE = {
    "mode": "balance",
    "weights": {
        "revenue": 0.4,
        "profit": 0.3,
        "turnover": 0.3,
    },
}


def make_decision(store_input: StoreInput) -> dict:
    recent_evals = get_eval_history(limit=10)
    recent = get_recent_decisions()

    adjusted_goal = adjust_goal(
        current_metrics=store_input.metrics,
        recent_evals=recent_evals,
    )
    current_goal = get_current_goal()
    constraints = build_constraints()
    knowledge = retrieve_knowledge()
    matched_patterns = match_patterns(store_input)
    ranked_patterns = rank_patterns(matched_patterns, store_input, top_n=3)
    top_pattern_ids = [item["pattern"]["id"] for item in ranked_patterns]
    competition_context = build_competition_context(matched_patterns, store_input)

    try:
        from app.synapse.agent_manager import find_agent_by_decision_type, load_learned_patterns
        synapse_global_patterns = load_learned_patterns()
        ep = synapse_global_patterns.get("effective", [])
        ap = synapse_global_patterns.get("anti", [])
        ep_text = "\n".join(f"✅ {p.get('what_worked', '')[:80]}" for p in ep[:3])
        ap_text = "\n".join(f"❌ {p.get('the_mistake', '')[:80]}" for p in ap[:3])
        if ep_text:
            knowledge += f"\n\n【Synapse有效模式】\n{ep_text}"
        if ap_text:
            knowledge += f"\n\n【Synapse反模式】\n{ap_text}"
    except Exception:
        pass

    prompt = build_prompt(
        store_input,
        recent,
        constraints,
        knowledge,
        competition_context=competition_context,
    )

    raw = call_llm(prompt)
    parsed = extract_json(raw)

    do_explore, explore_reason = should_explore()

    if do_explore:
        parsed = mutate_strategy(parsed, store_input)

    candidates = []
    for item in ranked_patterns:
        p = item["pattern"]
        candidates.append(
            {
                "decision": p["strategy"],
                "actions": p.get("actions", []),
                "problem": p.get("problem", ""),
                "pattern_id": p["id"],
                "is_pattern": True,
                "is_exploration": False,
            }
        )
    if do_explore:
        candidates.append(
            {
                "decision": parsed.get("decision", ""),
                "actions": parsed.get("actions", []),
                "problem": parsed.get("problem", ""),
                "pattern_id": None,
                "is_pattern": False,
                "is_exploration": True,
            }
        )

    input_for_sim = {
        "metrics": store_input.metrics,
        "scenario": store_input.scenario or "",
    }
    ranking = get_strategy_ranking(candidates, input_for_sim)
    best_sim = ranking[0] if ranking else {}

    sim_score = best_sim.get("simulated_score", 0)
    sim_outcome = best_sim.get("simulated_outcome", {})
    sim_explanation = explain_selection(
        best_sim, ranking[1] if len(ranking) > 1 else None
    )

    decision = Decision(
        problem=parsed.get("problem", ""),
        decision=parsed.get("decision", ""),
        actions=parsed.get("actions", []),
        expected_impact=parsed.get("expected_impact", ""),
        risk_level=parsed.get("risk_level", "medium"),
        confidence=float(parsed.get("confidence", 0.5)),
        decision_type=parsed.get("decision_type", "operation"),
        reasoning=parsed.get("reasoning", ""),
        used_pattern_ids=top_pattern_ids,
    )

    try:
        validate_decision(decision)
    except ContractError as e:
        return {
            "decision": None,
            "decision_id": None,
            "status": "contract_failed",
            "error": str(e),
            "raw_output": raw[:500],
        }

    check = self_check(decision)
    if not check["passed"]:
        decision.confidence = max(0.3, decision.confidence - 0.15)

    enforce_result = enforce_strategy(decision, constraints)

    decision.confidence = calibrate_confidence(decision)
    decision.decision_status = assign_status(decision.confidence)

    if sim_score > 0.1:
        decision.confidence = min(0.95, decision.confidence + 0.05)
    elif sim_score < 0.03:
        decision.confidence = max(0.35, decision.confidence - 0.08)

    if not decision.reasoning:
        decision.reasoning = build_reasoning(
            store_input, recent, knowledge, constraints
        )

    record = DecisionRecord(input=store_input, decision=decision)
    save(record)

    for pid in top_pattern_ids:
        update_pattern_usage(pid)

    debug_info = format_decision_debug(
        store_input,
        matched_patterns,
        ranked_patterns,
        top_pattern_ids,
        constraints,
        raw,
        {
            "decision_id": decision.decision_id,
            "decision": decision.model_dump(),
            "status": decision.decision_status,
        },
        enforce_result,
        simulation_data={
            "ranking": [
                {
                    "rank": i + 1,
                    "pattern_id": c.get("pattern_id"),
                    "is_exploration": c.get("is_exploration", False),
                    "simulated_score": c.get("simulated_score", 0),
                    "outcome": c.get("simulated_outcome", {}),
                }
                for i, c in enumerate(ranking[:3])
            ],
            "best_id": best_sim.get("pattern_id")
            or ("exploration" if do_explore else None),
            "best_score": sim_score,
            "best_outcome": sim_outcome,
            "explanation": sim_explanation,
        },
    )
    log_decision(debug_info)

    return {
        "decision": decision.model_dump(),
        "decision_id": decision.decision_id,
        "status": decision.decision_status,
        "reflection": reflect_on_history(recent),
        "check": {
            "passed": check["passed"],
            "issues": check["issues"],
            "warnings": check["warnings"],
        },
        "enforcement": {
            "adjustment": enforce_result["adjustment"],
            "used_good": enforce_result["used_good"],
            "used_bad": enforce_result["used_bad"],
        },
        "used_pattern_ids": top_pattern_ids,
        "competition": [
            {
                "rank": item["rank"],
                "id": item["pattern"]["id"],
                "final_score": item["final_score"],
                "base_score": item["base_score"],
                "usage_count": item["usage_count"],
            }
            for item in ranked_patterns
        ],
        "matched_patterns": [
            {"id": p["id"], "score": p["score"], "strategy": p["strategy"][:50]}
            for p in matched_patterns
        ],
        "exploration": {
            "is_exploration": do_explore,
            "reason": explore_reason,
            "mutation_type": parsed.get("mutation_type", None) if do_explore else None,
        },
        "simulation": {
            "ranking": [
                {
                    "rank": i + 1,
                    "pattern_id": c.get("pattern_id"),
                    "is_exploration": c.get("is_exploration", False),
                    "simulated_score": c.get("simulated_score", 0),
                    "outcome": c.get("simulated_outcome", {}),
                }
                for i, c in enumerate(ranking[:3])
            ],
            "best_id": best_sim.get("pattern_id")
            or ("exploration" if do_explore else None),
            "best_score": sim_score,
            "best_outcome": sim_outcome,
            "explanation": sim_explanation,
        },
        "goal": {
            "weights": current_goal,
            "was_adjusted": adjusted_goal is not None,
            "adjustment": adjusted_goal,
        },
    }


def record_evaluation_and_evolve(decision_record):
    return evolve_from_evaluation(decision_record)
