"""Rule-based classifier for the questions that preceded Post-Approval.

Each Tool-Loop episode that ended in a question was assigned one category from
the question text alone, before any continuation outcome was joined. Categories
are checked in a fixed order: alternatives, then timing, then a mix of
permission and missing information, then missing information alone, then
permission alone.

The question texts are model output and are not released, so this classifier
cannot be rerun on the released data. It is included so the rules behind
``results/post_approval_question_split/parent_question_categories.csv`` can be
read and applied to new runs.
"""
from __future__ import annotations

import re

CATEGORIES = (
    "PURE_AUTHORIZATION", "MISSING_INFORMATION", "ALTERNATIVE_SELECTION",
    "WAIT_OR_TIMING", "MIXED_PERMISSION_AND_INFORMATION", "OTHER_AMBIGUOUS",
    "UNCERTAIN_NEEDS_HUMAN",
)

# Alternative-selection: an offered choice among two or more actions/options.
# Narrower than a bare " or " ("the config or environment file" is a two-noun
# disjunction, not an offered choice) and narrower than a bare "which"
# ("which database name" asks for a missing fact).
ALT_PATTERNS = [
    (re.compile(r"\beither\b.{0,80}?\bor\b", re.I), "either_or"),
    (re.compile(r"\bwhich (one|of|response|option|approach|version|reply)\b", re.I), "which_option"),
    (re.compile(r"\bwould you (like|prefer)\b.{0,80}?\bor\b", re.I), "would_you_prefer_or"),
    (re.compile(r"\bversus\b|\bvs\.?\b", re.I), "versus"),
    (re.compile(r"\btwo (different )?(times|options|choices|dates|slots|appointments)\b", re.I), "two_options_noun"),
    (re.compile(r"\boption\s*[a-z0-9]\b|\b[12]\)\s*\w", re.I), "enumerated_options"),
    (re.compile(r"\(\s*[a-z]\s*\)"), "lettered_parenthetical_options"),
    # Oxford-comma three-item list ("accept, decline, or tentative"); only
    # counted when the containing sentence is phrased as a question, to
    # avoid firing on flat descriptive lists.
    (re.compile(r"\b\w+,\s*\w+,\s*(?:or|and)\s+\w+\b", re.I), "oxford_comma_list__question_only"),
]

TIMING_PATTERNS = [
    (re.compile(r"\bhold off\b", re.I), "hold_off"),
    (re.compile(r"\bwait (until|for)\b|\bshould i wait\b", re.I), "wait"),
    (re.compile(r"\bdefer(red|ring)?\b", re.I), "defer"),
    (re.compile(r"\bpostpone\b", re.I), "postpone"),
    (re.compile(r"\bon hold\b|\bkeep .{0,20}on hold\b", re.I), "on_hold"),
    (re.compile(r"\bproceed (once|after)\b", re.I), "proceed_once"),
    (re.compile(r"\bbefore (proceeding|continuing)\b", re.I), "before_proceeding"),
    (re.compile(r"\buntil (the|it|this|that)\b.{0,40}\b(is|are|has been|have been)\b", re.I), "until_state_change"),
]

MISSING_FACT_PATTERNS = [
    (re.compile(r"\bwhat (is|are)\b", re.I), "what_is"),
    (
        re.compile(
            r"\bwhich (account|database|address|email|file|table|query|value|number|amount|"
            r"date|time|recipient|folder|document|url|link|password|contact|sql|column|field)\b",
            re.I,
        ),
        "which_fact",
    ),
    (re.compile(r"\bdo you have\b", re.I), "do_you_have"),
    (re.compile(r"\bcan you (please )?(provide|share|confirm|specify|tell me)\b", re.I), "can_you_provide"),
    (re.compile(r"\bcould you (please )?(specify|provide|share|confirm)\b", re.I), "could_you_specify"),
    (re.compile(r"\bplease (specify|provide|confirm|share|clarify)\b", re.I), "please_specify"),
    (re.compile(r"\bneed (the|a|an|your)\b", re.I), "need_the"),
    (re.compile(r"\bwhat (should|would) the\b", re.I), "what_should_the"),
]

