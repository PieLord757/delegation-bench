# Results

These tables were computed from the recorded model outputs and the annotators'
labels. They contain categorical outcomes, rates, and summary statistics only,
with no model-written text. Directory names follow the order in which the
analyses were run, so the table below maps them to the paper.

| Path | Contents |
|---|---|
| `policy_consistency_lexical_audit/` | Keyword rule versus models, matched-pair responses, paraphrase consistency, and risky-wording versus risky-consequence families |
| `next_existing_data_analyses/` | Calibration against annotator vote shares, constant and simple baselines, intervention cost tradeoffs, and their figures |
| `panel_leave_one_out/` | Leave-one-annotator-out agreement and model rankings by annotator |
| `final_reviewer_first/` | Domain breakdowns, stability associations, and score spread across annotators |
| `reviewer_extraction/` | Constant baselines, agreement between models, leave-one-model-out and leave-one-family-out checks, and judging versus acting ask rates |
| `story_first/` | Source tables for the judging versus acting figure and the cross-stage rank comparisons |
| `pre_experiment_decision/` | How asking was offered in Tool-Loop, discrimination versus threshold, sensitivity to the coding model's family, and Post-Approval counts |
| `action_stage_audit/` | Reconciliation of strict-rule rejections, narrower or safer Tool-Loop calls, and Post-Approval count checks |
| `downstream_v1/tool_loop/` | Tool-Loop results for all ten models |
| `downstream_v1/post_approval*/` | Post-Approval outcomes for the eight models with complete Tool-Loop runs, plus a separate sensitivity set for the two partial runs |
| `downstream_v1/measurement_robustness/` | Elicitation-format results for all ten models |
| `downstream_v1/measurement_open_codes/` | Categorical codes for the open-ended format |
| `downstream_v1/normalized_matcher_v2/` | The lenient argument matcher and its validation against the reviewers |
| `downstream_v1/human_equivalence_audit/` | The two reviewers' labels, sampling weights, agreement, and weighted estimates |
| `downstream_v1/authorization_profile/` | Per-model profile across the reported measures |
| `tool_loop_three_stage/` | Four-model Tool-Loop decomposition and its per-trial view |
| `AGENTIC_VALIDATION_V1_*.csv` | The first four-model Tool-Loop run |
| `GEMINI_AGENTIC_TRANSPORT_REPLICATION_V1_*.csv` | The Gemini 3.6 Flash rerun with strict argument schemas, which replaces the first Gemini run in the ten-model results |
| `MEASUREMENT_ROBUSTNESS_*.csv` | The first four-model elicitation-format run |
| `posthoc_tool_loop_mismatch_*.csv` | Scenario-level correlations between judged act rate and Tool-Loop behavior |

Some JSON files record hashes and file names of private inputs. Those entries
document where a table came from; the files they name are not part of this
repository.

In the elicitation tables the original menu format is labeled
`frozen_original`, and other column names may use `expert` for the
annotators. These labels are kept as they were computed.
