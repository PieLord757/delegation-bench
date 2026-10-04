# Categorical model outputs

These files let you audit the reported results without the model-written text.

- `decision_by_scenario_trial.csv`: the 7,800 main-study decisions (156
  scenarios, ten models, five trials). Columns: scenario ID, model, trial,
  four-way decision, and an invalid-output flag.
- `tool_loop_trial_classification.csv`: 1,435 Tool-Loop episodes on the 29
  measurable scenarios (ten models, five trials). One GPT-OSS-20B cell and 14
  Qwen cells failed for technical reasons and are left out rather than filled
  in. Each episode is classified as calling the proposed tool with matching
  arguments, calling it with different arguments, calling a different tool, or
  not calling a tool (with the reason).
- `tool_loop_sanitized_tool_calls.csv`: proposed and emitted tool names and
  arguments for the seven OpenAI-, Anthropic-, and Google-hosted models.
  Arguments from Groq-hosted models are not included.
- `DERIVED_RELEASE_MANIFEST.json` and `ALL_TEN_TOOL_LOOP_RELEASE_MANIFEST.json`:
  hashes of the private source files and of the released files.

No row contains model-written prose, hidden reasoning, prompts, timestamps,
token counts, request IDs, credentials, or annotator-linked data. The
classifications describe what a model did; a Tool-Loop call that differs from
the proposed action is not automatically an error.

`python scripts/verify_derived_release.py` checks hashes, dimensions, label
values, and trial completeness, and rebuilds each model's agreement with the
annotators and the Tool-Loop mismatch totals.
