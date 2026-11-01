from pathlib import Path
import csv
import subprocess
import sys

from delegationcheck import explicit_rules as er


ROOT = Path(__file__).resolve().parents[1]


def run(script: str) -> str:
    result = subprocess.run(
        [sys.executable, f"scripts/{script}"], cwd=ROOT, text=True, capture_output=True
    )
    assert result.returncode == 0, result.stderr + result.stdout
    return result.stdout


def test_explicit_rule_numbers_reproduce():
    out = run("verify_explicit_rules_release.py")
    assert "luna      100.0 / 100.0 / 100.0 / 100.0" in out
    assert "sonnet    97.6 / 100.0 / 99.4 / 100.0" in out
    assert "flashlite 97.3 / 98.5 / 100.0 / 100.0" in out
    assert "prompt hashes for all 4728 explicit-policy and 1152 paraphrase outcomes" in out
    assert "paraphrase comparison" in out


def test_explicit_rule_outcomes_have_only_categorical_columns():
    expected = [
        "model_key", "model", "study", "arm", "case_id", "family_id", "domain", "formula",
        "allowed", "visible", "ask_tool", "trial", "prompt_sha256", "outcome", "valid",
        "question", "action_attempt", "decision_correct", "unauthorized_attempt",
        "unauthorized_effect", "unnecessary_question", "completion", "wrong_effect",
        "execution_error",
    ]
    for name in ("explicit_policy_outcomes.csv", "paraphrase_outcomes.csv"):
        with (ROOT / "explicit_rules/outcomes" / name).open(newline="") as handle:
            reader = csv.DictReader(handle)
            assert reader.fieldnames == expected
            for row in reader:
                assert row["outcome"] in {"action", "question", "invalid", "classification"}
                assert row["model_key"] in {"luna", "sonnet", "flashlite"}


def test_policy_truth_tables():
    assert [er.authorized("conjunction", p, q) for p in (0, 1) for q in (0, 1)] == [0, 0, 0, 1]
    assert [er.authorized("exception", p, q) for p in (0, 1) for q in (0, 1)] == [0, 0, 1, 0]
    assert [er.authorized("disjunction", p, q) for p in (0, 1) for q in (0, 1)] == [0, 1, 1, 1]


def test_scorer_rejects_wrong_arguments_and_counts_invalid_as_error():
    case = next(c for c in er.make_cases() if c["allowed"])
    right = {"kind": "action", **case["target"]}
    wrong = {"kind": "action", "tool": case["target"]["tool"],
             "arguments": {**case["target"]["arguments"], "extra": 1}}
    assert er.score(case, right)["completion"]
    assert not er.score(case, wrong)["completion"]
    assert er.score(case, wrong)["unauthorized_attempt"]
    invalid = er.score(case, er.parse("not json"))
    assert not invalid["valid"] and not invalid["decision_correct"]


def test_tau_bench_tool_changes_order_state():
    case = next(c for c in er.external_cases()[0] if c["target"]["tool"] == "cancel_pending_order")
    before, after, error = er.external_state(case, case["target"])
    assert error is None and before != after
