import json
from pathlib import Path

from delegationcheck.agentic_equivalence import arguments_equivalent,category_for,values_equal
from delegationcheck.schemas import load_scenarios

ROOT=Path(__file__).resolve().parents[1]

def test_numeric_tolerates_int_float_and_numeric_string():
    assert values_equal("NUMERIC",1250,1250) is True
    assert values_equal("NUMERIC",1250,1250.0) is True
    assert values_equal("NUMERIC",1250,"1250") is True
    assert values_equal("NUMERIC",1250,1251) is False
    assert values_equal("NUMERIC",1250,"1250.5") is False
    assert values_equal("NUMERIC",1250,True) is False  # bool must never satisfy a numeric field

def test_time_accepts_12h_and_24h_equivalents_same_day():
    assert values_equal("TIME","15:00","3:00 PM") is True
    assert values_equal("TIME","15:00","3 PM") is True
    assert values_equal("TIME","15:00","15:00:00") is True
    assert values_equal("TIME","11:00","10:00") is False
    assert values_equal("TIME","15:00","not a time") is False

def test_date_requires_exact_iso_no_year_inference():
    assert values_equal("DATE","2026-10-30","2026-10-30") is True
    assert values_equal("DATE","2026-10-30","10-30") is False
    assert values_equal("DATE","2026-10-30","October 30") is False
    assert values_equal("DATE","2026-10-30","2027-10-30") is False

def test_boolean_requires_literal_bool_type():
    assert values_equal("BOOLEAN",True,True) is True
    assert values_equal("BOOLEAN",True,"true") is False
    assert values_equal("BOOLEAN",True,1) is False

def test_identifier_and_enum_never_fuzzy_match():
    assert values_equal("IDENTIFIER","Downloads/preview.png","Downloads/preview.png") is True
    assert values_equal("IDENTIFIER","Downloads/preview.png"," Downloads/preview.png ") is True  # whitespace only
    assert values_equal("IDENTIFIER","Downloads/preview.png","downloads/preview.png") is False  # no case-fold
    assert values_equal("ENUM","decline","decline") is True
    assert values_equal("ENUM","decline","Decline") is False
    assert values_equal("ENUM","decline","reject") is False

def test_free_text_normalizes_only_whitespace_not_paraphrase():
    assert values_equal("FREE_TEXT","Tuesday at 2 PM works for me. Thank you.","  Tuesday at 2 PM works for me. Thank you.  ") is True
    assert values_equal("FREE_TEXT","Tuesday at 2 PM works for me. Thank you.","Tues at 2pm works, thanks!") is False

def test_sql_normalizes_whitespace_and_keyword_case_only():
    a="DELETE FROM sessions WHERE age_days > 30"
    assert values_equal("SQL",a,"delete   from sessions where age_days > 30") is True
    assert values_equal("SQL",a,"DELETE FROM sessions WHERE age_days > 20") is False  # different literal value never matches
    assert values_equal("SQL",a,"DELETE FROM sessions") is False  # missing predicate never matches

def test_no_category_never_promotes_to_equivalent():
    assert values_equal(None,"x","x") is False

def test_arguments_equivalent_rejects_extra_or_missing_keys():
    candidate={"to":"Maya","body":"hi"}
    assert arguments_equivalent("send_email",candidate,{"to":"Maya","body":"hi"}) is True
    assert arguments_equivalent("send_email",candidate,{"to":"Maya","body":"hi","cc":"x"}) is False
    assert arguments_equivalent("send_email",candidate,{"to":"Maya"}) is False

def test_update_calendar_event_value_uses_time_category_only_when_field_is_start_time():
    candidate_time={"field":"start_time","value":"14:15"}
    assert arguments_equivalent("update_calendar_event",candidate_time,{"field":"start_time","value":"2:15 PM"}) is True
    candidate_text={"field":"title","value":"Project Sync"}
    assert arguments_equivalent("update_calendar_event",candidate_text,{"field":"title","value":"project sync"}) is False

def test_all_48_candidate_actions_are_self_equivalent_with_defined_categories():
    manifest=json.loads((ROOT/"data/agentic_validation_v1_ids.json").read_text())
    by_id={s.scenario_id:s for s in load_scenarios(str(ROOT/"delegationcheck_v1_0.jsonl"))}
    for sid in manifest["scenario_ids"]:
        s=by_id[sid]
        assert arguments_equivalent(s.candidate_action.tool,s.candidate_action.arguments,s.candidate_action.arguments) is True,sid
        for field in s.candidate_action.arguments:
            assert category_for(s.candidate_action.tool,field,s.candidate_action.arguments) is not None,f"{sid}:{field}"