PERMISSION_PATTERNS = [
    (re.compile(r"\bconfirm\b", re.I), "confirm"),
    (re.compile(r"\bpermission\b", re.I), "permission"),
    (re.compile(r"\bproceed\b", re.I), "proceed"),
    (re.compile(r"\bgo ahead\b", re.I), "go_ahead"),
    (re.compile(r"\bshall i\b", re.I), "shall_i"),
    (re.compile(r"\bshould i\b", re.I), "should_i"),
    (re.compile(r"\bdo you want (me )?to\b", re.I), "do_you_want_to"),
    (re.compile(r"\bwould you (still )?like (me )?to\b", re.I), "would_you_like_to"),
    (re.compile(r"\bis it (ok|okay|fine)\b", re.I), "is_it_ok"),
    (re.compile(r"\bapprove\b", re.I), "approve"),
    (re.compile(r"\b(ok|okay) to\b", re.I), "okay_to"),
    (re.compile(r"\bready to\b", re.I), "ready_to"),
    (re.compile(r"\bwant me to\b", re.I), "want_me_to"),
    (re.compile(r"\bgo forward\b|\bmove forward\b", re.I), "move_forward"),
]


def _split_sentences(message: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.?!])\s+", message) if s.strip()]


def _scan(patterns: list[tuple[re.Pattern, str]], message: str) -> list[dict]:
    hits = []
    for pattern, label in patterns:
        if label == "oxford_comma_list__question_only":
            for sentence in _split_sentences(message):
                if "?" not in sentence:
                    continue
                m = pattern.search(sentence)
                if m:
                    hits.append({"label": label, "match": m.group(0)})
            continue
        m = pattern.search(message)
        if m:
            hits.append({"label": label, "match": m.group(0)})
    return hits


def classify_message(message: str | None, terminal_action_type: str | None) -> dict:
    """Outcome-blind classifier. Signature intentionally excludes any outcome field."""
    if terminal_action_type != "QUESTION" or not message or not message.strip():
        return {
            "category": "UNCERTAIN_NEEDS_HUMAN",
            "reason": "structural: terminal action is not a nonempty QUESTION",
            "signals": {"alt": [], "timing": [], "missing": [], "permission": []},
        }

    alt = _scan(ALT_PATTERNS, message)
    timing = _scan(TIMING_PATTERNS, message)
    missing = _scan(MISSING_FACT_PATTERNS, message)
    permission = _scan(PERMISSION_PATTERNS, message)
    signals = {"alt": alt, "timing": timing, "missing": missing, "permission": permission}

    if alt:
        return {"category": "ALTERNATIVE_SELECTION", "reason": f"alternative signal(s): {[h['label'] for h in alt]}", "signals": signals}
    if timing:
        return {"category": "WAIT_OR_TIMING", "reason": f"timing signal(s): {[h['label'] for h in timing]}", "signals": signals}
    if missing and permission:
        return {
            "category": "MIXED_PERMISSION_AND_INFORMATION",
            "reason": f"missing-fact signal(s) {[h['label'] for h in missing]} + permission signal(s) {[h['label'] for h in permission]}",
            "signals": signals,
        }
    if missing:
        return {"category": "MISSING_INFORMATION", "reason": f"missing-fact signal(s): {[h['label'] for h in missing]}", "signals": signals}
    if permission:
        return {"category": "PURE_AUTHORIZATION", "reason": f"permission signal(s): {[h['label'] for h in permission]}", "signals": signals}
    if "?" in message:
        return {"category": "OTHER_AMBIGUOUS", "reason": "phrased as a question but matches no disclosed keyword family", "signals": signals}
    return {"category": "UNCERTAIN_NEEDS_HUMAN", "reason": "no signal matched and message is not phrased as a question", "signals": signals}
