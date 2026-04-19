from fastapi import APIRouter, HTTPException
from app.debug_logger import get_logs, get_latest_log, clear_logs, get_decision_log
from app.debug_formatter import format_log_entry

router = APIRouter(prefix="/debug", tags=["调试"])


@router.get("/logs")
def list_debug_logs(limit: int = 20):
    logs = get_logs(limit=limit)
    return {
        "total": len(logs),
        "logs": logs,
    }


@router.get("/logs/latest")
def latest_debug_log():
    log = get_latest_log()
    if not log:
        return {"message": "暂无调试日志"}
    return {
        "log": log,
        "formatted": format_log_entry(log),
    }


@router.get("/logs/{decision_id}")
def get_decision_debug(decision_id: str):
    log = get_decision_log(decision_id)
    if not log:
        raise HTTPException(status_code=404, detail="未找到该决策的调试日志")
    return {
        "log": log,
        "formatted": format_log_entry(log),
    }


@router.get("/trace/{decision_id}")
def get_full_trace(decision_id: str):
    from app.memory import load_all

    log = get_decision_log(decision_id)
    records = load_all()
    record = None
    for r in records:
        if r.decision.decision_id == decision_id:
            record = r
            break

    if not log and not record:
        raise HTTPException(status_code=404, detail="未找到该决策")

    trace = {"decision_id": decision_id}

    if log:
        trace["debug"] = log

    if record:
        trace["record"] = {
            "input": record.input.model_dump(),
            "decision": record.decision.model_dump(),
            "evaluation": record.evaluation.model_dump() if record.evaluation else None,
            "timestamp": record.timestamp,
        }

    return trace


@router.delete("/logs")
def delete_debug_logs():
    clear_logs()
    return {"message": "调试日志已清空"}


@router.get("/stats")
def debug_stats():
    from app.pattern_engine import get_all_patterns

    logs = get_logs(limit=1000)
    patterns = get_all_patterns()

    pattern_usage = {}
    for log in logs:
        chosen = log.get("chosen_pattern")
        if chosen:
            pid = chosen.get("id")
            if pid:
                pattern_usage[pid] = pattern_usage.get(pid, 0) + 1

    evaluations = [l for l in logs if l.get("_evaluation")]
    avg_score = 0
    if evaluations:
        avg_score = sum(e["_evaluation"]["score"] for e in evaluations) / len(
            evaluations
        )

    return {
        "total_decisions": len(logs),
        "total_evaluations": len(evaluations),
        "avg_evaluation_score": round(avg_score, 3),
        "pattern_usage": pattern_usage,
        "total_patterns": len(patterns),
    }
