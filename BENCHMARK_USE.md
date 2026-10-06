# Using DiscretionBench

## Evaluating a new model

1. Before running anything, write down the model identifier, provider
   settings, prompt version, scenario order, number of trials, how invalid
   outputs are handled, and the analysis you will report.
2. Show the model only `user_instruction`, `context`, and `candidate_action`
   (see `DATASET_CARD.md`). For results comparable to the paper, use the prompt
   in `discretionbench/prompts_main.py` and five trials per scenario.
3. Keep every attempt, including technical failures. Do not rerun a call
   because of what it answered. An unparseable answer counts as invalid.
4. Parse answers into the four labels with `discretionbench/parser.py` and keep
   invalid outputs as their own category.
5. When bootstrapping, resample scenarios or pairs and keep all trials of a
   scenario together.
6. Report agreement with the annotators next to pair responsiveness, under-
   and over-intervention, and stability across trials. Do not reduce these to
   one score.

## Tool-Loop and Post-Approval

`discretionbench/study_prompts.py` renders the Tool-Loop prompt, the response
envelope schema, and the Post-Approval continuation. `tool_loop/environment.py`
provides the sandbox: each call is validated against `tool_loop/tool_schemas.json`
and recorded, and nothing outside the sandbox changes. An episode ends at the
first tool call, question, or refusal, or after three turns. Score calls to the
proposed tool with `discretionbench/agentic_equivalence.py` (strict) and
`discretionbench/candidate_correspondence_normalized_v2.py` (lenient). Strict
matching mostly rejects formatting differences, so report both, and treat a
mismatch as a difference from the proposed action, not automatically as an
error.

Use the 29 scenarios marked `structurally_measurable` in
`data/agentic_validation_v1_measurability.json` for argument-level results;
on the others the correct arguments cannot be inferred from the text.

## Adding an elicitation format

Treat a new prompt as a new measurement condition, not a replacement for the
main prompt. Report every format you ran and compare them on the same
scenarios. Do not pick the format after looking at agreement with the
annotators.

## Extending the benchmark

Do not edit `discretionbench_v1_0.jsonl`. Put new scenarios in a separately
versioned file, say whether they have human labels, and do not describe
authoring expectations as ground truth.
