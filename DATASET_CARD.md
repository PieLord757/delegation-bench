# DelegationBench v1.0 dataset card

## What it measures

DelegationBench evaluates one decision: given a natural-language user
instruction, relevant context, and a specific candidate action, should an agent
act now, ask permission, request a missing fact, or refuse for an independent
reason?

The benchmark is designed for policy characterization, not for certifying that
a model is safe or authorized in deployment. Its authoring directions and
metadata are design diagnostics, not normative ground truth.

## Composition

- 156 English-language scenarios.
- Six domains: files, calendars, code/system, communication,
  publishing/social, and purchasing.
- 96 core-factor scenarios arranged as 48 low/high matched pairs: 12 pairs
  each for scope, stakes, reversibility, and external visibility.
- 24 scenarios that cross risky-sounding wording with risky consequences, in
  six 2-by-2 families.
- 12 missing-fact cases, where the expected response is REQUEST_INFORMATION.
- 16 paraphrases linked to parent scenarios.
- 8 boundary cases.

Run `python scripts/summarize_dataset.py` for counts reconstructed directly
from the JSONL.

## Model-facing fields

The primary model prompt uses only:

- `user_instruction`;
- `context`;
- `candidate_action.tool`;
- `candidate_action.arguments`;
- `candidate_action.description`.

All factor labels, authoring expectations, notes, split identifiers, and human
reference fields are hidden from evaluated models.

## Labels

- `ACT`: execute the candidate action now.
- `ASK_AUTHORIZATION`: the action is known, but permission is missing.
- `REQUEST_INFORMATION`: a required factual or task input is missing.
- `REFUSE`: an independent harmful, prohibited, or fundamentally inappropriate
  reason remains even if permission and information were supplied.

The annotators' majority labels are in
`data/reference/expert_majority_reference.csv` (the file name predates the
paper).
It resolves 149 scenarios by a 2-of-3 or 3-of-3 vote from three
computer-science students with AI experience who labeled independently and
were not involved in building the benchmark. Seven scenarios have no majority.
The labels are an informed reference point, not a representative user
distribution or ground truth.

## Recommended reporting

Do not report one aggregate number alone. At minimum report:

1. four-way and binary ACT/NON_ACT reference agreement;
2. the convention used for invalid outputs;
3. under- and over-intervention separately;
4. pair responsiveness: the share of the 48 matched pairs in which the act
   rate moves in the designed direction;
5. repeated-generation settings and stability if sampling is used.

Treat REQUEST and REFUSE category-specific estimates cautiously because they
are sparse in the majority labels (8 REQUEST, 1 REFUSE).

## Known limitations

- Scenarios are synthetic and candidate-action focused rather than complete
  interactive workflows.
- The benchmark is English-only and covers six task domains.
- Three technically informed student annotators are not representative of a user population.
- Pair responsiveness measures whether a model reacts to the changed feature,
  not whether its decision is correct.
- Public benchmark items may eventually be exposed to model training.

## Integrity

The dataset SHA-256 is
`3ecc96cb79946f46afc27161c59b7a0661a545be8f0b6e46cc289fba514ac405`.
`python scripts/verify_artifact.py` checks it along with every other file in
`SHA256SUMS`. The file is never edited in place; any correction or extension
will be released as a new, separately versioned file. Some authoring-era
status and label fields are kept so the file matches the evaluated version;
`SCHEMA.md` explains why they are not evaluation inputs.

## Contamination check

`CONTAMINATION_CANARY.md` contains a unique string identifying this release.
It is not inside any scenario.
