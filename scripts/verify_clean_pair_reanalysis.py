#!/usr/bin/env python3
"""Check the feature effects in matched pairs, on all pairs and on clean pairs.

Act rates come from the 7,800 released decisions (five trials per scenario and
model; invalid outputs count as not acting). The pair review in
results/pair_construct_audit/pair_audit_table.csv marks 13 of the 24 stakes
and reversibility pairs as also changing something besides the target feature.
Reported in the paper: on all pairs, irreversibility lowers the act rate by
16.7 to 63.3 points and higher stakes by 0 to 65.0 points; on clean pairs,
GPT-5.6 Sol's stakes effect drops from 41.7 to 12.0 points and Claude Sonnet 5
and Claude Opus 4.8 rise to 76.0 and 100 points. No model or network calls.
"""
from __future__ import annotations

from collections import defaultdict
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "data/derived/decision_by_scenario_trial.csv"
PAIRS = ROOT / "results/pair_construct_audit/pair_audit_table.csv"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def pts(x: float) -> str:
    return f"{round(100 * x, 1) + 0.0:.1f}"


def main() -> int:
    pairs = read(PAIRS)
    if len(pairs) != 48:
        fail("expected 48 matched pairs")
    trials = defaultdict(list)
    for r in read(DECISIONS):
        trials[(r["endpoint"], r["scenario_id"])].append(r["canonical_decision"] == "ACT")
    models = sorted({m for m, _ in trials})
    if len(models) != 10 or any(len(v) != 5 for v in trials.values()):
        fail("expected ten models with five trials per scenario")
    act = {k: sum(v) / len(v) for k, v in trials.items()}

    def effect(model: str, rows: list[dict[str, str]]) -> float:
        # Mean drop in act rate from the low to the high variant.
        return sum(act[(model, p["low_scenario_id"])] - act[(model, p["high_scenario_id"])] for p in rows) / len(rows)

    confounded = [p for p in pairs if p["classification"] == "CONFOUNDED_FACTOR_MANIPULATION"]
    by_factor = defaultdict(int)
    for p in confounded:
        by_factor[p["factor"]] += 1
    if dict(by_factor) != {"stakes": 7, "reversibility": 6}:
        fail(f"unexpected confounded pairs: {dict(by_factor)}")

    full, clean = {}, {}
    for factor in ("scope", "stakes", "reversibility", "external_visibility"):
        rows = [p for p in pairs if p["factor"] == factor]
        kept = [p for p in rows if p["classification"] == "CLEAN_FACTOR_MANIPULATION"]
        if len(rows) != 12:
            fail(f"{factor}: expected 12 pairs")
        full[factor] = {m: effect(m, rows) for m in models}
        clean[factor] = {m: effect(m, kept) for m in models}

    checks = {
        "scope drop range": ((pts(min(full["scope"].values())), pts(max(full["scope"].values()))), ("78.3", "100.0")),
        "reversibility drop range": ((pts(min(full["reversibility"].values())), pts(max(full["reversibility"].values()))), ("16.7", "63.3")),
        "stakes drop range": ((pts(min(full["stakes"].values())), pts(max(full["stakes"].values()))), ("0.0", "65.0")),
        # The paper reports visibility as the change in act rate (high minus low).
        "visibility change range": ((pts(-max(full["external_visibility"].values())), pts(-min(full["external_visibility"].values()))), ("-16.7", "1.7")),
        "Sol stakes, all pairs": (pts(full["stakes"]["GPT-5.6 Sol"]), "41.7"),
        "Sol stakes, clean pairs": (pts(clean["stakes"]["GPT-5.6 Sol"]), "12.0"),
        "Sonnet 5 stakes, clean pairs": (pts(clean["stakes"]["Claude Sonnet 5"]), "76.0"),
        "Opus 4.8 stakes, clean pairs": (pts(clean["stakes"]["Claude Opus 4.8"]), "100.0"),
    }
    for name, (got, expected) in checks.items():
        if got != expected:
            fail(f"{name}: got {got}, paper {expected}")

    print("VERIFIED: 13 of 24 stakes and reversibility pairs confounded (7 stakes, 6 reversibility)")
    for name, (got, _) in checks.items():
        print(f"  {name}: {got}")
    print("Stakes effect (points), all 12 pairs -> 5 clean pairs:")
    for m in models:
        print(f"  {m:22s} {pts(full['stakes'][m]):>6s} -> {pts(clean['stakes'][m]):>6s}")
    print("Reversibility effect (points), all 12 pairs -> 6 clean pairs:")
    for m in models:
        print(f"  {m:22s} {pts(full['reversibility'][m]):>6s} -> {pts(clean['reversibility'][m]):>6s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
