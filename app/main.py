from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.models import (
    StoreInput,
    Decision,
    DecisionRecord,
    EvaluationResult,
)
from app.brain_core import make_decision, record_evaluation_and_evolve
from app.memory import load_all, update
from app.evaluation import evaluate
from app.evolution import get_high_score_patterns, get_failed_patterns
from app.pattern_engine import get_all_patterns, get_patterns_summary
from app.pattern_matcher import match_patterns
from app.comparison_test import (
    run_all_tests,
    run_comparison_test,
    test_pattern_priority,
    test_pattern_score_update,
)
from app.debug_api import router as debug_router
from app.debug_logger import get_logs
from app.auto_evaluator_v2 import auto_evaluate
from app.anti_bias_guard import anti_bias_check, get_bias_status
from app.eval_logger import (
    log_eval,
    get_eval_history,
    get_avg_score,
    get_score_trend,
    clear_eval_logs,
)
from app.exploration_engine import (
    get_exploration_stats,
    reset_exploration_state,
    adjust_exploration_rate,
)
from app.goal_engine import get_current_goal, reset_goal, update_goal
from app.goal_adjuster import get_goal_adjustment_status
from app.reality_logger import (
    log_real_outcome,
    get_real_outcomes,
    compute_prediction_accuracy,
    clear_real_outcomes,
)
from app.outcome_comparator import compare, compute_error_stats
from app.model_corrector import (
    adjust_prediction_rules,
    apply_adjustments,
    get_correction_status,
    reset_factors,
    get_current_factors,
)
from app.shadow_runner import run_shadow
from app.decision_comparator import compare_decisions, evaluate_brain_value
from app.shadow_logger import (
    log_shadow,
    get_shadow_logs,
    get_shadow_by_id,
    get_shadow_stats,
    update_shadow_outcome,
)
from app.failure_analyzer import analyze_failure
from app.failure_patterns import (
    save_failure_pattern,
    get_failure_logs,
    get_failure_stats,
    clear_failure_logs,
)
from app.improvement_engine import (
    suggest_improvement,
    get_top_improvements,
    get_priority_improvements,
    translate_reason,
)
from app.parameter_store import load_params, reset_params, get_all_params
from app.fix_executor import run_auto_fix, get_auto_fix_stats
from app.trend_analyzer import get_all_trends, get_convergence_status, clear_trend_logs
from app.stabilizer import get_stability_report
from app.decision_value import (
    calculate_value,
    calculate_decision_roi,
    estimate_brain_value_per_month,
)
from app.roi_reporter import (
    record_roi_entry,
    get_roi_entries,
    get_roi_stats,
    get_monthly_report,
    get_roi_summary,
    clear_roi_logs,
)
from app.reality_logger import (
    log_real_outcome,
    get_real_outcomes,
    get_real_outcomes_stats,
    clear_real_outcomes,
)
from app.outcome_tracker import (
    track_outcome,
    compare_with_brain_decision,
    calculate_real_roi,
)
from app.roi_real_calculator import calculate_real_roi_summary, get_top_performers
from app.synapse.feishu_bot import router as feishu_router
from app.synapse.agent_manager import init_agents

app = FastAPI(
    title="Brain V5.0 — 餐饮经营决策大脑（Professor Synapse增强版）",
    version="5.0.0",
)

app.include_router(debug_router)
app.include_router(feishu_router)


@app.on_event("startup")
def startup_init():
    init_agents()


@app.post("/decision")
def post_decision(body: StoreInput):
    result = make_decision(body)
    if result.get("error"):
        raise HTTPException(status_code=422, detail=result)
    return result


