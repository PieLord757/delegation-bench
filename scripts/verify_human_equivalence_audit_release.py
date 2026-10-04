#!/usr/bin/env python3
"""Recompute candidate-equivalence audit point estimates from safe categories."""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT
PATH = DATA_ROOT / "results/downstream_v1/human_equivalence_audit/audit_categorical_join.csv"
TWO_REVIEWER_PATH = DATA_ROOT / "results/downstream_v1/human_equivalence_audit/two_reviewer_categorical_join.csv"


def close(actual: float, expected: float) -> None:
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-12):
        raise AssertionError(f"{actual} != {expected}")


def main() -> None:
    with PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 200 or len({r["audit_case_id"] for r in rows}) != 200:
        raise AssertionError("expected 200 unique audit rows")
    forbidden = {"user_instruction", "context", "candidate_arguments", "actual_arguments", "human_rationale", "model"}
    if forbidden.intersection(rows[0]):
        raise AssertionError("provider text or private human rationale leaked into categorical release")
    for row in rows:
        row["weight"] = float(row["weight"])
    total = sum(r["weight"] for r in rows)
    accepted = [r for r in rows if r["rule"] == "ACCEPTED"]
    rejected = [r for r in rows if r["rule"] == "REJECTED"]
    accepted_weight = sum(r["weight"] for r in accepted)
    rejected_weight = sum(r["weight"] for r in rejected)
    precision = sum(r["weight"] for r in accepted if r["human"] == "EQUIVALENT") / accepted_weight
    false_rejection = sum(r["weight"] for r in rejected if r["human"] == "EQUIVALENT") / rejected_weight
    human_equivalent = sum(r["weight"] for r in rows if r["human"] == "EQUIVALENT") / total
    rule_agreement = sum(
        r["weight"] for r in rows
        if (r["rule"] == "ACCEPTED" and r["human"] == "EQUIVALENT")
        or (r["rule"] == "REJECTED" and r["human"] == "NOT_EQUIVALENT")
    ) / total
    tool = [r for r in rows if r["study"] == "tool_loop"]
    tool_semantic = sum(r["weight"] for r in tool if r["human"] == "EQUIVALENT") / sum(r["weight"] for r in tool)
    close(total, 1133.0)
    close(precision, 1.0)
    close(false_rejection, 0.8713066574701795)
    close(human_equivalent, 0.9458193076904463)
    close(rule_agreement, 0.6199353260253525)
    close(tool_semantic, 0.9392811826046248)
    print("PASS: 200 unique blinded-audit judgments")
    print("PASS: strict ACCEPT precision = 100.0%")
    print("PASS: weighted strict REJECT false-rejection fraction = 87.1%")
    print("PASS: weighted Tool-Loop semantic correspondence among candidate-tool calls = 93.9%")

    with TWO_REVIEWER_PATH.open(newline="", encoding="utf-8") as handle:
        paired = list(csv.DictReader(handle))
    if len(paired) != 200 or len({r["audit_case_id"] for r in paired}) != 200:
        raise AssertionError("expected 200 unique two-reviewer audit rows")
    if forbidden.intersection(paired[0]) or {"reviewer1_rationale", "reviewer2_rationale"}.intersection(paired[0]):
        raise AssertionError("private text or rationale leaked into two-reviewer release")
    raw_agreement = sum(r["reviewer1_equivalence"] == r["reviewer2_equivalence"] for r in paired) / len(paired)
    for row in paired:
        row["sampling_weight"] = float(row["sampling_weight"])
    total = sum(r["sampling_weight"] for r in paired)
    reviewer2_semantic = sum(
        r["sampling_weight"] for r in paired if r["reviewer2_equivalence"] == "EQUIVALENT"
    ) / total
    rejected = [r for r in paired if r["deterministic_rule_class"] == "REJECTED"]
    reviewer2_false_rejection = sum(
        r["sampling_weight"] for r in rejected if r["reviewer2_equivalence"] == "EQUIVALENT"
    ) / sum(r["sampling_weight"] for r in rejected)
    tool = [r for r in paired if r["study"] == "tool_loop"]
    reviewer2_tool_semantic = sum(
        r["sampling_weight"] for r in tool if r["reviewer2_equivalence"] == "EQUIVALENT"
    ) / sum(r["sampling_weight"] for r in tool)
    close(raw_agreement, 0.97)
    close(reviewer2_semantic, 0.9639529833704591)
    close(reviewer2_false_rejection, 0.9143788892216566)
    close(reviewer2_tool_semantic, 0.9596030961016124)
    print("PASS: two-reviewer raw equivalence agreement = 97.0%")
    print("PASS: Reviewer 2 weighted strict REJECT false-rejection fraction = 91.4%")
    print("PASS: Reviewer 2 weighted Tool-Loop semantic correspondence = 96.0%")


if __name__ == "__main__":
    main()
