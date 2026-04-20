"""Unit tests for the shot fixture walker.

Covers every pinned branch of the walker's contract so regressions in the
comparator itself are caught before they mask regressions in the transformer.
"""

from tests.shot_fixture_walker import _MISSING, Mismatch, assert_equal, compare


def test_identical_nested_structures_yield_no_mismatches():
    expected = {
        "summary": {"avg_pressure_bar": 8.5, "duration_s": 27.3},
        "phases": [{"name": "bloom", "samples": [{"t": 0.1, "cp": 0.0}]}],
    }
    actual = {
        "summary": {"avg_pressure_bar": 8.5, "duration_s": 27.3},
        "phases": [{"name": "bloom", "samples": [{"t": 0.1, "cp": 0.0}]}],
    }
    assert compare(expected, actual) == []


def test_scalar_value_mismatch_at_nested_path_reports_path_and_kind():
    expected = {
        "phases": [
            {"samples": [{"weight_flow_g_s": 2.00}] * 13},
        ],
    }
    actual = {
        "phases": [
            {"samples": [{"weight_flow_g_s": 2.00}] * 13},
        ],
    }
    expected["phases"][0]["samples"][12] = {"weight_flow_g_s": 2.14}
    actual["phases"][0]["samples"][12] = {"weight_flow_g_s": 2.09}

    mismatches = compare(expected, actual)
    assert len(mismatches) == 1
    m = mismatches[0]
    assert m.kind == "value"
    assert m.path == "phases[0].samples[12].weight_flow_g_s"
    assert m.expected == 2.14
    assert m.actual == 2.09


def test_bool_vs_int_is_type_mismatch_not_silent_pass():
    assert compare(True, 1) == [Mismatch(path="", kind="type", expected=True, actual=1)]
    assert compare(False, 0) == [Mismatch(path="", kind="type", expected=False, actual=0)]


def test_extra_key_in_actual_reports_extra_key_mismatch():
    expected = {"a": 1}
    actual = {"a": 1, "debug_flag": True}
    mismatches = compare(expected, actual)
    assert len(mismatches) == 1
    m = mismatches[0]
    assert m.kind == "extra_key"
    assert m.path == "debug_flag"
    assert m.expected is _MISSING
    assert m.actual is True


def test_missing_key_in_actual_reports_missing_key_mismatch():
    expected = {"a": 1, "rmse_bar": 0.12}
    actual = {"a": 1}
    mismatches = compare(expected, actual)
    assert len(mismatches) == 1
    m = mismatches[0]
    assert m.kind == "missing_key"
    assert m.path == "rmse_bar"
    assert m.expected == 0.12
    assert m.actual is _MISSING


def test_list_length_mismatch_short_circuits_without_per_element_walk():
    expected = [1, 2, 3]
    actual = [1, 2, 3, 4]
    mismatches = compare(expected, actual)
    assert len(mismatches) == 1
    m = mismatches[0]
    assert m.kind == "length"
    assert m.path == ""
    assert m.expected == 3
    assert m.actual == 4


def test_none_and_none_equal_none_vs_zero_is_type():
    assert compare(None, None) == []

    mismatches = compare(None, 0)
    assert len(mismatches) == 1
    assert mismatches[0].kind == "type"

    extra_missing = compare({"a": 1}, {})
    assert len(extra_missing) == 1
    assert extra_missing[0].kind == "missing_key"
    assert extra_missing[0].path == "a"


def test_deeply_nested_mismatch_path_formatting():
    expected = {"phases": [{}, {"samples": [{}] * 13}]}
    actual = {"phases": [{}, {"samples": [{}] * 13}]}
    expected["phases"][1]["samples"][12] = {"weight_flow_g_s": 2.14}
    actual["phases"][1]["samples"][12] = {"weight_flow_g_s": 2.09}

    mismatches = compare(expected, actual)
    assert len(mismatches) == 1
    assert mismatches[0].path == "phases[1].samples[12].weight_flow_g_s"


def test_collect_through_cap_with_mid_recursion_cutoff():
    expected = {"root": {f"k{i:02d}": i for i in range(15)}}
    actual = {"root": {f"k{i:02d}": i + 1 for i in range(15)}}

    mismatches = compare(expected, actual, max_mismatches=10)
    assert len(mismatches) == 10
    paths = [m.path for m in mismatches]
    assert paths == [f"root.k{i:02d}" for i in range(10)]
    for i, m in enumerate(mismatches):
        assert m.kind == "value"
        assert m.expected == i
        assert m.actual == i + 1


def test_container_category_mismatch_does_not_recurse():
    expected = {"a": 1}
    actual = [1]
    mismatches = compare(expected, actual)
    assert len(mismatches) == 1
    assert mismatches[0].kind == "type"
    assert mismatches[0].path == ""


def test_assert_equal_raises_on_mismatch():
    try:
        assert_equal({"a": 1}, {"a": 2})
    except AssertionError as exc:
        assert "a:" in str(exc)
    else:
        raise AssertionError("expected AssertionError")


def test_assert_equal_silent_on_match():
    assert_equal({"a": 1}, {"a": 1})
