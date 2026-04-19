import time
from app.brain_core import make_decision
from app.memory import save, load_all, update
from app.evaluation import evaluate
from app.models import StoreInput, Decision, DecisionRecord, EvaluationResult


def run_single_test(test_case):
    store_input = StoreInput(**test_case["input"])
    result = make_decision(store_input)

    if result.get("error"):
        print(f"  ⚠️ 决策生成失败: {result.get('error')}")
        return {
            "name": test_case["name"],
            "decision": None,
            "decision_id": None,
            "used_pattern_ids": [],
            "competition": [],
            "error": result.get("error"),
        }

    decision = result["decision"]
    decision_id = result["decision_id"]

    record = DecisionRecord(
        input=store_input,
        decision=Decision(**decision),
    )

    print(f"  ✅ decision_id: {decision_id}")
    print(
        f"     类型: {decision.get('decision_type')} | 置信度: {decision.get('confidence')} | 状态: {result['status']}"
    )
    print(f"     问题: {decision.get('problem')}")
    print(f"     决策: {decision.get('decision')}")
    print(f"     动作: {', '.join(decision.get('actions', [])[:2])}")

    return {
        "name": test_case["name"],
        "decision": decision,
        "decision_id": decision_id,
        "used_pattern_ids": result.get("used_pattern_ids", []),
        "competition": result.get("competition", []),
    }


def run_batch_tests(test_cases, delay=2):
    results = []
    for i, case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] 场景: {case['name']}")
        result = run_single_test(case)
        results.append(result)
        if i < len(test_cases) and delay:
            print(f"  ⏳ 等待 {delay}s ...")
            time.sleep(delay)
    return results


def stability_test(test_case, times=3, delay=2):
    print(f"\n{'=' * 50}")
    print(f"🧪 稳定性测试: {test_case['name']} (×{times})")
    print(f"{'=' * 50}")

    results = []
    for i in range(times):
        print(f"\n  第 {i + 1} 次运行:")
        result = run_single_test(test_case)
        results.append(result)
        if i < times - 1 and delay:
            print(f"  ⏳ 等待 {delay}s ...")
            time.sleep(delay)

    decision_ids = [r["decision_id"] for r in results if r.get("decision_id")]
    all_same_type = all(
        r["decision"].get("decision_type")
        == results[0]["decision"].get("decision_type")
        for r in results
        if r.get("decision")
    )

    print(f"\n{'=' * 50}")
    print(f"📊 稳定性结果:")
    print(
        f"   决策ID一致: {'✅' if len(set(decision_ids)) == 1 else '⚠️ 不同ID（正常，UUID随机）'}"
    )
    print(f"   决策类型一致: {'✅' if all_same_type else '⚠️ 有变化'}")
    for i, r in enumerate(results, 1):
        d = r.get("decision", {})
        print(
            f"   [{i}] {d.get('decision_type')} | confidence:{d.get('confidence')} | {r.get('decision_id', '')[:8]}..."
        )

    return results


def evaluate_decision(decision_id, metrics, comment=""):
    records = load_all()
    target = None
    for r in records:
        if r.decision.decision_id == decision_id:
            target = r
            break

    if not target:
        return {"error": "决策记录不存在"}

    result = evaluate(metrics)
    target.evaluation = EvaluationResult(
        score=result["score"],
        metrics=result["metrics"],
        final_judgement=result["final_judgement"],
        comment=comment,
    )
    update(target)

    return {
        "evaluation": {
            "score": result["score"],
            "final_judgement": result["final_judgement"],
            "comment": comment,
        },
        "decision_id": decision_id,
    }


def calculate_stats(scores):
    if not scores:
        return {"error": "无评分数据"}

    avg = sum(scores) / len(scores)
    passed = sum(1 for s in scores if s >= 0.7)
    failed = len(scores) - passed

    return {
        "total": len(scores),
        "avg_score": round(avg, 4),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(scores), 4),
        "scores": scores,
    }


def compare_with_agent(agent_result, brain_result):
    print(f"\n{'=' * 50}")
    print(f"🔍 Agent V2 vs Brain V1 对比")
    print(f"{'=' * 50}")
    print(f"Agent V2: {agent_result}")
    print(f"Brain V1: {brain_result}")
    print(f"{'=' * 50}")
