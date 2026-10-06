# Reproducing the reported numbers

Every command below runs from the repository root, makes no model or network
calls, and needs only the packages in `requirements-tested.txt`.

```bash
python scripts/validate_dataset.py discretionbench_v1_0.jsonl
python scripts/summarize_dataset.py
python scripts/verify_artifact.py
python scripts/verify_derived_release.py
python scripts/verify_story_first_headlines.py
python scripts/verify_human_equivalence_audit_release.py
python scripts/verify_normalized_matcher_v2_release.py
python scripts/reconstruct_tool_loop_summary.py
python scripts/make_agreement_coherence_figure.py
python scripts/make_ask_and_action_figure.py
python scripts/update_checksums.py --check
pytest -q
```

## What each command checks

| Command | What it checks |
|---|---|
| `validate_dataset.py` | Schema, pairing, and paraphrase links for all 156 scenarios |
| `summarize_dataset.py` | Counts by split, domain, feature, and pair |
| `verify_artifact.py` | Every file against `SHA256SUMS`, the dataset hash, 156/149 reference counts, the keyword rule's 69.1% agreement and 9/48 pairs, the model agreement and Brier ranges, Krippendorff's alpha (.437 four-way, .543 binary), and the license inventory |
| `verify_derived_release.py` | Rebuilds each model's four-way agreement with the annotators from the 7,800 released decisions, and the Tool-Loop mismatch totals from the 1,435 released episodes |
| `verify_story_first_headlines.py` | Recomputes the three gaps from released tables: the keyword rule's 69.1% agreement and 9/48 pairs, the elicitation result (balanced option order lowers Brier for 10/10 models and is best for 9/10), leave-one-annotator-out agreement (73.8%–79.8%), the lower Tool-Loop ask rate for all ten models, the rank correlation of -.491 between judged act rate and proposed-tool calls, and the 227 Post-Approval continuations from eight models |
| `verify_human_equivalence_audit_release.py` | Reviewer agreement (97.0%) and each reviewer's weighted estimates (93.9% and 96.0% Tool-Loop correspondence) from the 200 audit labels and weights |
| `verify_normalized_matcher_v2_release.py` | The lenient matcher's 900 of 1,011 accepted Tool-Loop calls (89.0%) and its precision against both reviewers |
| `reconstruct_tool_loop_summary.py` | Rebuilds the four-model three-stage Tool-Loop summary from the per-trial view |
| `make_agreement_coherence_figure.py` | Redraws the agreement versus pair-responsiveness figure |
| `make_ask_and_action_figure.py` | Redraws the judging versus acting figure |
| `update_checksums.py --check` | Confirms `SHA256SUMS` lists every file with its current hash |

## Where the reported tables live

| Paper result | File |
|---|---|
| Keyword rule versus models | `results/policy_consistency_lexical_audit/policy_consistency_rule_model_comparison.csv` |
| Feature effects in matched pairs | `results/policy_consistency_lexical_audit/policy_consistency_core_pairs.csv` |
| Agreement with the annotators | `data/reference/final_model_vs_expert_reference.csv` |
| Annotator agreement and alpha | `data/reference/final_expert_agreement_summary.csv` |
| Leave-one-annotator-out | `results/panel_leave_one_out/leave_one_out_panel_agreement.csv` |
| Score spread by annotator | `results/final_reviewer_first/model_agreement_by_annotator_spread.csv` |
| Elicitation formats | `results/downstream_v1/measurement_robustness/condition_metrics.csv`, `panel_validity_metrics.csv`, `elicitation_envelope.csv` |
| Open-ended format coding | `results/downstream_v1/measurement_open_codes/open_ended_coding_consensus.csv` |
| Stability versus format shift | `results/final_reviewer_first/stability_associations.csv` |
| Asking when judging versus acting | `results/reviewer_extraction/same48_ask_by_endpoint.csv`, `results/story_first/offline_vs_tool_loop_ask.csv` |
| Judged act rate versus tool calls | `results/story_first/action_stage_profile.csv`, `results/posthoc_tool_loop_mismatch_scenario_correlations.csv` |
| Tool-Loop outcomes for all ten models | `results/downstream_v1/tool_loop/model_summary.csv`, `data/derived/tool_loop_trial_classification.csv` |
| Post-Approval | `results/downstream_v1/post_approval/stage_comparison.csv`, `results/downstream_v1/post_approval_primary/scenario_trial_outcomes.csv` |
| Strict versus lenient matching | `results/downstream_v1/normalized_matcher_v2/` |
| Human correspondence audit | `results/downstream_v1/human_equivalence_audit/` |
| Narrower or safer calls | `results/action_stage_audit/narrower_safer_by_endpoint.csv` |
| Domain breakdown | `results/final_reviewer_first/domain_summary.csv`, `factor_by_domain.csv` |

`results/README.md` describes each results directory.

## Limits

Model responses and individual annotator files are not released. The tables
under `results/` were computed from those private files and are shipped as
outputs. The verification scripts recompute the headline values from the
released categorical data and check them against those tables. They cannot
re-parse model text or recompute anything that needs a vote linked to a
specific annotator.

These paper results have no source table in this repository:

- the explicit-rule checks (policy cases and τ-bench decision points);
- the split of Post-Approval questions into simple permission, timing,
  alternative, and mixed questions;
- the stakes and reversibility re-analysis restricted to clean pairs.
