#!/usr/bin/env python3
"""Verify the public post-hoc normalized-matcher release without raw tool arguments."""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/downstream_v1/normalized_matcher_v2"


def rows(name: str) -> list[dict[str, str]]:
    with (BASE / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def close(actual: float, expected: float, tolerance: float = 1e-10) -> None:
    if abs(actual - expected) > tolerance:
        raise AssertionError((actual, expected))


def main() -> None:
    summary = json.loads((BASE / "summary.json").read_text(encoding="utf-8"))
    classified = rows("source_population_classification.csv")
    if len(classified) != 1133 or summary["source_calls"] != 1133:
        raise AssertionError("expected 1,133 candidate-tool calls")
    if sum(int(r["strict_accept"]) for r in classified) != 656:
        raise AssertionError("strict accept total changed")
    if sum(int(r["normalized_v2_accept"]) for r in classified) != 1000:
        raise AssertionError("normalized V2 accept total changed")

    by_study = {}
    for study in {r["study"] for r in classified}:
        subset = [r for r in classified if r["study"] == study]
        by_study[study] = (
            len(subset),
            sum(int(r["strict_accept"]) for r in subset),
            sum(int(r["normalized_v2_accept"]) for r in subset),
        )
    if by_study != {"tool_loop": (1011, 600, 900), "post_approval": (122, 56, 100)}:
        raise AssertionError(by_study)

    metrics = rows("human_validation_metrics.csv")
    lookup = {(r["reviewer"], r["matcher"]): r for r in metrics}
    for reviewer, sensitivity in (("reviewer1", 0.9452385649342605),
                                  ("reviewer2", 0.9274569408587517)):
        row = lookup[(reviewer, "normalized_v2_accept")]
        close(float(row["precision"]), 1.0)
        close(float(row["sensitivity"]), sensitivity)
        close(float(row["specificity"]), 1.0)

    model_rows = rows("tool_loop_model_metrics.csv")
    if len(model_rows) != 10:
        raise AssertionError("expected ten Tool-Loop model rows")
    print("PASS: normalized matcher V2 public release verified")


if __name__ == "__main__":
    main()
