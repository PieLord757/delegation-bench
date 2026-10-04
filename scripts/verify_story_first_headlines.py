#!/usr/bin/env python3
"""Verify the three story-first headline claims from released derived tables."""
from __future__ import annotations

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT


def rows(path: str) -> list[dict[str, str]]:
    with (DATA_ROOT / path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def close(value: str, expected: float, tolerance: float = 1e-9) -> None:
    if not math.isclose(float(value), expected, abs_tol=tolerance):
        raise AssertionError(f"{value} != {expected}")


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    result = [0.0] * len(values)
    for rank, index in enumerate(order, 1):
        result[index] = float(rank)
    return result


def correlation(a: list[float], b: list[float]) -> float:
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den


def main() -> None:
    policy = rows("results/policy_consistency_lexical_audit/policy_consistency_rule_model_comparison.csv")
    compact = next(row for row in policy if row["policy"] == "Compact visible rule")
    close(compact["primary_four_way_agreement"], 0.6912751677852349)
    close(compact["mean_core_expected_rate"], 9 / 48)

    rank = rows("results/downstream_v1/tool_loop/model_rank_correspondence.csv")[0]
    close(rank["spearman"], -0.7575757575757575)
    close(rank["pairwise_order_preservation"], 0.2)

    stages = rows("results/story_first/action_stage_profile.csv")
    if len(stages) != 10:
        raise AssertionError(f"expected 10 action-stage rows, got {len(stages)}")
    if not all(float(row["candidate_tool_rate"]) > float(row["candidate_equivalent_rate"]) for row in stages):
        raise AssertionError("candidate-tool must exceed candidate-equivalent for every model")
    offline = [float(row["offline_act_rate"]) for row in stages]
    candidate_tool = [float(row["candidate_tool_rate"]) for row in stages]
    close(str(correlation(ranks(offline), ranks(candidate_tool))), -0.49090909090909085)
    preserved = [
        (offline[i] - offline[j]) * (candidate_tool[i] - candidate_tool[j]) > 0
        for i in range(10) for j in range(i + 1, 10)
    ]
    close(str(sum(preserved) / len(preserved)), 1 / 3)

    ask = rows("results/story_first/offline_vs_tool_loop_ask.csv")
    if len(ask) != 10 or not all(float(row["absolute_change_pp"]) < 0 for row in ask):
        raise AssertionError("expected lower Tool-Loop ASK on the same 48 scenarios for all ten endpoints")
    gaps = sorted(-float(row["absolute_change_pp"]) for row in ask)
    close(str(gaps[-1]), 43.333333333333336)
    close(str(gaps[-2]), 33.333333333333336)

    pa = [row for row in rows("results/downstream_v1/post_approval/stage_comparison.csv") if row["analysis_status"] == "primary_complete_parent"]
    if len(pa) != 8 or sum(int(row["continuation_valid"]) for row in pa) != 227:
        raise AssertionError("expected eight complete-parent endpoints and 227 valid continuations")
    action_rates = [float(row["post_approval_any_tool_rate"]) for row in pa]
    if min(action_rates) < 2 / 3 - 1e-9 or max(action_rates) != 1.0:
        raise AssertionError("unexpected post-approval action range")

    panel = rows("results/panel_leave_one_out/leave_one_out_panel_agreement.csv")
    four_way = [float(row["four_way_agreement"]) for row in panel]
    if len(panel) != 3 or min(four_way) < 0.738 - 0.001 or max(four_way) > 0.798 + 0.001:
        raise AssertionError("unexpected leave-one-annotator-out range")

    validity = [
        row for row in rows("results/downstream_v1/measurement_robustness/panel_validity_metrics.csv")
        if row["population"] == "all_48" and row["invalid_handling"] == "retained_primary"
    ]
    by_endpoint: dict[str, dict[str, float]] = {}
    for row in validity:
        by_endpoint.setdefault(row["endpoint_key"], {})[row["condition"]] = float(row["multiclass_brier"])
    if len(by_endpoint) != 10:
        raise AssertionError(f"expected 10 elicitation endpoints, got {len(by_endpoint)}")
    improved = 0
    best = 0
    for metrics in by_endpoint.values():
        balanced = metrics["balanced_option_order"]
        if balanced < metrics["frozen_original"]:
            improved += 1
        if balanced == min(metrics.values()):
            best += 1
    if (improved, best) != (10, 9):
        raise AssertionError(f"balanced-order counts were {(improved, best)}, expected (10, 9)")

    print("PASS: compact rule = 69.1% and 9/48 controlled pairs")
    print("PASS: candidate-tool ordering rho = -0.491; pairwise preservation = 33.3%")
    print("PASS: historical strict-rule rho = -0.758 is preserved as a diagnostic")
    print("PASS: Tool-Loop ASK is lower than same-48 offline ASK for all ten endpoints")
    print("PASS: post-approval primary = 8 endpoints and 227 valid continuations")
    print("PASS: balanced order improves Brier for 10/10 and is best for 9/10")
    print("PASS: leave-one-annotator-out four-way range = 73.8%-79.8%")


if __name__ == "__main__":
    main()
