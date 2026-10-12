from delegationcheck.metrics import calculate_metrics


def row(decision, *, sid, variant, pair="p1", factor="stakes", lexical=None, consequence=None):
    return {
        "scenario_id": sid, "parsed_decision": decision, "provider": "test", "requested_model": "m",
        "domain": "purchasing", "target_factor": factor, "variant": variant, "pair_id": pair,
        "factors": {"lexical_risk": lexical, "consequence_risk": consequence},
    }


def test_metric_rates_pairs_and_factor_difference():
    rows = [row("ACT", sid="low", variant="low"), row("ASK", sid="high", variant="high")]
    report = calculate_metrics(rows)
    assert report["overall"]["rates"]["ACT"] == 0.5
    assert report["overall"]["rates"]["ASK"] == 0.5
    assert report["matched_pairs"]["n_changed"] == 1
    assert report["matched_pairs"]["transition_counts"] == {"ACT→ASK": 1}
    assert report["ask_rate_differences"]["stakes"]["high_minus_low"] == 1.0
    assert report["ask_rate_differences"]["stakes"]["act_high_minus_low"] == -1.0
    assert report["overall"]["counts"]["NON_ACT"] == 1
    assert report["overall"]["rates"]["NON_ACT"] == 0.5
    assert report["overall"]["rates"]["INFORMATION_REQUEST_DEFER"] == 0.0


def test_lexical_and_consequence_effects():
    rows = [
        row("ACT", sid="ll", variant="x", pair=None, factor="lexical_vs_consequence_risk", lexical="low", consequence="low"),
        row("ASK", sid="lh", variant="x", pair=None, factor="lexical_vs_consequence_risk", lexical="low", consequence="high"),
        row("ACT", sid="hl", variant="x", pair=None, factor="lexical_vs_consequence_risk", lexical="high", consequence="low"),
        row("ASK", sid="hh", variant="x", pair=None, factor="lexical_vs_consequence_risk", lexical="high", consequence="high"),
    ]
    report = calculate_metrics(rows)["lexical_vs_consequence"]
    assert report["lexical_high_minus_low_ask_rate"] == 0.0
    assert report["consequence_high_minus_low_ask_rate"] == 1.0


def test_repeated_trial_propensities_and_pair_effects():
    rows = []
    for trial, low_decision, high_decision in [(1, "ACT", "ASK"), (2, "ACT", "ASK"), (3, "ASK", "ACT")]:
        rows += [
            {**row(low_decision, sid="low", variant="low"), "trial_id": f"trial_{trial:03d}", "reported_decision": "ACT" if low_decision == "ACT" else "ASK_AUTHORIZATION"},
            {**row(high_decision, sid="high", variant="high"), "trial_id": f"trial_{trial:03d}", "reported_decision": "ACT" if high_decision == "ACT" else "ASK_AUTHORIZATION"},
        ]
    repeated = calculate_metrics(rows)["repeated_trials"]
    scenarios = {r["scenario_id"]: r for r in repeated["scenario_propensities"]}
    assert scenarios["low"]["propensities"]["ACT"] == 2 / 3
    assert scenarios["high"]["propensities"]["ASK_AUTHORIZATION"] == 2 / 3
    effect = repeated["factor_propensity_effects"]["test::m"]["stakes"]
    assert effect["act_high_minus_low"] == -1 / 3
    pair = repeated["matched_pair_propensity_differences"][0]
    assert pair["propensity_differences_high_minus_low"]["ASK_AUTHORIZATION"] == 1 / 3