@app.post("/decision/{decision_id}/evaluate")
def post_evaluate(decision_id: str, body: dict):
    records = load_all()
    target = None
    for r in records:
        if r.decision.decision_id == decision_id:
            target = r
            break

    if not target:
        raise HTTPException(status_code=404, detail="决策记录不存在")

    score = body.get("score")
    if score is None:
        raise HTTPException(status_code=422, detail="score字段必填")

    ev = EvaluationResult(
        score=score,
        metrics=body.get("metrics", {}),
        final_judgement="positive"
        if score >= 0.7
        else ("negative" if score < 0.3 else "neutral"),
        comment=body.get("comment", ""),
    )
    target.evaluation = ev
    update(target)

    evolve_result = record_evaluation_and_evolve(target)

    try:
        from app.synapse.feedback_loop import auto_learn_from_decision_result
        synapse_learn = auto_learn_from_decision_result(
            decision_id, ev.score, target.decision.decision_type
        )
    except Exception:
        synapse_learn = {"status": "skipped"}

    return {
        "evaluation": ev.model_dump(),
        "decision_id": decision_id,
        "evolution": evolve_result,
        "synapse_learning": synapse_learn,
    }


@app.get("/decision/history")
def get_history():
    records = load_all()
    return [r.model_dump() for r in records]


@app.get("/decision/{decision_id}")
def get_decision(decision_id: str):
    records = load_all()
    for r in records:
        if r.decision.decision_id == decision_id:
            return r.model_dump()
    raise HTTPException(status_code=404, detail="决策记录不存在")


@app.get("/patterns")
def get_patterns():
    data = get_all_patterns()
    meta = {"total": len(data), "total_abstracted": len(data)}
    return {
        "patterns": data,
        "meta": meta,
        "summary": get_patterns_summary(),
        "high_score_patterns": get_high_score_patterns(),
        "failed_patterns": get_failed_patterns(),
    }


@app.post("/patterns/match")
def match_current_patterns(body: StoreInput):
    matched = match_patterns(body, top_n=3)
    return {
        "matched_patterns": matched,
        "count": len(matched),
    }


@app.get("/competition/report")
def get_competition_report():
    report = run_all_tests()
    return report


@app.get("/competition/test")
def run_competition_tests():
    report = run_comparison_test()
    priority = test_pattern_priority()
    scorer = test_pattern_score_update()
    return {
        "comparison": report,
        "priority_test": priority,
        "scorer_test": scorer,
        "all_passed": priority["passed"] and scorer["passed"],
    }


@app.post("/evaluate/{decision_id}/auto")
def auto_evaluate_decision(decision_id: str):
    records = load_all()
    target = None
    for r in records:
        if r.decision.decision_id == decision_id:
            target = r
            break

    if not target:
        raise HTTPException(status_code=404, detail="决策记录不存在")

    decision_dict = target.decision.model_dump()
    components = auto_evaluate(decision_dict)
    raw_score = components["final_score"]

    biased_score = anti_bias_check(decision_dict, raw_score)

    meta = {
        "rule_score": components["rule_score"],
        "llm_score": components["llm_score"],
        "bias_adjusted": biased_score != raw_score,
        "used_pattern": decision_dict.get("used_pattern_ids", [None])[0],
    }
    log_eval(decision_id, biased_score, meta)

    ev = EvaluationResult(
        score=biased_score,
        metrics={},
        final_judgement="positive"
        if biased_score >= 0.7
        else ("negative" if biased_score < 0.3 else "neutral"),
        comment="自动评估",
    )
    target.evaluation = ev
    update(target)

    evolve_result = record_evaluation_and_evolve(target)

    try:
        from app.synapse.feedback_loop import auto_learn_from_decision_result
        synapse_learn = auto_learn_from_decision_result(
            decision_id, biased_score, decision_dict.get("decision_type", "operation")
        )
    except Exception:
        synapse_learn = {"status": "skipped"}

    return {
        "decision_id": decision_id,
        "auto_score": components,
        "after_bias_guard": biased_score,
        "bias_guard_active": biased_score != raw_score,
        "evaluation": ev.model_dump(),
        "evolution": evolve_result,
        "synapse_learning": synapse_learn,
    }


@app.get("/bias/status")
def get_bias_status_api():
    status = get_bias_status()
    trend = get_score_trend(window=20)
    return {
        "bias": status,
        "score_trend": trend,
        "avg_score": get_avg_score(window=20),
    }


@app.get("/eval/history")
def get_eval_history_api(limit: int = 50):
    history = get_eval_history(limit=limit)
    return {
        "total": len(history),
        "history": history,
        "avg_score": get_avg_score(window=len(history)),
        "trend": get_score_trend(window=len(history)),
    }


