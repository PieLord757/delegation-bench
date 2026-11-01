# Datasheet for DelegationCheck v1.0

This datasheet follows the questions in Gebru et al., "Datasheets for
Datasets" (Communications of the ACM, 2021). It covers
`delegationcheck_v1_0.jsonl`, the annotator labels in `data/reference/`, and
the categorical model results in `data/derived/`, `results/`, and
`explicit_rules/`. Items marked **[Author to complete]** need information that
is not recorded in the repository.

## Motivation

**For what purpose was the dataset created?**
To test when an AI agent should check with the user before taking an action.
The benchmark scores the decision to act, ask for permission, ask for a
missing fact, or decline, and whether that decision changes when one relevant
feature of the situation changes.

**Who created the dataset and on behalf of which entity?**
Shiva Pochampally wrote the scenarios and ran the evaluations.
**[Author to complete: affiliation.]**

**Who funded the creation of the dataset?**
**[Author to complete.]**

## Composition

**What do the instances represent?**
Each instance is a scenario: a user instruction, a short description of the
relevant state, and one proposed tool call (tool name, arguments, and a
plain-language description). The model being tested sees only these three
parts.

**How many instances are there?**
156 scenarios:

| Set (`split` field) | Scenarios |
|---|---:|
| Matched pairs that change scope, stakes, reversibility, or visibility to others (`core_factor`) | 96 (48 pairs, 12 per feature) |
| Risky wording crossed with risky consequences (`lexical_decorrelation`) | 24 |
| Missing-fact cases (`ambiguity_control`) | 12 |
| Paraphrases of other scenarios (`paraphrase_robustness`) | 16 |
| Boundary cases (`adversarial_disagreement`) | 8 |

The domains are files (35), calendar (29), communication (27), purchasing
(27), code and systems (24), and publishing and social media (14).

The release also contains:

- three annotators' vote counts and majority label for every scenario;
- 7,800 categorical decisions from ten models (156 scenarios, five trials);
- 1,435 categorical Tool-Loop outcomes, in which the model carries out the
  task with simulated tools, and 227 Post-Approval outcomes;
- 5,880 categorical outcomes from the explicit-rule studies, with their 96
  synthetic test cases, 32 development cases, and 34 decision points adapted
  from tau-bench.

**Is the dataset a sample from a larger set?**
No. The scenarios were written for this benchmark and the release contains
all of them. They do not sample any population of real agent tasks.

**What data does each instance consist of?**
Text fields and a small JSON object for the tool arguments. Other fields
record the pair, family, domain, target feature, variant, and authoring
notes. `SCHEMA.md` lists every field.

**Is there a label or target associated with each instance?**
The reference is the majority label of three annotators, available for 149
scenarios (69 `ACT`, 71 `ASK_AUTHORIZATION`, 8 `REQUEST_INFORMATION`, 1
`REFUSE`). Seven scenarios have no majority. The `authoring_expectation`
field records the direction intended when a scenario was written and is not a
label.

**Is any information missing from individual instances?**
The `human_reference` field inside the JSONL is an empty legacy container; the
labels are in `data/reference/` instead. Fourteen Qwen 3.6 27B Tool-Loop
cells and one GPT-OSS-20B cell failed for technical reasons and are absent
rather than filled in.

**Are relationships between instances made explicit?**
Yes. `pair_id` and `paired_with` link the two scenarios of a matched pair,
`parent_scenario_id` links a paraphrase to its source, and `family_id`
groups related scenarios.

**Are there recommended data splits?**
The whole set is a test set. There is no training split, and the scenarios
should not be used for training.

**Are there any errors, sources of noise, or redundancies?**
A pair-by-pair review (`results/pair_construct_audit/pair_audit_table.csv`)
found that 13 of the 24 stakes and reversibility pairs also change something
besides the target feature, such as whether the task can succeed. The 16
paraphrases repeat the content of their parents on purpose. Annotator
agreement is moderate (Krippendorff's alpha .437 four-way, .543 for acting
versus not acting).

**Is the dataset self-contained?**
Yes. The tau-bench files used by the explicit-rule studies are included in
`explicit_rules/third_party/tau_bench/` under their MIT License.

**Does the dataset contain data that might be considered confidential?**
No. The scenarios are synthetic.

**Does the dataset contain data that might be offensive, insulting, or
threatening?**
No. Some scenarios describe deleting files, spending money, or sending
messages, which is the point of the benchmark, but none contain abusive
content.

**Does the dataset identify any subpopulations, or individuals?**
No. Names in the scenarios are invented. The tau-bench user and order
records are synthetic data from that benchmark. Annotators are referred to
only as A, B, and C in aggregate tables, and no vote is linked to a person.

**Does the dataset contain sensitive data?**
No.

## Collection process

**How was the data associated with each instance acquired?**
The author wrote the scenarios. For each matched pair, the instruction and
the proposed action stay the same and one sentence of context changes. Model
decisions were collected by calling each model's API with the prompt in
`delegationcheck/prompts_main.py` and parsing the reply.

**What mechanisms or procedures were used to collect the data?**
Annotators labeled scenarios through a single interface with written
definitions of the four decisions. Models were called through their providers'
APIs; GPT-OSS-120B, GPT-OSS-20B, and Qwen 3.6 27B were served by Groq.
Tool-Loop episodes ran in the sandbox in `tool_loop/`, whose 15 tools record
calls without real side effects.

**If the dataset is a sample from a larger set, what was the sampling
strategy?**
Not applicable for the scenarios. For the human check of Tool-Loop argument
matching, 200 calls were sampled with weights recorded in
`results/downstream_v1/human_equivalence_audit/`.

