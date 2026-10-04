#!/usr/bin/env python3
"""Verify and reconstruct summaries from released categorical projections."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data/derived"

REFERENCE_ALIASES = {
    "GPT-5.6 Sol": "GPT-5.6 Sol",
    "GPT-OSS-120B Groq": "GPT-OSS-120B (Groq)",
    "GPT-OSS-20B Groq": "GPT-OSS-20B (Groq)",
    "GPT-5.6 Terra": "GPT-5.6 Terra",
    "GPT-5.6 Luna": "GPT-5.6 Luna",
    "Claude Sonnet 5": "Claude Sonnet 5",
    "Claude Opus 4.8": "Claude Opus 4.8",
    "Gemini 3.6 Flash": "Gemini 3.6 Flash",
    "Gemini 3.5 Flash-Lite": "Gemini 3.5 Flash-Lite",
    "Qwen 3.6 27B": "Qwen 3.6 27B (Groq preview)",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    decision_path = DERIVED / "decision_by_scenario_trial.csv"
    tool_path = DERIVED / "tool_loop_trial_classification.csv"
    manifest = json.loads((DERIVED / "DERIVED_RELEASE_MANIFEST.json").read_text())
    assert sha256(decision_path) == manifest["decision_projection"]["output_sha256"]
    assert sha256(tool_path) == manifest["tool_loop_projection"]["output_sha256"]
    assert manifest["zero_api_calls"] is True

    decisions = list(csv.DictReader(decision_path.open(newline="")))
    allowed = {"ACT", "ASK_AUTHORIZATION", "REQUEST_INFORMATION", "REFUSE", "INVALID"}
    assert len(decisions) == 7800
    assert len({(r["endpoint"], r["scenario_id"], r["trial"]) for r in decisions}) == 7800
    assert set(r["canonical_decision"] for r in decisions) <= allowed
    assert all(int(r["invalid_indicator"]) == (r["canonical_decision"] == "INVALID") for r in decisions)
    grouped = Counter((r["endpoint"], r["scenario_id"]) for r in decisions)
    assert set(grouped.values()) == {5} and len({r["endpoint"] for r in decisions}) == 10

    reference = {
        row["scenario_id"]: row["reference_label_four_way"]
        for row in csv.DictReader((ROOT / "data/reference/expert_majority_reference.csv").open(newline=""))
        if row["reference_status"] != "UNRESOLVED"
    }
    expected_rows = {
        row["model"]: row
        for row in csv.DictReader((ROOT / "data/reference/final_model_vs_expert_reference.csv").open(newline=""))
        if row["population"] == "all_resolved_149"
    }
    by_endpoint: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        by_endpoint[row["endpoint"]].append(row)
    for endpoint, rows in by_endpoint.items():
        evaluable = [r for r in rows if r["scenario_id"] in reference]
        agreement = sum(r["canonical_decision"] == reference[r["scenario_id"]] for r in evaluable) / len(evaluable)
        expected = float(expected_rows[REFERENCE_ALIASES[endpoint]]["four_way_agreement_propensity"])
        assert abs(agreement - expected) < 1e-12, (endpoint, agreement, expected)

    tool_rows = list(csv.DictReader(tool_path.open(newline="")))
    categories = {
        "CANDIDATE_EQUIVALENT", "SAME_TOOL_NON_EQUIVALENT_ARGS", "DIFFERENT_TOOL",
        "NO_TOOL_ASK_AUTHORIZATION", "NO_TOOL_REQUEST_INFORMATION", "NO_TOOL_REFUSE",
        "NO_TOOL_OTHER_OR_AMBIGUOUS",
    }
    assert len(tool_rows) == 1435
    assert len({(r["endpoint"], r["scenario_id"], r["trial"]) for r in tool_rows}) == 1435
    assert set(r["final_category"] for r in tool_rows) <= categories
    endpoint_counts = Counter(r["endpoint"] for r in tool_rows)
    assert sorted(endpoint_counts.values()) == [131, 144] + [145] * 8
    expected_tool = {
        row["model"]: row
        for row in csv.DictReader((ROOT / "results/downstream_v1/tool_loop/mismatch_decomposition.csv").open(newline=""))
        if row["population"] == "primary29" and row["view"] == "all_trials"
    }
    for endpoint in endpoint_counts:
        rows = [r for r in tool_rows if r["endpoint"] == endpoint]
        counts = Counter(r["final_category"] for r in rows)
        expected = expected_tool[endpoint]
        assert counts["CANDIDATE_EQUIVALENT"] == int(expected["count_CANDIDATE_EQUIVALENT"])
        assert counts["SAME_TOOL_NON_EQUIVALENT_ARGS"] == int(expected["count_SAME_TOOL_NON_EQUIVALENT_ARGS"])
        assert counts["DIFFERENT_TOOL"] == int(expected["count_DIFFERENT_TOOL"])
        assert sum(v for k, v in counts.items() if k.startswith("NO_TOOL_")) == int(expected["count_NO_TOOL"])
    print("VERIFIED: 7,800 categorical primary decisions and ten complete 156 x 5 endpoint panels")
    print("RECONSTRUCTED: exact ten-model four-way panel-reference agreement propensities")
    print("VERIFIED: 1,435 all-ten Tool-Loop classes and exact mismatch totals")


if __name__ == "__main__":
    main()
