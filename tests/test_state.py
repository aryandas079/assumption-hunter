import copy
import json

import pytest
from conftest import INITIAL, SKILL, UPDATED
from jsonschema import Draft202012Validator, FormatChecker
from state import MAX_BYTES, StateError, compare_snapshots, load_snapshot, parse_snapshot, rank_assumptions


def test_samples_match_both_validators():
    schema = json.loads((SKILL / "assets" / "assumptions.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for example in (INITIAL, UPDATED):
        validator.validate(load_snapshot(example))


@pytest.mark.parametrize("value", [
    b"\xff", b"", "[", "[]", '{"a":1,"a":2}', '{"number":NaN}', '{"number":1e999}',
    "[" * 1200 + "]" * 1200,
])
def test_rejects_invalid_json(value):
    with pytest.raises(StateError):
        parse_snapshot(value)


def test_input_size_limit(initial, tmp_path):
    raw = json.dumps(initial).encode()
    bounded = raw.ljust(MAX_BYTES, b" ")
    assert parse_snapshot(bounded) == initial
    path = tmp_path / "large.json"
    path.write_bytes(bounded + b" ")
    with pytest.raises(StateError, match="exceeds"):
        load_snapshot(path)


@pytest.mark.parametrize("date", ["2026-02-30T12:00:00Z", "2026-11-23", "2026-11-23T06:00:00+05:30", None])
def test_utc_date_validation(initial, date):
    initial["audited_at"] = date
    with pytest.raises(StateError, match="audited_at"):
        parse_snapshot(json.dumps(initial))


@pytest.mark.parametrize(("field", "value"), [
    ("status", "guaranteed"), ("category", {}), ("id", "ASM-1"), ("impact", True),
    ("impact", -1), ("uncertainty", 6), ("test_cost", 2.0), ("mitigation", " "),
    ("falsification_test", None), ("source_locations", None), ("evidence", [{"kind": "support"}]),
])
def test_rejects_invalid_assumption_fields(initial, field, value):
    initial["assumptions"][0][field] = value
    with pytest.raises(StateError, match=field):
        parse_snapshot(json.dumps(initial))


@pytest.mark.parametrize("path", [
    "../private", "docs/../../private", "/secret", "C:/secret", "C:secret",
    r"C:\secret", r"\\server\share", "docs//file", "docs/./file", "memo.md:stream", "memo\n.md",
])
def test_unsafe_source_path(initial, path):
    initial["assumptions"][0]["source_locations"][0]["path"] = path
    with pytest.raises(StateError, match="source_locations"):
        parse_snapshot(json.dumps(initial))


def test_line_range_and_duplicate_ids(initial):
    item = initial["assumptions"][0]
    item["source_locations"][0].update(line_start=2, line_end=1)
    with pytest.raises(StateError, match="line_start"):
        parse_snapshot(json.dumps(initial))
    item["source_locations"] = []
    initial["assumptions"].append(item)
    with pytest.raises(StateError, match="duplicate assumption ID"):
        parse_snapshot(json.dumps(initial))


def test_nullable_metadata_and_non_testable_preference(initial):
    item = initial["assumptions"][0]
    item.update(category="preference", status="not_testable", falsification_test=None, source_locations=[])
    item["evidence"] = [{
        "kind": "support", "source": None, "summary": "Project preference recorded.",
        "verified_by": None, "observed_at": None,
    }]
    assert parse_snapshot(json.dumps(initial)) == initial


def test_rank_override_and_exact_ties(initial):
    critical, routine = initial["assumptions"]
    critical.update(impact=5, uncertainty=1, test_cost=5)
    routine.update(impact=4, uncertainty=2, test_cost=2)
    other = dict(routine, id="ASM-003", impact=2, uncertainty=4)
    tied = dict(routine, id="ASM-004")
    initial["assumptions"] = [other, tied, routine, critical]
    ranked = rank_assumptions(initial)
    assert [row["id"] for row in ranked] == ["ASM-001", "ASM-002", "ASM-004", "ASM-003"]
    assert ranked[0]["critical_unresolved"] and ranked[0]["score"] == 1


def test_rank_empty(initial):
    initial["assumptions"] = []
    assert rank_assumptions(initial) == []


def test_comparison_tracks_changes_and_reports_no_raw_evidence(initial, updated):
    updated["assumptions"][0]["statement"] += " In the staging run."
    updated["assumptions"][1]["id"] = "ASM-003"
    diff = compare_snapshots(initial, updated)
    for key in ("statement_changed", "status_changed", "evidence_changed", "priority_changed"):
        assert diff[key] == ["ASM-001"]
    assert diff["added"] == ["ASM-003"]
    assert diff["retired"] == ["ASM-002"]
    change = diff["changes"][0]
    assert change["status"] == {"before": "untested", "after": "contradicted"}
    assert change["reason"] == updated["assumptions"][0]["last_changed_reason"]
    assert updated["assumptions"][0]["evidence"][0]["summary"] not in json.dumps(diff)


def test_compare_ignores_order_and_stale_reason(updated):
    row = updated["assumptions"][0]
    row["evidence"].append(dict(row["evidence"][0], kind="support"))
    new = copy.deepcopy(updated)
    new["assumptions"][0]["evidence"].reverse()
    new["assumptions"].reverse()
    assert not any(compare_snapshots(updated, new).values())
    new["assumptions"][1]["mitigation"] = "Use a unique constraint."
    diff = compare_snapshots(updated, new)
    assert diff["changes"] == [{"id": "ASM-001", "fields": ["mitigation"], "reason": None}]


def test_compare_rejects_other_projects(initial, updated):
    updated["project_id"] = "other"
    with pytest.raises(StateError, match="different projects"):
        compare_snapshots(initial, updated)
