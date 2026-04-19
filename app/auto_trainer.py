import json
import time
from typing import Dict, Any, List

TEST_CASES = [
    {
        "name": "包房严重偏低",
        "store_id": "auto_001",
        "date": "2026-04-11",
        "metrics": {"revenue": 8000, "turnover": 1.1, "包房使用率": 0.18},
        "menu": [{"name": "烧鹅", "sales": 30}],
        "feedback": [{"type": "差评", "content": "包房太冷"}],
        "scenario": "包房使用率18%，低于严重阈值",
    },
    {
        "name": "营收下降",
        "store_id": "auto_002",
        "date": "2026-04-11",
        "metrics": {"revenue": 7000, "turnover": 0.9, "包房使用率": 0.30},
        "menu": [{"name": "煲仔饭", "sales": 50}],
        "feedback": [],
        "scenario": "营收大幅下降，翻台率过低",
    },
    {
        "name": "翻台率过低",
        "store_id": "auto_003",
        "date": "2026-04-11",
        "metrics": {"revenue": 12000, "turnover": 0.8, "包房使用率": 0.35},
        "menu": [{"name": "招牌菜", "sales": 40}],
        "feedback": [{"type": "差评", "content": "等位时间长"}],
        "scenario": "翻台率0.8，远低于正常水平",
    },
]


def run_training_round(
    cases: List[Dict], base_url: str = "http://localhost:8900"
) -> Dict[str, Any]:
    import requests

    results = []
    for case in cases:
        r = requests.post(f"{base_url}/decision", json=case, timeout=120)
        d = r.json()

        decision = d.get("decision", {})
        used_ids = d.get("used_pattern_ids", [])
        competition = d.get("competition", [])
        exploration = d.get("exploration", {})

        results.append(
            {
                "case": case["name"],
                "decision_id": d.get("decision_id"),
                "used_pattern": used_ids[0] if used_ids else None,
                "confidence": decision.get("confidence", 0),
                "decision_type": decision.get("decision_type", "—"),
                "is_exploration": exploration.get("is_exploration", False),
                "mutation_type": exploration.get("mutation_type"),
                "ranked_patterns": [
                    {"id": c["id"], "final": c["final_score"]} for c in competition[:3]
                ]
                if competition
                else [],
            }
        )

        time.sleep(1)

    return results


def run_training_loop(
    rounds: int = 10,
    base_url: str = "http://localhost:8900",
    verbose: bool = True,
) -> Dict[str, Any]:
    import requests
    from app.auto_evaluator_v2 import auto_evaluate
    from app.anti_bias_guard import anti_bias_check
    from app.eval_logger import log_eval, get_avg_score, get_score_trend
    from app.pattern_engine import get_all_patterns

    all_results = []

    print(f"\n{'=' * 60}")
    print(f"  🚀 自动训练循环开始 ({rounds}轮 × {len(TEST_CASES)}场景)")
    print(f"{'=' * 60}")

    for round_num in range(1, rounds + 1):
        if verbose:
            print(f"\n{'─' * 60}")
            print(f"  第 {round_num}/{rounds} 轮")
            print(f"{'─' * 60}")

        round_results = run_training_round(TEST_CASES, base_url)
        round_scores = []

        for res in round_results:
            decision = {
                "actions": [],
                "used_pattern_ids": [res["used_pattern"]]
                if res["used_pattern"]
                else [],
                "reasoning": "",
                "risk_level": "medium",
                "decision": res.get("confidence", 0) > 0.5 and "决策" or "",
                "confidence": res.get("confidence", 0.5),
                "is_exploration": res.get("is_exploration", False),
            }

            components = auto_evaluate(decision)
            raw_score = components["final_score"]

            biased_score = anti_bias_check(decision, raw_score)
            final_score = biased_score

            log_eval(
                res["decision_id"],
                final_score,
                {
                    "rule_score": components["rule_score"],
                    "llm_score": components["llm_score"],
                    "bias_adjusted": biased_score != raw_score,
                    "case": res["case"],
                    "pattern": res["used_pattern"],
                    "is_exploration": res.get("is_exploration", False),
                    "exploration_bonus": components.get("exploration_bonus", 0),
                },
            )

            round_scores.append(final_score)

            if verbose:
                pat = res["used_pattern"] or "无"
                conf = res["confidence"]
                is_exp = res.get("is_exploration", False)
                exp_icon = "🚀" if is_exp else "  "
                bias_icon = (
                    "↓降权"
                    if biased_score != raw_score
                    else (
                        "⭐探索"
                        if is_exp and components.get("exploration_bonus", 0)
                        else "✅"
                    )
                )
                print(
                    f"  {exp_icon} {res['case'][:13]:<13} | "
                    f"Pattern:{pat or '—':<12} | "
                    f"置信度:{conf:.2f} | "
                    f"评分:{final_score:.3f} "
                    f"({bias_icon})"
                )

        avg = sum(round_scores) / len(round_scores) if round_scores else 0
        if verbose:
            print(f"  平均分: {avg:.3f}")

        all_results.append(
            {
                "round": round_num,
                "scores": round_scores,
                "avg": round(avg, 4),
                "decisions": round_results,
            }
        )

        time.sleep(0.5)

    print(f"\n{'=' * 60}")
    print(f"  📊 训练汇总 ({rounds}轮)")
    print(f"{'=' * 60}")

    total_scores = [s for r in all_results for s in r["scores"]]
    overall_avg = sum(total_scores) / len(total_scores) if total_scores else 0
    print(f"  总决策数: {len(total_scores)}")
    print(f"  总体平均分: {overall_avg:.3f}")
    print(f"  最高分: {max(total_scores):.3f}")
    print(f"  最低分: {min(total_scores):.3f}")

    total_explorations = sum(
        1 for r in all_results for d in r["decisions"] if d.get("is_exploration", False)
    )
    print(
        f"  探索次数: {total_explorations} ({total_explorations / len(total_scores) * 100:.1f}%)"
        if total_scores
        else ""
    )

    trend = get_score_trend(window=min(len(total_scores), 20))
    print(f"  趋势: {trend['trend']} (变化: {trend['change']:+.3f})")

    patterns = get_all_patterns()
    print(f"\n  Pattern状态:")
    for p in patterns:
        print(
            f"    {p['id']}: score={p['score']:.4f} | usage={p.get('usage_count', 0)}次"
        )

    return {
        "rounds": rounds,
        "total_decisions": len(total_scores),
        "overall_avg": round(overall_avg, 4),
        "trend": trend,
        "round_results": all_results,
        "patterns": patterns,
        "exploration_count": total_explorations,
    }


def main():
    import sys

    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    run_training_loop(rounds=rounds, verbose=True)


if __name__ == "__main__":
    main()