@app.post("/train/loop")
def run_auto_training(rounds: int = 10):
    from app.auto_trainer import run_training_loop

    result = run_training_loop(rounds=rounds, verbose=False)
    return result


@app.get("/exploration/stats")
def get_exploration_stats_api():
    stats = get_exploration_stats()
    bias = get_bias_status()
    trend = get_score_trend(window=20)
    return {
        "exploration": stats,
        "bias": bias,
        "score_trend": trend,
        "recommendation": _get_recommendation(stats, trend),
    }


def _get_recommendation(stats: dict, trend: dict) -> str:
    actual_rate = stats.get("actual_rate", 0)
    target_rate = stats.get("target_rate", 0.15)
    change = trend.get("change", 0)

    if change < -0.05:
        return "⚠️ 性能下降，建议降低探索率"
    elif change > 0.05:
        return "✅ 性能提升，探索策略有效"
    elif actual_rate < target_rate * 0.5:
        return "⚠️ 探索过少，可能陷入局部最优"
    elif actual_rate > target_rate * 1.5:
        return "⚠️ 探索过多，可能影响稳定性"
    else:
        return "✅ 探索率正常，系统运行良好"


@app.post("/exploration/reset")
def reset_exploration():
    reset_exploration_state()
    return {"message": "探索状态已重置"}


@app.get("/goal/status")
def get_goal_status():
    status = get_goal_adjustment_status()
    current = get_current_goal()
    return {
        "current_goal": current,
        "adjustment_status": status,
        "profit_share": f"{current.get('profit_weight', 0) * 100:.0f}%",
        "revenue_share": f"{current.get('revenue_weight', 0) * 100:.0f}%",
        "turnover_share": f"{current.get('turnover_weight', 0) * 100:.0f}%",
    }


@app.post("/goal/reset")
def reset_goal_api():
    reset_goal()
    return {"message": "目标权重已重置为默认值", "goal": get_current_goal()}


@app.post("/goal/update")
def update_goal_api(body: dict):
    update_goal(body)
    return {"message": "目标权重已更新", "goal": get_current_goal()}


@app.post("/reality/feedback")
def post_reality_feedback(body: dict):
    decision_id = body.get("decision_id")
    real_metrics = body.get("real_metrics")

    if not decision_id or not real_metrics:
        raise HTTPException(status_code=422, detail="decision_id 和 real_metrics 必填")

    records = load_all()
    target = None
    for r in records:
        if r.decision.decision_id == decision_id:
            target = r
            break

    predicted_outcome = None
    debug_logs = get_logs(limit=500)
    for log in reversed(debug_logs):
        if log.get("decision_id") == decision_id:
            sim = log.get("simulation", {})
            if sim:
                for cand in sim.get("ranking", []):
                    if cand.get("rank") == 1:
                        predicted_outcome = cand.get("outcome", {})
                        break
            break

    entry = log_real_outcome(decision_id, real_metrics, predicted_outcome)

    errors = None
    adjustments = None
    if predicted_outcome:
        errors = compare(predicted_outcome, real_metrics)
        adjustments = adjust_prediction_rules(errors)
        if adjustments:
            apply_adjustments(adjustments)

    return {
        "logged": True,
        "decision_id": decision_id,
        "real_metrics": real_metrics,
        "predicted_outcome": predicted_outcome,
        "errors": errors,
        "adjustments": adjustments,
        "correction_status": get_correction_status(),
    }


@app.get("/reality/outcomes")
def get_reality_outcomes(limit: int = 20):
    outcomes = get_real_outcomes(limit=limit)
    accuracy = compute_prediction_accuracy(window=min(len(outcomes), 20))
    return {
        "total": len(outcomes),
        "outcomes": outcomes,
        "accuracy": accuracy,
    }


@app.get("/reality/accuracy")
def get_reality_accuracy():
    outcomes = get_real_outcomes(limit=100)
    accuracy = compute_prediction_accuracy(window=min(len(outcomes), 20))
    factors = get_current_factors()
    status = get_correction_status()
    return {
        "accuracy": accuracy,
        "factors": factors,
        "correction_status": status,
        "sample_size": len(outcomes),
    }