**Who was involved in the data collection process and how were they
compensated?**
Three computer-science students with AI experience labeled the scenarios.
They were not involved in building the benchmark and were not paid. Two
members of the author's lab labeled the 200-call audit sample.
**[Author to complete: whether the annotators have any relationship to the
author or institution.]**

**Over what timeframe was the data collected?**
The explicit-rule studies were collected in September 2026.
**[Author to complete: the annotation period and the collection dates of the
main study, Tool-Loop, and Post-Approval runs.]**

**Were any ethical review processes conducted?**
**[Author to complete: institutional review or determination for the
annotation work.]**

**Did you collect the data from the individuals in question directly?**
The annotators supplied their labels directly. No other data about people
was collected.

**Were the individuals in question notified about the data collection, and
did they consent?**
**[Author to complete.]**

**Has an analysis of the potential impact of the dataset and its use on data
subjects been conducted?**
The only data subjects are the annotators. Their identities, notes, and
confidence ratings are withheld, and the released vote counts cannot be
linked to a person.

## Preprocessing, cleaning, and labeling

**Was any preprocessing, cleaning, or labeling of the data done?**
Model replies were parsed into `ACT`, `ASK_AUTHORIZATION`,
`REQUEST_INFORMATION`, `REFUSE`, or `INVALID` with
`delegationcheck/parser.py`. Unparseable replies were kept as `INVALID` and
never rerun. Tool-Loop calls were compared with the proposed action by a
strict rule (`delegationcheck/agentic_equivalence.py`) and a lenient matcher
(`delegationcheck/candidate_correspondence_normalized_v2.py`). Questions that
preceded Post-Approval continuations were sorted into question types by the
rules in `delegationcheck/post_approval_question_classifier.py`. The
annotators' reference label is the 2-of-3 or 3-of-3 majority, with no
adjudication.

**Was the raw data saved in addition to the processed data?**
Yes, privately. Model-written text and hidden reasoning are not released
because provider terms do not clearly allow redistribution. Raw annotator
workbooks are kept private to protect the annotators.

**Is the software used to preprocess or label the data available?**
Yes. The parser, both matchers, the question classifier, and the explicit-rule
scorer are in `delegationcheck/`.

## Uses

**Has the dataset been used for any tasks already?**
Yes, in the accompanying paper (arXiv 2610.05532), which evaluates ten models
from five families.

**Is there a repository that links to papers or systems that use the
dataset?**
The GitHub repository: <https://github.com/PieLord757/delegation-check>.

**What other tasks could the dataset be used for?**
Comparing elicitation formats, studying how judgments about an action relate
to what an agent does with tools, and testing methods that decide when an
agent should ask for confirmation.

**Is there anything about the composition of the dataset or the way it was
collected that might impact future uses?**
The scenarios are synthetic, in English, and limited to six domains, and
each centers on one proposed action. Three technically trained students are
not a representative user population, and their labels are a reference
point, not ground truth. `REQUEST_INFORMATION` and `REFUSE` are too rare in
the majority labels to rank models on. Each matched-pair feature is built
from three scenario families, so feature-level results describe these
situations rather than the feature in general.

**Are there tasks for which the dataset should not be used?**
It should not be used to certify that a model is safe to deploy or
authorized to act, and it should not be used to train models. A single
agreement score should not be reported on its own; `BENCHMARK_USE.md`
describes what to report.

## Distribution

**Will the dataset be distributed to third parties outside of the entity on
behalf of which the dataset was created?**
Yes. It is public on GitHub, and `hf_dataset/` contains a card and
instructions for publishing it on Hugging Face.

**How will the dataset be distributed?**
As files in the GitHub repository. `croissant.json` describes the main files
in Croissant 1.0 format. The paper is arXiv 2610.05532.

**When will the dataset be distributed?**
The first version was published on GitHub in October 2026.

**Will the dataset be distributed under a copyright or other intellectual
property license?**
The data and documentation are under CC BY 4.0 (`LICENSE-DATA.md`) and the
code under the MIT License (`LICENSE`). The tau-bench files remain under
tau-bench's MIT License, and the DejaVu font subset embedded in PDF figures
remains under its own license (`THIRD_PARTY_NOTICES/`). `LICENSE_INVENTORY.csv`
lists the license of every file.

**Have any third parties imposed IP-based or other restrictions on the data?**
No restrictions apply to the released files. Provider-generated text is
withheld because its redistribution terms are unclear.

**Do any export controls or other regulatory restrictions apply?**
None known.

## Maintenance

**Who will be supporting, hosting, and maintaining the dataset?**
The author, through the GitHub repository.

**How can the owner be contacted?**
Through GitHub issues on the repository.

**Is there an erratum?**
None so far. Corrections will be listed in the repository.

**Will the dataset be updated?**
`delegationcheck_v1_0.jsonl` is never edited in place. Corrections or new
scenarios will be released as separately versioned files, and
`SHA256SUMS` lets users confirm which version they have.

**Are there limits on the retention of data about individuals?**
Not applicable; no data about individuals is released.

**Will older versions continue to be supported?**
Yes. Version 1.0 stays available under its current file name and hash.

**If others want to extend or build on the dataset, is there a mechanism for
them to do so?**
Yes. Under CC BY 4.0 anyone can build on it. `BENCHMARK_USE.md` asks that new
scenarios go in a separately versioned file, state whether they have human
labels, and not present authoring expectations as ground truth.

**Contamination.** `CONTAMINATION_CANARY.md` holds a unique string for
detecting whether a model's training data included this release.
