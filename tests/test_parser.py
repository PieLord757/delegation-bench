import pytest

from delegationcheck.parser import parse_response
from delegationcheck.schemas import Decision


@pytest.mark.parametrize("raw,decision,status", [
    ('{"decision":"ASK","reason":"Need approval."}', Decision.ASK, "json"),
    ('```json\n{"decision": "act", "reason": "Authorized."}\n```', Decision.ACT, "json"),
    ("Decision: DEFER\nMissing a recipient.", Decision.DEFER, "fallback_label"),
    ("REFUSE", Decision.REFUSE, "fallback_label"),
    ("I considered ACT and ASK but cannot decide.", Decision.INVALID, "unparseable"),
    ("", Decision.INVALID, "empty"),
])
def test_parse_response(raw, decision, status):
    parsed = parse_response(raw)
    assert parsed.decision == decision
    assert parsed.status == status
