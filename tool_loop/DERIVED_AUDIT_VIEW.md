# Four-model Tool-Loop per-trial view

`results/tool_loop_three_stage/three_stage_trial_paths.csv` has one row per
Tool-Loop trial for the first four-model run on the 29 measurable scenarios:
580 rows (29 scenarios, four models, five trials). It contains no model text,
prompts, tool arguments, or annotator information.

## Columns

- `condition`: model name;
- `scenario_id`, `trial_id`: scenario and trial identifiers;
- `offline_act`: whether the matching main-study trial chose ACT;
- `candidate_tool`: whether the Tool-Loop trial called the proposed tool;
- `candidate_equivalent`: whether it also passed the strict argument rule;
- `joint_a_t_e`: offline ACT, proposed tool called, and arguments matched;
- `same_tool_non_equivalent`: proposed tool called with non-matching arguments;
- `no_candidate_tool`: proposed tool not called.

The last two columns give the mismatch breakdown used in the paper. They
measure correspondence with the proposed action, not correctness.

`results/tool_loop_three_stage/manifest.json` records the hashes of the private
source files and of this view. `python scripts/reconstruct_tool_loop_summary.py`
rebuilds the summary table from it.
