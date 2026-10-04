#!/usr/bin/env python3
"""Reconstruct the released Tool-Loop summary from its non-textual trial view."""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results/tool_loop_three_stage/three_stage_trial_paths.csv"
EXPECTED = ROOT / "results/tool_loop_three_stage/three_stage_summary.csv"
FIELDS = [
    "condition", "n_trials", "p_offline_act", "p_candidate_tool_given_act",
    "p_equivalent_given_act_and_tool", "p_joint_act_tool_equivalent", "chain_product",
    "p_candidate_tool", "p_equivalent_given_tool", "p_equivalent",
    "p_candidate_tool_given_nonact", "p_equivalent_given_nonact_and_tool",
    "act_path_no_candidate_tool", "act_path_same_tool_bad_args",
]


def ratio(num: int, den: int) -> float:
    return num / den if den else float("nan")


def summarize(group: list[dict[str, str]]) -> dict[str, object]:
    values = [{k: int(v) for k, v in row.items() if k not in {"condition", "scenario_id", "trial_id"}} for row in group]
    n = len(values)
    act = sum(r["offline_act"] for r in values)
    nonact = n - act
    tool = sum(r["candidate_tool"] for r in values)
    equiv = sum(r["candidate_equivalent"] for r in values)
    act_tool = sum(r["offline_act"] and r["candidate_tool"] for r in values)
    act_equiv = sum(r["offline_act"] and r["candidate_equivalent"] for r in values)
    nonact_tool = sum((not r["offline_act"]) and r["candidate_tool"] for r in values)
    nonact_tool_equiv = sum((not r["offline_act"]) and r["candidate_tool"] and r["candidate_equivalent"] for r in values)
    p_act = ratio(act, n)
    p_tool_act = ratio(act_tool, act)
    p_equiv_act_tool = ratio(act_equiv, act_tool)
    return {
        "n_trials": n,
        "p_offline_act": p_act,
        "p_candidate_tool_given_act": p_tool_act,
        "p_equivalent_given_act_and_tool": p_equiv_act_tool,
        "p_joint_act_tool_equivalent": ratio(act_equiv, n),
        "chain_product": p_act * p_tool_act * p_equiv_act_tool,
        "p_candidate_tool": ratio(tool, n),
        "p_equivalent_given_tool": ratio(equiv, tool),
        "p_equivalent": ratio(equiv, n),
        "p_candidate_tool_given_nonact": ratio(nonact_tool, nonact),
        "p_equivalent_given_nonact_and_tool": ratio(nonact_tool_equiv, nonact_tool),
        "act_path_no_candidate_tool": ratio(sum(r["offline_act"] and r["no_candidate_tool"] for r in values), act),
        "act_path_same_tool_bad_args": ratio(sum(r["offline_act"] and r["same_tool_non_equivalent"] for r in values), act),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("reproduction_outputs/tool_loop_summary.csv"))
    args = parser.parse_args()
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in csv.DictReader(INPUT.open(newline="")):
        groups[row["condition"]].append(row)
    produced = [{"condition": condition, **summarize(group)} for condition, group in groups.items()]
    expected = {r["condition"]: r for r in csv.DictReader(EXPECTED.open(newline=""))}
    for row in produced:
        target = expected[row["condition"]]
        for field in FIELDS[1:]:
            if field == "n_trials":
                assert int(row[field]) == int(target[field])
            else:
                assert abs(float(row[field]) - float(target[field])) < 1e-12, (row["condition"], field)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(produced)
    print(f"RECONSTRUCTED AND MATCHED: {len(produced)} conditions; wrote {args.output.resolve()}")


if __name__ == "__main__":
    main()
