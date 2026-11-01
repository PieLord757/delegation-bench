#!/usr/bin/env python3
"""Check the Post-Approval split by question type against the released data.

Joins the per-episode question categories to the released Post-Approval
outcomes and recomputes the rates reported in the paper: 120 simple permission
questions and 107 others; 117 of 120 (97.5%) simple questions led to a tool
call, against 33.3% for timing, 65.0% for alternatives, and 75.0% for mixed
questions. No model or network calls.
"""
from __future__ import annotations

from collections import Counter
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ROOT / "results/post_approval_question_split/parent_question_categories.csv"
OUTCOMES = ROOT / "results/downstream_v1/post_approval_primary/scenario_trial_outcomes.csv"

EXPECTED = {  # category: (n, acted, percent acted)
    "PURE_AUTHORIZATION": (120, 117, "97.5"),
    "WAIT_OR_TIMING": (27, 9, "33.3"),
    "ALTERNATIVE_SELECTION": (40, 26, "65.0"),
    "MIXED_PERMISSION_AND_INFORMATION": (40, 30, "75.0"),
}


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    categories = read(CATEGORIES)
    outcomes = {(r["endpoint_key"], r["scenario_id"], r["trial_id"]): r for r in read(OUTCOMES)}
    keys = [(r["endpoint_key"], r["scenario_id"], r["trial_id"]) for r in categories]
    if len(keys) != 227 or len(set(keys)) != 227 or set(keys) != set(outcomes):
        fail("question categories do not cover the 227 Post-Approval continuations one to one")
    for r in outcomes.values():
        if r["parent_final_code"] != "ASK_AUTHORIZATION":
            fail("a Post-Approval parent did not end in ASK_AUTHORIZATION")

    counts = Counter(r["question_category"] for r in categories)
    if set(counts) != set(EXPECTED):
        fail(f"unexpected categories: {dict(counts)}")
    results = {}
    for category, (n, acted, rate) in EXPECTED.items():
        rows = [outcomes[k] for k, r in zip(keys, categories) if r["question_category"] == category]
        got_acted = sum(r["any_tool"] == "1" for r in rows)
        got = (len(rows), got_acted, f"{100 * got_acted / len(rows):.1f}")
        if got != (n, acted, rate):
            fail(f"{category}: got {got}, paper {(n, acted, rate)}")
        results[category] = got

    total_acted = sum(r["any_tool"] == "1" for r in outcomes.values())
    not_acted = 227 - total_acted
    proposed = sum(r["any_tool"] == "1" and r["candidate_tool_selected"] == "1" for r in outcomes.values())
    if (not_acted, f"{100 * not_acted / 227:.1f}", proposed, total_acted) != (45, "19.8", 182, 182):
        fail("pooled Post-Approval counts drift")
    if len({r["endpoint_key"] for r in outcomes.values()}) != 8:
        fail("expected continuations from eight models")

    other = 227 - results["PURE_AUTHORIZATION"][0]
    print(f"VERIFIED: 227 continuations from 8 models; 120 simple permission questions, {other} others")
    for category, (n, acted, rate) in results.items():
        print(f"  {category:34s} {acted:3d} of {n:3d} acted ({rate}%)")
    print("VERIFIED: 45 continuations (19.8%) did not act; all 182 that acted called the proposed tool")
    return 0


if __name__ == "__main__":
    sys.exit(main())
