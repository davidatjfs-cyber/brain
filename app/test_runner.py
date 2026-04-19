#!/usr/bin/env python3
import sys
import time
import json
from app.test_cases import TEST_CASES
from app.test_engine import (
    run_batch_tests,
    stability_test,
    evaluate_decision,
    calculate_stats,
    compare_with_agent,
)


def print_banner():
    print("\n" + "=" * 60)
    print("  🧠  Brain V1 决策系统 — 测试模块")
    print("=" * 60)


def print_stats(stats, round_num=None):
    label = f"第 {round_num} 轮" if round_num else "统计结果"
    print(f"\n{'=' * 50}")
    print(f"  📊 {label} — 统计结果")
    print(f"{'=' * 50}")
    print(f"  总测试数 : {stats['total']}")
    print(
        f"  平均分   : {stats['avg_score']:.4f}  {'✅ 达标' if stats['avg_score'] >= 0.7 else '❌ 未达标'}"
    )
    print(f"  通过数   : {stats['passed']} / {stats['total']}")
    print(f"  通过率   : {stats['pass_rate'] * 100:.1f}%")
    print(f"  分数列表 : {[round(s, 3) for s in stats['scores']]}")
    print(f"{'=' * 50}")


def run_manual_scoring(results):
    print("\n" + "=" * 60)
    print("  ✏️  人工评分（0~1分）")
    print("  说明: 0.7分以上为合格，评估决策质量、可执行性、风险控制")
    print("=" * 60)

    scores = []
    for r in results:
        if not r.get("decision"):
            print(f"  ⚠️ 跳过 {r['name']}（决策生成失败）")
            continue

        d = r["decision"]
        print(f"\n场景: {r['name']}")
        print(f"  问题: {d.get('problem', '')[:60]}")
        print(f"  决策: {d.get('decision', '')[:60]}")
        print(f"  动作: {' | '.join(d.get('actions', [])[:2])}")
        print(f"  风险: {d.get('risk_level')} | LLM置信度: {d.get('confidence')}")

        while True:
            try:
                raw = input("  人工评分 (0~1，q跳过): ").strip()
                if raw.lower() == "q":
                    print("  → 跳过")
                    break
                score = float(raw)
                if 0 <= score <= 1:
                    comment = input("  评价 (回车跳过): ").strip()
                    ev_result = evaluate_decision(
                        r["decision_id"],
                        {
                            "revenue_change": score * 0.4,
                            "profit_change": score * 0.3,
                            "turnover_change": score * 0.3,
                        },
                        comment or "",
                    )
                    scores.append(score)
                    print(
                        f"  ✅ 记录: {score} | {ev_result.get('evaluation', {}).get('final_judgement', '—')}"
                    )
                    break
                else:
                    print("  ⚠️ 请输入 0~1 之间的数字")
            except ValueError:
                print("  ⚠️ 无效输入，请输入数字或 q")

    return scores


def run_full_test_rounds(num_rounds=3):
    print_banner()
    print(f"\n📋 测试集: {len(TEST_CASES)} 条测试场景")
    print(f"🔄 测试轮次: {num_rounds} 轮")
    print(f"🎯 达标线: 平均分 ≥ 0.7")

    all_scores = []
    round_stats = []

    for round_num in range(1, num_rounds + 1):
        print(f"\n\n{'#' * 60}")
        print(f"  🔵 第 {round_num} / {num_rounds} 轮测试开始")
        print(f"{'#' * 60}")

        results = run_batch_tests(TEST_CASES, delay=1)

        round_scores = run_manual_scoring(results)
        if not round_scores:
            print("  ⚠️ 本轮无有效评分，跳过统计")
            continue

        all_scores.extend(round_scores)
        stats = calculate_stats(round_scores)
        round_stats.append({"round": round_num, **stats})
        print_stats(stats, round_num)

    print(f"\n\n{'#' * 60}")
    print(f"  📈 整体汇总 (共 {num_rounds} 轮)")
    print(f"{'#' * 60}")

    if all_scores:
        overall = calculate_stats(all_scores)
        print_stats(overall)
        for rs in round_stats:
            bar = "█" * int(rs["avg_score"] * 20) + "░" * (
                20 - int(rs["avg_score"] * 20)
            )
            print(
                f"  轮次 {rs['round']}: [{bar}] {rs['avg_score']:.3f}  {'✅' if rs['avg_score'] >= 0.7 else '❌'}"
            )
    else:
        print("  ⚠️ 无评分数据")

    print(f"\n{'=' * 60}")
    print(f"  🏁 测试完成！")
    print(f"{'=' * 60}")

    return round_stats


def run_stability_check():
    print_banner()
    print("\n🧪 稳定性测试（同一场景运行3次）\n")

    stability_test(TEST_CASES[0], times=3, delay=1)


def run_quick_test(n=3):
    print_banner()
    print(f"\n⚡ 快速测试（前 {n} 条场景）\n")
    results = run_batch_tests(TEST_CASES[:n], delay=0)
    scores = run_manual_scoring(results)
    if scores:
        stats = calculate_stats(scores)
        print_stats(stats)


def main():
    print_banner()
    print("\n选择测试模式:")
    print("  1) 完整测试 (3轮 × 10场景 × 人工评分)")
    print("  2) 快速测试 (3场景)")
    print("  3) 稳定性测试")
    print("  4) 仅生成决策（不评分）")
    print("  5) 退出")

    choice = input("\n请输入选项 [1-5]: ").strip()

    if choice == "1":
        run_full_test_rounds(3)
    elif choice == "2":
        run_quick_test(3)
    elif choice == "3":
        run_stability_check()
    elif choice == "4":
        print_banner()
        print(f"\n⚡ 仅生成决策（前5条场景）\n")
        results = run_batch_tests(TEST_CASES[:5], delay=0)
        print(f"\n✅ 完成 {len(results)} 条决策生成")
    elif choice == "5":
        print("再见！")
    else:
        print("无效选项")


if __name__ == "__main__":
    main()
