#!/usr/bin/env python3
"""Check the explicit-rule results in the paper against the released outcomes.

Covers the main-text table of balanced accuracy under explicit rules and the
appendix tables: policy format, ordinary-rule control, candidate visibility
and question interface, tau-bench decision points, development pilot, paired
contrasts, and the paraphrase comparison. Also checks that the released case
files and every prompt hash are reproduced by delegationcheck/explicit_rules.py
and that the vendored tau-bench files match their upstream hashes.

No model or network calls.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from delegationcheck import explicit_rules as er  # noqa: E402

BASE = ROOT / "explicit_rules"
MODELS = ("luna", "sonnet", "flashlite")
SCORE_FIELDS = (
    "valid", "question", "action_attempt", "decision_correct", "unauthorized_attempt",
    "unauthorized_effect", "unnecessary_question", "completion", "wrong_effect", "execution_error",
)

# Paper values, in percent, as printed (one decimal).
MAIN_TABLE = {  # natural, structured, decision given, tau-bench
    "luna": ("100.0", "100.0", "100.0", "100.0"),
    "sonnet": ("97.6", "100.0", "99.4", "100.0"),
    "flashlite": ("97.3", "98.5", "100.0", "100.0"),
}
# (study, arm): model -> (N, valid, balanced accuracy, unauthorized, completion)
ARM_TABLES = {
    ("generalization", "decision"): {"flashlite": (192, 192, "100.0", "0.0", "100.0"), "luna": (192, 192, "100.0", "0.0", "100.0"), "sonnet": (192, 192, "99.4", "0.0", "98.8")},
    ("generalization", "natural"): {"flashlite": (192, 189, "97.3", "0.0", "96.4"), "luna": (192, 192, "100.0", "0.0", "100.0"), "sonnet": (192, 192, "97.6", "0.0", "95.2")},
    ("generalization", "structured"): {"flashlite": (192, 189, "98.5", "0.0", "98.8"), "luna": (192, 192, "100.0", "0.0", "100.0"), "sonnet": (192, 192, "100.0", "0.0", "100.0")},
    ("ordinary_control", "ordinary"): {"flashlite": (192, 192, "100.0", None, None), "luna": (192, 192, "97.7", None, None), "sonnet": (192, 192, "98.1", None, None)},
    ("factorial", "visible0_asktool0"): {"flashlite": (144, 141, "97.9", "0.0", "100.0"), "luna": (144, 144, "100.0", "0.0", "100.0"), "sonnet": (144, 144, "100.0", "0.0", "100.0")},
    ("factorial", "visible0_asktool1"): {"flashlite": (144, 143, "99.3", "0.0", "100.0"), "luna": (144, 144, "100.0", "0.0", "100.0"), "sonnet": (144, 144, "100.0", "0.0", "100.0")},
    ("factorial", "visible1_asktool0"): {"flashlite": (144, 144, "100.0", "0.0", "100.0"), "luna": (144, 144, "100.0", "0.0", "100.0"), "sonnet": (144, 142, "98.6", "0.0", "97.2")},
    ("factorial", "visible1_asktool1"): {"flashlite": (144, 140, "97.2", "0.0", "97.2"), "luna": (144, 144, "100.0", "0.0", "100.0"), "sonnet": (144, 144, "100.0", "0.0", "100.0")},
    ("transfer", "natural"): {m: (68, 68, "100.0", "0.0", "100.0") for m in MODELS},
    ("transfer", "structured"): {m: (68, 68, "100.0", "0.0", "100.0") for m in MODELS},
    ("pilot", "decision"): {m: (32, 32, "100.0", "0.0", "100.0") for m in MODELS},
    ("pilot", "natural"): {m: (32, 32, "100.0", "0.0", "100.0") for m in MODELS},
    ("pilot", "structured"): {"flashlite": (32, 31, "97.2", "0.0", "100.0"), "luna": (32, 32, "100.0", "0.0", "100.0"), "sonnet": (32, 32, "100.0", "0.0", "100.0")},
}
# model -> list of (label, estimate, low, high), percentage points
CONTRASTS = {
    "luna": [("structured-natural/family", "0.0", "0.0", "0.0"), ("structured-natural/domain", "0.0", "0.0", "0.0"),
             ("visibility", "0.0", "0.0", "0.0"), ("ask_tool", "0.0", "0.0", "0.0"), ("interaction", "0.0", "0.0", "0.0"),
             ("tau structured-natural/task", "0.0", "0.0", "0.0")],
    "sonnet": [("structured-natural/family", "2.1", "0.0", "5.2"), ("structured-natural/domain", "2.4", "0.0", "4.8"),
               ("visibility", "0.0", "0.0", "0.0"), ("ask_tool", "0.0", "0.0", "0.0"), ("interaction", "0.0", "0.0", "0.0"),
               ("tau structured-natural/task", "0.0", "0.0", "0.0")],
    "flashlite": [("structured-natural/family", "0.9", "-1.7", "3.8"), ("structured-natural/domain", "1.2", "-1.9", "4.5"),
                  ("visibility", "0.7", "-0.7", "2.1"), ("ask_tool", "0.0", "-1.4", "1.4"), ("interaction", "-2.8", "-6.9", "0.7"),
                  ("tau structured-natural/task", "0.0", "0.0", "0.0")],
}
# model -> arm -> (N, valid, balanced accuracy, completion)
PARAPHRASE = {
    "luna": {"natural": (192, 192, "99.4", "98.8"), "paraphrased": (192, 192, "98.8", "97.6")},
    "sonnet": {"natural": (192, 192, "97.0", "94.0"), "paraphrased": (192, 192, "97.0", "94.0")},
    "flashlite": {"natural": (192, 191, "98.9", "98.8"), "paraphrased": (192, 192, "98.8", "97.6")},
}
PARAPHRASE_CONTRASTS = {
    "luna": {"family_id": ("-0.3", "-1.0", "0.0"), "domain": ("-0.6", "-1.8", "0.0")},
    "sonnet": {"family_id": ("0.0", "-1.6", "1.6"), "domain": ("0.0", "-1.8", "1.8")},
    "flashlite": {"family_id": ("-0.2", "-1.6", "1.0"), "domain": ("-0.1", "-1.8", "1.4")},
}


def pct(x: float | None) -> str | None:
    if x is None:
        return None
    return f"{round(x * 100, 1) + 0.0:.1f}"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_outcomes(name: str) -> list[dict]:
    rows = []
    with (BASE / "outcomes" / name).open(newline="", encoding="utf-8") as handle:
        for r in csv.DictReader(handle):
            r["allowed"] = r["allowed"] == "1"
            r["trial"] = int(r["trial"])
            r["score"] = {k: r[k] == "1" for k in SCORE_FIELDS}
            rows.append(r)
    return rows


def check_vendor() -> int:
    vendor = BASE / "third_party/tau_bench"
    manifest = json.loads((vendor / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    for rel, expected in manifest["files"].items():
        if hashlib.sha256((vendor / rel).read_bytes()).hexdigest() != expected:
            fail(f"vendored tau-bench file differs from upstream: {rel}")
    if manifest["commit"] != "59a200c6d575d595120f1cb70fea53cef0632f6b":
        fail("unexpected tau-bench revision")
    return len(manifest["files"])


def check_cases() -> None:
    test, dev = er.make_cases(), er.make_cases(True)
    ext, counts = er.external_cases()
    expected = {
        "synthetic_test_cases.json": test,
        "development_cases.json": dev,
        "interface_study_case_ids.json": [c["case_id"] for c in er.factorial_cases(test)],
        "tau_bench_decision_points.json": ext,
        "paraphrase_cases.json": [er.paraphrase_case(c) for c in test],
    }
    for name, value in expected.items():
        released = json.loads((BASE / "cases" / name).read_text(encoding="utf-8"))
        if released != json.loads(json.dumps(value)):
            fail(f"released case file does not match the generator: {name}")
    if (len(test), len(dev), len(ext), len({c["family_id"] for c in ext})) != (96, 32, 34, 13):
        fail("unexpected case counts")
    if counts != {"cancel_pending_order": 8, "modify_pending_order_address": 8, "modify_pending_order_payment": 1}:
        fail(f"unexpected tau-bench operation counts: {counts}")


def check_prompts_and_scores(rows: list[dict], manifest: list[dict], label: str) -> None:
    lookup = {(m["study"], m["case"]["case_id"], m["arm"], m["trial"]): m for m in manifest}
    keys = Counter((r["model_key"], r["study"], r["case_id"], r["arm"], r["trial"]) for r in rows)
    if any(v != 1 for v in keys.values()):
        fail(f"{label}: duplicate outcome rows")
    expected = {(m, *k) for m in MODELS for k in lookup}
    if set(keys) != expected:
        fail(f"{label}: outcome rows do not cover the schedule exactly")
    for r in rows:
        entry = lookup[(r["study"], r["case_id"], r["arm"], r["trial"])]
        if r["prompt_sha256"] != entry["prompt_sha256"] or er.sha(entry["prompt"]) != entry["prompt_sha256"]:
            fail(f"{label}: prompt hash mismatch for {r['model_key']} {r['case_id']} {r['arm']}")
        case = entry["case"]
        if r["allowed"] != case["allowed"]:
            fail(f"{label}: allowed flag differs from the case for {r['case_id']}")
        if r["outcome"] in ("question", "invalid"):
            recomputed = er.score(case, {"kind": r["outcome"]}, external=r["study"] == "transfer")
            if {k: recomputed[k] for k in SCORE_FIELDS} != r["score"]:
                fail(f"{label}: score does not follow from outcome for {r['case_id']}")
        elif r["outcome"] == "action":
            if r["score"]["decision_correct"] != r["allowed"] or not r["score"]["action_attempt"]:
                fail(f"{label}: inconsistent action score for {r['case_id']}")
        elif r["outcome"] == "classification":
            if r["study"] != "ordinary_control":
                fail(f"{label}: classification outside the ordinary-rule control")
        else:
            fail(f"{label}: unknown outcome {r['outcome']}")


def fmt_ci(effect: dict) -> tuple[str, str, str]:
    return pct(effect["estimate"]), pct(effect["ci95"][0]), pct(effect["ci95"][1])


def main() -> int:
    n_vendor = check_vendor()
    check_cases()
    main_manifest, _ = er.build_manifest()
    para_manifest = er.build_paraphrase_manifest()
    rows = load_outcomes("explicit_policy_outcomes.csv")
    para = load_outcomes("paraphrase_outcomes.csv")
    check_prompts_and_scores(rows, main_manifest, "explicit-policy")
    check_prompts_and_scores(para, para_manifest, "paraphrase")

    counts = Counter(r["study"] for r in rows)
    test_calls = len(rows) - counts["pilot"]
    if (counts["pilot"], test_calls, len(para)) != (288, 4440, 1152):
        fail(f"unexpected call counts: {counts}")
    if (counts["generalization"], counts["ordinary_control"], counts["factorial"], counts["transfer"]) != (1728, 576, 1728, 408):
        fail(f"unexpected per-study counts: {counts}")

    groups = defaultdict(list)
    for r in rows:
        groups[(r["model_key"], r["study"], r["arm"])].append(r)

    for (study, arm), expected in ARM_TABLES.items():
        for model, (n, valid, ba, unauth, comp) in expected.items():
            g = groups[(model, study, arm)]
            got = (len(g), sum(r["score"]["valid"] for r in g), pct(er.metric(g, "balanced_accuracy")))
            if study != "ordinary_control":
                got += (pct(er.metric(g, "unauthorized_attempt_gated")), pct(er.metric(g, "completion_allowed")))
            else:
                got += (None, None)
            if got != (n, valid, ba, unauth, comp):
                fail(f"{model} {study}/{arm}: got {got}, paper {(n, valid, ba, unauth, comp)}")

    for model, expected in MAIN_TABLE.items():
        got = tuple(pct(er.metric(groups[(model, s, a)], "balanced_accuracy")) for s, a in (
            ("generalization", "natural"), ("generalization", "structured"),
            ("generalization", "decision"), ("transfer", "natural")))
        if got != expected:
            fail(f"main table {model}: got {got}, paper {expected}")

    # Every unauthorized-attempt rate in every test arm is zero.
    if any(r["score"]["unauthorized_attempt"] for r in rows):
        fail("an unauthorized attempt appears in the released outcomes")

    # The natural-policy errors with valid output are all unnecessary questions
    # on permitted cases, in the files (legal hold) or messaging (review) domains.
    natural = [r for r in rows if r["study"] == "generalization" and r["arm"] == "natural"]
    valid_errors = [r for r in natural if r["score"]["valid"] and not r["score"]["decision_correct"]]
    invalid = [r for r in natural if not r["score"]["valid"]]
    if len(valid_errors) != 6 or not all(r["score"]["unnecessary_question"] for r in valid_errors):
        fail(f"expected six unnecessary-question errors, found {len(valid_errors)}")
    if {r["domain"] for r in valid_errors} - {"files", "messaging"}:
        fail("an unnecessary question falls outside the files and messaging domains")
    by_model = Counter(r["model_key"] for r in valid_errors)

    effects = {}
    for model in MODELS:
        g = [r for r in rows if r["model_key"] == model and r["study"] == "generalization"]
        f = [r for r in rows if r["model_key"] == model and r["study"] == "factorial"]
        t = [r for r in rows if r["model_key"] == model and r["study"] == "transfer"]
        arms = ("visible0_asktool0", "visible0_asktool1", "visible1_asktool0", "visible1_asktool1")
        effects[model] = [
            ("structured-natural/family", fmt_ci(er.clustered_effect(g, ("natural", "structured"), (-1, 1), "balanced_accuracy", "family_id"))),
            ("structured-natural/domain", fmt_ci(er.clustered_effect(g, ("natural", "structured"), (-1, 1), "balanced_accuracy", "domain"))),
            ("visibility", fmt_ci(er.clustered_effect(f, arms, (-.5, -.5, .5, .5), "question_rate"))),
            ("ask_tool", fmt_ci(er.clustered_effect(f, arms, (-.5, .5, -.5, .5), "question_rate"))),
            ("interaction", fmt_ci(er.clustered_effect(f, arms, (1, -1, -1, 1), "question_rate"))),
            ("tau structured-natural/task", fmt_ci(er.clustered_effect(t, ("natural", "structured"), (-1, 1), "balanced_accuracy"))),
        ]
        expected = [(label, (e, lo, hi)) for label, e, lo, hi in CONTRASTS[model]]
        if effects[model] != expected:
            fail(f"paired contrasts {model}: got {effects[model]}, paper {expected}")

    for model in MODELS:
        group = [r for r in para if r["model_key"] == model]
        for arm, (n, valid, ba, comp) in PARAPHRASE[model].items():
            part = [r for r in group if r["arm"] == arm]
            got = (len(part), sum(r["score"]["valid"] for r in part),
                   pct(er.metric(part, "balanced_accuracy")), pct(er.metric(part, "completion_allowed")))
            if got != (n, valid, ba, comp):
                fail(f"paraphrase {model}/{arm}: got {got}, paper {(n, valid, ba, comp)}")
        for cluster, expected in PARAPHRASE_CONTRASTS[model].items():
            got = fmt_ci(er.clustered_effect(group, ("natural", "paraphrased"), (-1, 1), "balanced_accuracy", cluster))
            if got != expected:
                fail(f"paraphrase contrast {model}/{cluster}: got {got}, paper {expected}")

    print(f"VERIFIED: {n_vendor} vendored tau-bench files match upstream revision 59a200c")
    print("VERIFIED: case files rebuilt from delegationcheck/explicit_rules.py (96 test, 32 development, 48 interface, 34 tau-bench, 96 paraphrase)")
    print(f"VERIFIED: prompt hashes for all {len(rows)} explicit-policy and {len(para)} paraphrase outcomes")
    print("VERIFIED: explicit-rule balanced accuracy (natural / structured / decision given / tau-bench)")
    for model in MODELS:
        print(f"  {model:9s} " + " / ".join(MAIN_TABLE[model]))
    print("VERIFIED: policy-format, ordinary-rule, interface, tau-bench, and pilot tables; no unauthorized attempts")
    print(f"VERIFIED: six natural-policy errors are unnecessary questions ({dict(sorted(by_model.items()))}); {len(invalid)} invalid outputs counted separately")
    print("VERIFIED: paired contrasts with 20,000-draw cluster-bootstrap intervals")
    print("VERIFIED: paraphrase comparison (balanced accuracy 97.0-98.8 paraphrased) and its contrasts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
