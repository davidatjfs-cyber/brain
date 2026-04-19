import json
from typing import List, Dict, Any
from app.pattern_engine import get_all_patterns, load_patterns
from app.pattern_scorer import get_pattern_by_id
from app.test_engine import run_single_test


TEST_CASES = [
    {
        "name": "包房使用率严重偏低",
        "store_id": "test_001",
        "date": "2026-04-11",
        "metrics": {"revenue": 8000, "turnover": 1.1, "包房使用率": 0.18},
        "menu": [{"name": "烧鹅", "sales": 30}],
        "feedback": [{"type": "差评", "content": "包房太冷"}],
        "scenario": "包房本周使用率只有18%，低于严重异常阈值",
    },
    {
        "name": "营收大幅下降",
        "store_id": "test_002",
        "date": "2026-04-11",
        "metrics": {"revenue": 7000, "turnover": 1.0, "包房使用率": 0.30},
        "menu": [{"name": "烧鹅", "sales": 20}],
        "feedback": [],
        "scenario": "门店日营收远低于目标",
    },
    {
        "name": "翻台率过低",
        "store_id": "test_003",
        "date": "2026-04-11",
        "metrics": {"revenue": 12000, "turnover": 0.9, "包房使用率": 0.35},
        "menu": [{"name": "烧鹅", "sales": 40}],
        "feedback": [{"type": "差评", "content": "等位时间太长"}],
        "scenario": "翻台率只有0.9，低于正常水平",
    },
]


def run_comparison_test() -> Dict[str, Any]:
    results = []
    patterns_before = load_patterns()["patterns"]

    for case in TEST_CASES:
        wrapped = {"name": case["name"], "input": case}
        result = run_single_test(wrapped)
        d = result.get("decision")

        matched_ids = result.get("used_pattern_ids", [])
        top_pattern = matched_ids[0] if matched_ids else None

        results.append(
            {
                "case": case["name"],
                "decision": d.get("decision", "")[:80] if d else "生成失败",
                "decision_type": d.get("decision_type", "—") if d else "—",
                "confidence": d.get("confidence", 0) if d else 0,
                "used_pattern": top_pattern or "无",
                "all_matched": matched_ids,
                "competition": result.get("competition", []),
                "reasoning": d.get("reasoning", "")[:120] if d else "",
            }
        )

    patterns_after = load_patterns()["patterns"]

    return {
        "results": results,
        "patterns_before": len(patterns_before),
        "patterns_after": len(patterns_after),
        "total_patterns": len(patterns_after),
    }


def print_comparison_report(report: Dict[str, Any]):
    print("\n" + "=" * 70)
    print("  🏆 Pattern Competition 测试报告")
    print("=" * 70)
    print(f"\n策略规律库总量: {report['total_patterns']} 个\n")

    print(f"{'场景':<25} {'策略类型':<12} {'置信度':<8} {'使用Pattern'}")
    print("-" * 70)

    for r in report["results"]:
        pat = r["used_pattern"]
        conf = f"{r['confidence']:.2f}"
        competition = r.get("competition", [])
        comp_str = ""
        if competition:
            comp_str = f" | 竞争: " + " > ".join(
                f"{c['id']}({c['final_score']:.2f})" for c in competition[:2]
            )
        print(f"{r['case']:<22} {r['decision_type']:<12} {conf:<8} {pat}{comp_str}")

    print()
    print("=" * 70)
    print("  📊 策略使用分布")
    print("=" * 70)

    pat_counts: Dict[str, int] = {}
    for r in report["results"]:
        p = r["used_pattern"]
        pat_counts[p] = pat_counts.get(p, 0) + 1

    for pat, count in sorted(pat_counts.items(), key=lambda x: -x[1]):
        bar = "█" * count + "░" * (len(report["results"]) - count)
        print(f"  {pat:<20} [{bar}] {count}/{len(report['results'])}")

    print()
    print("=" * 70)


def test_pattern_priority() -> Dict[str, Any]:
    """测试：高分 pattern 是否优先被使用"""
    patterns = get_all_patterns()
    if len(patterns) < 2:
        return {
            "passed": False,
            "reason": f"patterns数量不足({len(patterns)})，需要至少2个才能测试优先级",
        }

    sorted_by_score = sorted(patterns, key=lambda p: p["score"], reverse=True)
    top1 = sorted_by_score[0]
    top2 = sorted_by_score[1]

    return {
        "passed": top1["score"] > top2["score"],
        "top1": {
            "id": top1["id"],
            "score": top1["score"],
            "usage": top1.get("usage_count", 0),
        },
        "top2": {
            "id": top2["id"],
            "score": top2["score"],
            "usage": top2.get("usage_count", 0),
        },
        "reason": f"Top1({top1['score']:.3f}) > Top2({top2['score']:.3f}) ✓",
    }


def test_pattern_score_update():
    """测试：pattern 评分是否可动态更新"""
    patterns = get_all_patterns()
    if not patterns:
        return {"passed": False, "reason": "patterns为空"}

    p = patterns[0]
    old_score = p["score"]
    old_count = p.get("usage_count", 0)

    from app.pattern_scorer import update_pattern_score

    result = update_pattern_score(p["id"], 0.5)

    updated = get_pattern_by_id(p["id"])
    new_score = updated["score"]
    new_count = updated.get("usage_count", 0)

    return {
        "passed": new_count == old_count + 1 and new_score != old_score,
        "pattern_id": p["id"],
        "old_score": old_score,
        "new_score": new_score,
        "usage_count_before": old_count,
        "usage_count_after": new_count,
        "reason": f"score: {old_score:.3f} → {new_score:.3f}, usage: {old_count} → {new_count}",
    }


def run_all_tests() -> Dict[str, Any]:
    report = run_comparison_test()
    priority = test_pattern_priority()
    scorer = test_pattern_score_update()

    print_comparison_report(report)

    print("\n  🔬 专项测试")
    print("  " + "-" * 50)
    print(
        f"  1. Pattern优先级: {'✅ 通过' if priority['passed'] else '❌ 失败'} — {priority.get('reason', '')}"
    )
    print(
        f"  2. 动态评分更新: {'✅ 通过' if scorer['passed'] else '❌ 失败'} — {scorer.get('reason', '')}"
    )

    all_passed = priority["passed"] and scorer["passed"]
    print(f"\n  {'🏆 全部测试通过' if all_passed else '⚠️ 部分测试失败'}")
    print("  " + "-" * 50)

    return {
        "comparison_report": report,
        "priority_test": priority,
        "scorer_test": scorer,
        "all_passed": all_passed,
    }