@app.post("/reality/reset")
def reset_reality_data():
    clear_real_outcomes()
    reset_factors()
    return {"message": "真实数据已清空，预测因子已重置"}


class ShadowInput(BaseModel):
    input: dict
    real_decision: dict


class ShadowOutcomeUpdate(BaseModel):
    result: str
    actual_score: float = 0
    notes: str = ""


@app.post("/shadow/run")
def run_shadow_api(body: ShadowInput):
    result = run_shadow(body.input, body.real_decision)
    comparison = compare_decisions(result["real_decision"], result["brain_decision"])
    evaluation = evaluate_brain_value(comparison, None)

    shadow_data = {
        "input": body.input,
        "real_decision": body.real_decision,
        "brain_decision": result["brain_decision"],
        "comparison": comparison,
        "evaluation": evaluation,
    }

    log_id = log_shadow(shadow_data)

    return {
        "log_id": log_id,
        "brain_decision": result["brain_decision"],
        "comparison": comparison,
        "evaluation": evaluation,
        "stats": get_shadow_stats(),
    }


@app.get("/shadow/logs")
def get_shadow_logs_api(limit: int = 50):
    logs = get_shadow_logs(limit=limit)
    stats = get_shadow_stats()
    return {
        "logs": logs,
        "total": len(logs),
        "stats": stats,
    }


@app.get("/shadow/log/{log_id}")
def get_shadow_log(log_id: str):
    log = get_shadow_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="影子记录不存在")
    return log


@app.get("/shadow/stats")
def get_shadow_stats_api():
    stats = get_shadow_stats()
    logs = get_shadow_logs(limit=0)

    brain_win_count = sum(
        1
        for log in logs
        if log.get("evaluation", {}).get("brain_better_than_human", False)
    )

    verdict_counts = {}
    for log in logs:
        v = log.get("evaluation", {}).get("verdict", "未知")
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    return {
        **stats,
        "brain_win_count": brain_win_count,
        "brain_win_rate": brain_win_count / len(logs) if logs else 0,
        "verdict_distribution": verdict_counts,
    }


@app.post("/shadow/outcome/{log_id}")
def update_shadow_outcome_api(log_id: str, body: ShadowOutcomeUpdate):
    success = update_shadow_outcome(log_id, body.model_dump())
    if not success:
        raise HTTPException(status_code=404, detail="影子记录不存在")

    log = get_shadow_by_id(log_id)
    comparison = log.get("comparison", {})
    evaluation = evaluate_brain_value(comparison, body.model_dump())

    real_outcome_data = {
        "actual_score": body.actual_score,
        "result": body.result,
    }
    brain_decision = log.get("brain_decision", {}).get("decision", {})

    value_result = calculate_value(real_outcome_data, brain_decision, log)
    roi_result = calculate_decision_roi(value_result)
    record_roi_entry(log_id, value_result, roi_result, body.model_dump())

    failure_analysis = None
    improvements = []
    auto_fix_result = None

    if body.actual_score < 0.5 or body.result in ["failure", "negative", "bad"]:
        real_decision = log.get("real_decision", {})

        outcome_data = {
            "predicted_score": evaluation.get("score", 0.5),
            "actual_score": body.actual_score,
        }

        failure_analysis = analyze_failure(real_decision, brain_decision, outcome_data)

        if failure_analysis["reasons"]:
            save_failure_pattern(
                shadow_log_id=log_id,
                reasons=failure_analysis["reasons"],
                details=failure_analysis["details"],
                failure_score=failure_analysis["failure_score"],
                summary=failure_analysis["summary"],
                real_decision=real_decision,
                brain_decision=brain_decision,
            )
            improvements = suggest_improvement(failure_analysis["reasons"])

            auto_fix_result = run_auto_fix(failure_analysis["reasons"])

    return {
        "updated": True,
        "log_id": log_id,
        "outcome": body.model_dump(),
        "re_evaluation": evaluation,
        "value": value_result,
        "roi": roi_result,
        "failure_analysis": failure_analysis,
        "improvements": improvements,
        "auto_fix": auto_fix_result,
    }


