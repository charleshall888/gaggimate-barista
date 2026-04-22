"""Parity gate for the DDSA Python port versus the JS reference.

Walks every shot fixture in ``mcp/tests/fixtures/shots/*.slog``, runs
``classify_phase_exits`` and ``estimate_auto_delay`` on the parsed
:class:`ShotData` plus its sibling ``<shot_id>.profile.json`` snapshot, and
asserts the produced payload matches the sibling ``<shot_id>.reference-js.json``
captured from ``AnalyzerService.js`` v1.8.0 via the harness in
``mcp/tests/fixtures/shots/harness/capture.js``.

This file is the normative gate per spec R11: when it goes green, the Python
port behaves identically to the JS source within ``1e-3`` absolute tolerance
for floats and exact equality for integer / ``Math.round``-derived fields.

PER_FIELD_TOL discipline (spec R11):

* Every entry MUST carry an inline ``#`` comment directly above with BOTH the
  JS source line AND a one-line root-cause note. Comments explain WHY the
  tolerance is needed, not just WHERE in the JS source.
* Every field whose value is produced by a JS ``Math.round`` call (the port
  has 4 such call sites that survive into the emitted shape — JS:333, 345,
  899, 902) is forced to strict ``==`` via the ``EXACT`` sentinel.
* The R11-named ``auto_delay.delay_ms``, ``phases[*].estimatedScaleDelayMs``
  surface here as ``EXACT`` entries. ``phases[*].match_step`` is JS-internal
  (JS:619) and never reaches the emitted shape, so it is intentionally absent
  from PER_FIELD_TOL — the spec note "if the port produces fewer such fields,
  the EXACT list shrinks accordingly" applies.

If a future fixture introduces a genuine accumulation-order divergence on a
float field, add a per-path entry with a numeric tolerance and a comment
naming the JS line + root cause. Per the plan veto surface: more than 3 new
PER_FIELD_TOL entries in a single session is a stop-and-surface signal.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from gaggimate_mcp.analysis.shot_analyzer import (
    classify_phase_exits,
    estimate_auto_delay,
)
from gaggimate_mcp.parsers.shot import parse_binary_shot

from tests.shot_fixture_walker import EXACT, compare


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "shots"
SLOG_FIXTURES = sorted(FIXTURE_DIR.glob("*.slog")) if FIXTURE_DIR.exists() else []


# Python-only keys produced by ``classify_phase_exits`` that have no JS
# counterpart in the reference output. Stripped from the comparable Python
# payload so the walker does not flag them as ``extra_key`` mismatches.
_PYTHON_ONLY_PHASE_KEYS = ("exit_reason_type", "unavailable_reason")


def _strip_python_only_phase_keys(phase: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``phase`` with Python-only sentinel keys removed."""
    return {k: v for k, v in phase.items() if k not in _PYTHON_ONLY_PHASE_KEYS}


