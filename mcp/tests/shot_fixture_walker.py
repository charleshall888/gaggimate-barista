"""Deep-equality walker for shot fixture regression tests.

Recursively compares two nested dict/list/scalar structures and returns a list
of field-path mismatches. Used by ``test_shot_regression.py`` to compare
transformer output against checked-in golden JSON.
"""

import math
from dataclasses import dataclass
from typing import Literal, Optional


_MISSING = object()

# Sentinel that, when used as a value in ``per_field_tol``, forces strict
# equality (``==``) for that field path even when ``float_tol > 0``. The
# sentinel is exposed as a module-level singleton so callers can write
# ``per_field_tol={"auto_delay.delay_ms": EXACT}``.
EXACT = object()


@dataclass
class Mismatch:
    path: str
    kind: Literal["value", "type", "length", "extra_key", "missing_key"]
    expected: object
    actual: object
    tolerance: Optional[float] = None


def _dict_child_path(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _resolve_tol(
    path: str,
    float_tol: float,
    per_field_tol: Optional[dict[str, float]],
) -> float:
    """Return the effective absolute tolerance for the given field path.

    Returns 0.0 to mean "strict equality required". Per-field overrides
    (including the ``EXACT`` sentinel and explicit ``None``) win over the
    global ``float_tol``.
    """
    if per_field_tol is not None and path in per_field_tol:
        override = per_field_tol[path]
        if override is None or override is EXACT:
            return 0.0
        return float(override)
    return float_tol


def _floats_equal(expected: float, actual: float, tol: float) -> bool:
    """Compare two floats with NaN-aware semantics.

    Both NaN -> equal. Exactly one NaN -> not equal. Otherwise: strict ``==``
    when ``tol == 0.0``, ``math.isclose(abs_tol=tol, rel_tol=0.0)`` when
    ``tol > 0``.
    """
    exp_nan = math.isnan(expected)
    act_nan = math.isnan(actual)
    if exp_nan or act_nan:
        return exp_nan and act_nan
    if tol > 0.0:
        return math.isclose(expected, actual, abs_tol=tol, rel_tol=0.0)
    return expected == actual


def _walk(
    expected: object,
    actual: object,
    path: str,
    out: list[Mismatch],
    cap: int,
    float_tol: float,
    per_field_tol: Optional[dict[str, float]],
) -> None:
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
            _walk(expected[key], actual[key], child_path, out, cap, float_tol, per_field_tol)
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
            _walk(expected[i], actual[i], f"{path}[{i}]", out, cap, float_tol, per_field_tol)
        return

    # Leaf scalar comparison. Floats get tolerance + NaN-aware treatment;
    # everything else (ints, strings, etc.) uses Python's strict ``==``.
    if isinstance(expected, float) and isinstance(actual, float):
        tol = _resolve_tol(path, float_tol, per_field_tol)
        if not _floats_equal(expected, actual, tol):
            out.append(
                Mismatch(
                    path=path,
                    kind="value",
                    expected=expected,
                    actual=actual,
                    tolerance=tol if tol > 0.0 else None,
                )
            )
        return

    if expected != actual:
        out.append(Mismatch(path=path, kind="value", expected=expected, actual=actual))


def compare(
    expected: object,
    actual: object,
    max_mismatches: int = 10,
    float_tol: float = 0.0,
    per_field_tol: Optional[dict[str, float]] = None,
) -> list[Mismatch]:
    out: list[Mismatch] = []
    _walk(expected, actual, "", out, max_mismatches, float_tol, per_field_tol)
    return out


def _format_mismatch(m: Mismatch) -> str:
    path = m.path or "<root>"
    if m.kind == "value":
        base = f"{path}: expected {m.expected!r}, got {m.actual!r}"
        if m.tolerance is not None:
            base += f" (abs_tol={m.tolerance!r})"
        return base
    if m.kind == "type":
        return f"{path}: expected {type(m.expected).__name__}, got {type(m.actual).__name__}"
    if m.kind == "length":
        return f"{path}: expected length {m.expected}, got length {m.actual}"
    if m.kind == "extra_key":
        return f"extra key in actual: {path}"
    if m.kind == "missing_key":
        return f"missing key in actual: {path}"
    return f"{path}: unknown mismatch kind {m.kind!r}"


def assert_equal(
    expected: object,
    actual: object,
    max_mismatches: int = 10,
    float_tol: float = 0.0,
    per_field_tol: Optional[dict[str, float]] = None,
) -> None:
    mismatches = compare(
        expected,
        actual,
        max_mismatches=max_mismatches,
        float_tol=float_tol,
        per_field_tol=per_field_tol,
    )
    if not mismatches:
        return
    lines = [f"{len(mismatches)} mismatch(es) found:"]
    lines.extend("  " + _format_mismatch(m) for m in mismatches)
    raise AssertionError("\n".join(lines))