@app.get("/failure/stats")
def get_failure_stats_api():
    stats = get_failure_stats()
    improvements = get_top_improvements(stats)

    translated_reasons = [
        {"reason": r, "chinese": translate_reason(r)}
        for r in stats.get("top_failure_reasons", [])
    ]

    return {
        **stats,
        "translated_reasons": translated_reasons,
        "top_improvements": improvements,
    }


@app.get("/failure/logs")
def get_failure_logs_api(limit: int = 50):
    logs = get_failure_logs(limit=limit)
    return {
        "logs": logs,
        "total": len(logs),
    }


@app.post("/failure/reset")
def reset_failure_logs_api():
    clear_failure_logs()
    return {"message": "失败记录已清空"}


@app.get("/system/params")
def get_system_params_api():
    params = get_all_params()
    fix_stats = get_auto_fix_stats()
    return {
        "params": params,
        "fix_stats": fix_stats,
    }


@app.post("/system/reset")
def reset_system_params_api():
    params = reset_params()
    return {
        "message": "系统参数已重置为默认值",
        "params": params,
    }


@app.post("/system/params/{key}")
def update_param_api(key: str, body: dict):
    value = body.get("value")
    if value is None:
        raise HTTPException(status_code=422, detail="value字段必填")

    set_param(key, value)
    return {
        "message": f"参数 {key} 已更新",
        "key": key,
        "value": value,
        "all_params": get_all_params(),
    }


@app.get("/system/stability")
def get_stability_api():
    stability = get_stability_report()
    trends = get_all_trends()
    convergence = get_convergence_status()

    return {
        **stability,
        "trends": trends,
        "convergence": convergence,
    }


@app.get("/system/trends")
def get_trends_api():
    trends = get_all_trends()
    return {
        "trends": trends,
    }


@app.post("/system/trends/reset")
def reset_trends_api():
    clear_trend_logs()
    return {"message": "趋势记录已清空"}


@app.get("/roi/report")
def get_roi_report_api():
    stats = get_roi_stats()
    summary = get_roi_summary()
    monthly = get_monthly_report()
    shadow_stats = get_shadow_stats()

    value_estimate = estimate_brain_value_per_month(shadow_stats)

    return {
        **stats,
        "summary": summary["summary"],
        "monthly_report": monthly,
        "value_estimate": value_estimate,
    }


@app.get("/roi/summary")
def get_roi_summary_api():
    return get_roi_summary()


@app.get("/roi/entries")
def get_roi_entries_api(limit: int = 20):
    entries = get_roi_entries(limit=limit)
    return {
        "entries": entries,
        "total": len(entries),
    }


@app.get("/roi/monthly")
def get_roi_monthly_api():
    return get_monthly_report()


@app.post("/roi/reset")
def reset_roi_logs_api():
    clear_roi_logs()
    return {"message": "ROI记录已清空"}


class RealityInput(BaseModel):
    decision_id: str
    before: dict
    after: dict
    is_brain_decision: bool = False


@app.post("/reality/input")
def reality_input_api(body: RealityInput):
    result = track_outcome(
        decision_id=body.decision_id,
        before_data=body.before,
        after_data=body.after,
        is_brain_decision=body.is_brain_decision,
    )

    comparison = compare_with_brain_decision(body.decision_id)

    return {
        "logged": True,
        "result": result,
        "comparison": comparison,
    }


@app.get("/roi/real")
def get_real_roi_api():
    summary = calculate_real_roi_summary()
    top_performers = get_top_performers(limit=5)

    return {
        **summary,
        "top_performers": top_performers,
    }


@app.get("/reality/outcomes")
def get_reality_outcomes_api(limit: int = 50):
    outcomes = get_real_outcomes(limit=limit)
    stats = get_real_outcomes_stats()

    return {
        "outcomes": outcomes,
        "total": len(outcomes),
        "stats": stats,
    }


@app.get("/reality/stats")
def get_reality_stats_api():
    return get_real_outcomes_stats()


@app.get("/reality/compare/{decision_id}")
def compare_decision_api(decision_id: str):
    comparison = compare_with_brain_decision(decision_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="决策记录不存在")
    return comparison


@app.post("/reality/reset")
def reset_reality_api():
    clear_real_outcomes()
    return {"message": "真实数据已清空"}