def _build_per_field_tol() -> dict[str, Any]:
    """Construct the PER_FIELD_TOL allowlist.

    Each entry is paired with an inline comment (above the entry) citing the
    JS source line that produces the field AND a one-line root-cause note.
    Comments explain WHY exact equality is required for that path, not merely
    where the JS code lives.

    The fixtures shipped today have at most 6 phases (246 has 6: indices
    0-5; 247/249 each have 5: indices 0-4). We enumerate phase-indexed
    EXACT entries up to phases[5] so the same allowlist works across all
    three fixtures without per-fixture branching.
    """
    tol: dict[str, Any] = {}

    # JS:899 — usedSettings.scaleDelayMs is ``Math.round(sum/count/50)*50``
    # under auto-adjust (or the seed echo when count==0). Bucketed integer:
    # any float drift would be a port bug, not an accumulation artefact.
    tol["auto_delay.delay_ms"] = EXACT

    # JS:333 — phaseEstimatedScaleDelayMs is js_round of the calculated
    # delay; per-phase integer that must match exactly. Enumerated per
    # phase index because PER_FIELD_TOL paths are concrete (the walker
    # resolves ``phases[N].estimatedScaleDelayMs`` literally).
    # JS:333 — phase 0 estimated scale delay; integer rounded via Math.round, parity must be exact
    tol["phases[0].estimatedScaleDelayMs"] = EXACT
    # JS:333 — phase 1 estimated scale delay; integer rounded via Math.round, parity must be exact
    tol["phases[1].estimatedScaleDelayMs"] = EXACT
    # JS:333 — phase 2 estimated scale delay; integer rounded via Math.round, parity must be exact
    tol["phases[2].estimatedScaleDelayMs"] = EXACT
    # JS:333 — phase 3 estimated scale delay; integer rounded via Math.round, parity must be exact
    tol["phases[3].estimatedScaleDelayMs"] = EXACT
    # JS:333 — phase 4 estimated scale delay; integer rounded via Math.round, parity must be exact
    tol["phases[4].estimatedScaleDelayMs"] = EXACT
    # JS:333 — phase 5 estimated scale delay; integer rounded via Math.round, parity must be exact (only 246 reaches here)
    tol["phases[5].estimatedScaleDelayMs"] = EXACT

    # JS:345 — phaseDelayReviewMs is js_round of the same delay value
    # surfaced into the auto-delay review hint. Integer; exact equality.
    # JS:345 — phase 0 delay-review ms; integer rounded via Math.round, parity must be exact
    tol["phases[0].delayReviewMs"] = EXACT
    # JS:345 — phase 1 delay-review ms; integer rounded via Math.round, parity must be exact
    tol["phases[1].delayReviewMs"] = EXACT
    # JS:345 — phase 2 delay-review ms; integer rounded via Math.round, parity must be exact
    tol["phases[2].delayReviewMs"] = EXACT
    # JS:345 — phase 3 delay-review ms; integer rounded via Math.round, parity must be exact
    tol["phases[3].delayReviewMs"] = EXACT
    # JS:345 — phase 4 delay-review ms; integer rounded via Math.round, parity must be exact
    tol["phases[4].delayReviewMs"] = EXACT
    # JS:345 — phase 5 delay-review ms; integer rounded via Math.round, parity must be exact (only 246 reaches here)
    tol["phases[5].delayReviewMs"] = EXACT

    return tol


PER_FIELD_TOL: dict[str, Any] = _build_per_field_tol()


def _build_comparable(reference: dict[str, Any], py_phases: list, py_auto_delay: dict) -> tuple[dict, dict]:
    """Return ``(expected, actual)`` dicts shaped for the walker.

    Both sides are reduced to the subset of fields covered by the DDSA port:
    ``phases`` (with Python-only keys stripped) and ``auto_delay.delay_ms``
    (mapped from JS ``usedSettings.scaleDelayMs``). The reference's
    additional top-level fields (``total``, ``rawSamples``, ``startTime``,
    ``isAutoAdjusted``, etc.) are out of scope for the port and excluded
    from the comparison.
    """
    expected = {
        "phases": [_strip_python_only_phase_keys(p) for p in reference["phases"]],
        "auto_delay": {"delay_ms": reference["usedSettings"]["scaleDelayMs"]},
    }
    actual = {
        "phases": [_strip_python_only_phase_keys(dict(p)) for p in py_phases],
        "auto_delay": {"delay_ms": py_auto_delay["delay_ms"]},
    }
    return expected, actual


@pytest.mark.parametrize(
    "slog_path",
    SLOG_FIXTURES,
    ids=lambda p: p.stem,
)
def test_python_port_matches_js_reference(slog_path: Path) -> None:
    profile_path = slog_path.with_suffix(".profile.json")
    reference_path = slog_path.with_suffix(".reference-js.json")

    if not profile_path.exists():
        pytest.fail(
            f"Missing profile sibling: {profile_path}; see "
            f"mcp/README.md ## Adding a new fixture for capture instructions"
        )
    if not reference_path.exists():
        pytest.fail(
            f"Missing reference-js sibling: {reference_path}; see "
            f"mcp/README.md ## Adding a new fixture for capture instructions"
        )

    shot_data = parse_binary_shot(slog_path.read_bytes(), slog_path.stem.zfill(6))
    profile_data = json.loads(profile_path.read_text(encoding="utf-8"))
    reference = json.loads(reference_path.read_text(encoding="utf-8"))

    py_phases = classify_phase_exits(shot_data, profile_data)
    py_auto_delay = estimate_auto_delay(shot_data, profile_data)

    expected, actual = _build_comparable(reference, py_phases, py_auto_delay)

    mismatches = compare(
        expected,
        actual,
        max_mismatches=20,
        float_tol=1e-3,
        per_field_tol=PER_FIELD_TOL,
    )

    if mismatches:
        from tests.shot_fixture_walker import _format_mismatch
        lines = [
            f"Parity divergence on fixture {slog_path.stem} "
            f"({len(mismatches)} mismatch(es)):"
        ]
        lines.extend("  " + _format_mismatch(m) for m in mismatches)
        pytest.fail("\n".join(lines))
