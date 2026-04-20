"""Deep-equality walker for shot fixture regression tests.

Recursively compares two nested dict/list/scalar structures and returns a list
of field-path mismatches. Used by ``test_shot_regression.py`` to compare
transformer output against checked-in golden JSON.
"""

from dataclasses import dataclass
from typing import Literal


_MISSING = object()


@dataclass
class Mismatch:
    path: str
    kind: Literal["value", "type", "length", "extra_key", "missing_key"]
    expected: object
    actual: object


def _dict_child_path(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _walk(expected: object, actual: object, path: str, out: list[Mismatch], cap: int) -> None:
    if len(out) >= cap:
        return

    exp_is_bool = isinstance(expected, bool)
    act_is_bool = isinstance(actual, bool)
    if exp_is_bool or act_is_bool:
        if exp_is_bool and act_is_bool:
            if expected != actual:
                out.append(Mismatch(path=path, kind="value", expected=expected, actual=actual))
            return
        out.append(Mismatch(path=path, kind="type", expected=expected, actual=actual))
        return

    if expected is None or actual is None:
        if expected is None and actual is None:
            return
        out.append(Mismatch(path=path, kind="type", expected=expected, actual=actual))
        return

    exp_is_dict = isinstance(expected, dict)
    act_is_dict = isinstance(actual, dict)
    exp_is_list = isinstance(expected, list)
    act_is_list = isinstance(actual, list)

    if exp_is_dict != act_is_dict or exp_is_list != act_is_list:
        out.append(Mismatch(path=path, kind="type", expected=expected, actual=actual))
        return

    if exp_is_dict:
        for key in sorted(expected.keys()):
            if len(out) >= cap:
                return
            child_path = _dict_child_path(path, key)
            if key not in actual:
                out.append(Mismatch(path=child_path, kind="missing_key", expected=expected[key], actual=_MISSING))
                continue
            _walk(expected[key], actual[key], child_path, out, cap)
        for key in sorted(set(actual.keys()) - set(expected.keys())):
            if len(out) >= cap:
                return
            child_path = _dict_child_path(path, key)
            out.append(Mismatch(path=child_path, kind="extra_key", expected=_MISSING, actual=actual[key]))
        return

    if exp_is_list:
        if len(expected) != len(actual):
            out.append(Mismatch(path=path, kind="length", expected=len(expected), actual=len(actual)))
            return
        for i in range(len(expected)):
            if len(out) >= cap:
                return
            _walk(expected[i], actual[i], f"{path}[{i}]", out, cap)
        return

    if expected != actual:
        out.append(Mismatch(path=path, kind="value", expected=expected, actual=actual))


def compare(expected: object, actual: object, max_mismatches: int = 10) -> list[Mismatch]:
    out: list[Mismatch] = []
    _walk(expected, actual, "", out, max_mismatches)
    return out


def _format_mismatch(m: Mismatch) -> str:
    path = m.path or "<root>"
    if m.kind == "value":
        return f"{path}: expected {m.expected!r}, got {m.actual!r}"
    if m.kind == "type":
        return f"{path}: expected {type(m.expected).__name__}, got {type(m.actual).__name__}"
    if m.kind == "length":
        return f"{path}: expected length {m.expected}, got length {m.actual}"
    if m.kind == "extra_key":
        return f"extra key in actual: {path}"
    if m.kind == "missing_key":
        return f"missing key in actual: {path}"
    return f"{path}: unknown mismatch kind {m.kind!r}"


def assert_equal(expected: object, actual: object, max_mismatches: int = 10) -> None:
    mismatches = compare(expected, actual, max_mismatches=max_mismatches)
    if not mismatches:
        return
    lines = [f"{len(mismatches)} mismatch(es) found:"]
    lines.extend("  " + _format_mismatch(m) for m in mismatches)
    raise AssertionError("\n".join(lines))
