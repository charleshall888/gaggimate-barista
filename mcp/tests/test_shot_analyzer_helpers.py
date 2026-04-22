"""Unit tests for the four DDSA helpers + scale-lost sticky flag.

These tests gate Task 8a on logic correctness against hand-computed expected
values (NOT against reference-JS output). The reference-JS parity check is
deferred to Task 10's regression harness; this file isolates helper math so a
T10 failure narrows to "main algorithm composition" rather than "helper math".

The scale-lost sticky-flag tests use synthetic samples because none of the
shipped 246/247/249 fixtures exhibit a mid-shot BT-scale drop (acknowledged
coverage gap; see ``mcp/README.md`` Known coverage gaps).
"""

import math

from gaggimate_mcp.analysis.shot_analyzer import (
    PREDICTIVE_WINDOW_MS,
    _get_metric_stats,
    _get_phase_anchor_index_for_weight_rate,
    _get_phase_weight_rate,
    _get_regression_weight_rate,
    _update_scale_lost_flag,
)


# ---------------------------------------------------------------------------
# _get_metric_stats
# ---------------------------------------------------------------------------


def test_get_metric_stats_known_window() -> None:
    """10 evenly-spaced samples, weights 1.0..10.0g, dt=100ms each.

    Hand-computed expectations:
    - start = 1.0, end = 10.0
    - min   = 1.0, max = 10.0
    - time-weighted avg = sum(val * dt) / sum(dt)
        = (2+3+4+5+6+7+8+9+10) * 0.1 / (9 * 0.1)
        = 5.4 / 0.9 = 6.0
      (note: the i=0 sample is skipped from the weighted sum per JS lines 47-53)
    """
    samples = [{"t": i * 100, "v": float(i + 1)} for i in range(10)]
    stats = _get_metric_stats(samples, "v")
    assert stats["start"] == 1.0
    assert stats["end"] == 10.0
    assert stats["min"] == 1.0
    assert stats["max"] == 10.0
    assert math.isclose(stats["avg"], 6.0, rel_tol=1e-9)


def test_get_metric_stats_single_sample_falls_back_to_start() -> None:
    """Single-sample phase: totalTime=0 → avg = start (JS line 61)."""
    samples = [{"t": 0, "v": 7.5}]
    stats = _get_metric_stats(samples, "v")
    assert stats["start"] == 7.5
    assert stats["end"] == 7.5
    assert stats["avg"] == 7.5


def test_get_metric_stats_handles_none_as_zero() -> None:
    """JS loose-equality: ``val == null`` treats None/missing as 0."""
    samples = [
        {"t": 0, "v": None},
        {"t": 100, "v": 5.0},
    ]
    stats = _get_metric_stats(samples, "v")
    # start coerced from None → 0
    assert stats["start"] == 0
    assert stats["end"] == 5.0
    assert stats["min"] == 0
    assert stats["max"] == 5.0


# ---------------------------------------------------------------------------
# _get_phase_anchor_index_for_weight_rate
# ---------------------------------------------------------------------------


def test_phase_anchor_non_last_returns_final_index() -> None:
    samples = [{"t": 0, "v": 0.0}, {"t": 100, "v": 1.0}, {"t": 200, "v": 2.0}]
    assert _get_phase_anchor_index_for_weight_rate(samples, is_last_phase=False) == 2


def test_phase_anchor_last_skips_extended_recording_tail() -> None:
    """Last-phase anchor walks back past extended-recording samples."""
    samples = [
        {"t": 0, "v": 0.0, "systemInfo": {"extended_recording": False}},
        {"t": 100, "v": 1.0, "systemInfo": {"extended_recording": False}},
        {"t": 200, "v": 2.0, "systemInfo": {"extended_recording": True}},
        {"t": 300, "v": 2.1, "systemInfo": {"extended_recording": True}},
    ]
    assert _get_phase_anchor_index_for_weight_rate(samples, is_last_phase=True) == 1


def test_phase_anchor_empty_returns_minus_one() -> None:
    assert _get_phase_anchor_index_for_weight_rate([], is_last_phase=True) == -1
    assert _get_phase_anchor_index_for_weight_rate([], is_last_phase=False) == -1


def test_phase_anchor_last_all_extended_falls_back_to_final() -> None:
    samples = [
        {"t": 0, "v": 0.0, "systemInfo": {"extended_recording": True}},
        {"t": 100, "v": 1.0, "systemInfo": {"extended_recording": True}},
    ]
    assert _get_phase_anchor_index_for_weight_rate(samples, is_last_phase=True) == 1


# ---------------------------------------------------------------------------
# _get_regression_weight_rate
# ---------------------------------------------------------------------------


def test_get_regression_weight_rate_linear_ramp() -> None:
    """Linear ramp: t=0,100,...,900ms; v=0.0,0.1,...,0.9g.

    Slope = 0.1g per 100ms = 1.0 g/s. Window covers all 10 samples since
    900ms - 4000ms = -3100ms (full range stays inside the cutoff).
    """
    samples = [{"t": i * 100, "v": i * 0.1} for i in range(10)]
    rate = _get_regression_weight_rate(samples, end_index=9)
    assert math.isclose(rate, 1.0, rel_tol=1e-9, abs_tol=1e-9)


def test_get_regression_weight_rate_window_clip_to_4s() -> None:
    """Samples spanning > 4s: only the trailing 4s window contributes.

    50 samples at 100ms intervals (t=0..4900ms) on a 1.0 g/s ramp.
    end_index=49 → cutoff = 4900-4000 = 900ms → start_index walks back to
    the first sample with t > 900ms (i.e. t=1000ms, index 10), giving 40
    samples in the window. Slope is still 1.0 g/s (linear ramp).
    """
    samples = [{"t": i * 100, "v": i * 0.1} for i in range(50)]
    rate = _get_regression_weight_rate(samples, end_index=49)
    assert math.isclose(rate, 1.0, rel_tol=1e-9, abs_tol=1e-9)


def test_get_regression_weight_rate_flat_returns_zero() -> None:
    """Flat (no weight gain) → tdev2>0 but slope <=0 → returns 0."""
    samples = [{"t": i * 100, "v": 5.0} for i in range(10)]
    rate = _get_regression_weight_rate(samples, end_index=9)
    assert rate == 0.0


def test_get_regression_weight_rate_out_of_range_returns_zero() -> None:
    samples = [{"t": 0, "v": 0.0}, {"t": 100, "v": 0.1}]
    assert _get_regression_weight_rate(samples, end_index=0) == 0.0
    assert _get_regression_weight_rate(samples, end_index=99) == 0.0


def test_get_regression_weight_rate_constant_t_degenerate() -> None:
    """All samples at same t → tdev2 < 1e-10 → return 0."""
    samples = [{"t": 1000, "v": float(i)} for i in range(5)]
    assert _get_regression_weight_rate(samples, end_index=4) == 0.0


# ---------------------------------------------------------------------------
# _get_phase_weight_rate
# ---------------------------------------------------------------------------


def test_get_phase_weight_rate_last_vs_non_last() -> None:
    """Documented contract differs for the final phase.

    Construct a phase with two extended-recording tail samples whose weight
    drops sharply (post-stop drip artifact). For the non-last phase, the
    anchor is the final sample → regression includes the artifact and yields
    a different (smaller, possibly zero) slope. For the last phase, the
    anchor walks back past the extended-recording samples → regression sees
    only the clean ramp and yields ~1.0 g/s.
    """
    # Clean ramp 0..9 at 100ms intervals (10 samples), then 2 extended-
    # recording tail samples that drop the weight back toward zero.
    samples = []
    for i in range(10):
        samples.append({
            "t": i * 100,
            "v": i * 0.1,
            "systemInfo": {"extended_recording": False},
        })
    samples.append({
        "t": 1000,
        "v": 0.4,
        "systemInfo": {"extended_recording": True},
    })
    samples.append({
        "t": 1100,
        "v": 0.2,
        "systemInfo": {"extended_recording": True},
    })

    # Last-phase: anchor = index 9, regression sees clean ramp → ~1.0 g/s.
    rate_last = _get_phase_weight_rate(samples, is_last_phase=True)
    assert math.isclose(rate_last, 1.0, rel_tol=1e-9, abs_tol=1e-9)

    # Non-last: anchor = final index 11 (extended); regression sees the drop.
    # The slope will be different (smaller). Confirm the contract: the two
    # paths produce different rates when the tail is dirty.
    rate_non_last = _get_phase_weight_rate(samples, is_last_phase=False)
    assert rate_non_last != rate_last


def test_get_phase_weight_rate_empty_phase_returns_zero() -> None:
    assert _get_phase_weight_rate([], is_last_phase=True) == 0.0
    assert _get_phase_weight_rate([], is_last_phase=False) == 0.0


# ---------------------------------------------------------------------------
# _update_scale_lost_flag — sticky behavior + trigger conditions
# ---------------------------------------------------------------------------


def test_scale_lost_flag_sticky() -> None:
    """Once True, the flag stays True even when subsequent samples are clean.

    Mirrors the JS sticky pattern: ``scaleConnectionBrokenPermanently`` is
    only ever set, never cleared (lines 268, 316-318).
    """
    clean_samples = [
        {"t": 0, "v": 0.0, "systemInfo": {"bluetooth_scale_connected": True}},
        {"t": 100, "v": 0.5, "systemInfo": {"bluetooth_scale_connected": True}},
    ]
    # Starts True (a previous phase already broke the connection).
    result = _update_scale_lost_flag(clean_samples, is_brew_by_weight=True, current_flag=True)
    assert result is True

    # Even with is_brew_by_weight=False (which would otherwise short-circuit
    # to current_flag), the sticky True propagates.
    result_off = _update_scale_lost_flag(clean_samples, is_brew_by_weight=False, current_flag=True)
    assert result_off is True


def test_scale_lost_flag_triggers_on_bt_drop() -> None:
    """Flag flips False → True when any sample reports BT-scale disconnect.

    Synthetic phase: scale was connected for 4 samples, then dropped on
    sample 5 (and stays disconnected). Per JS strict-equality check
    (``bluetoothScaleConnected === false``), the helper sets the sticky flag
    to True for the entire phase via ``samples.some(...)``.

    Note: the original Task 8a wording referred to "cumulative weight drop"
    but the JS-faithful trigger keys on ``systemInfo.bluetoothScaleConnected
    === false`` (lines 244-247, 311-318), not on weight delta. This test
    matches the actual ported semantics.
    """
    samples = [
        {"t": 0, "v": 0.0, "systemInfo": {"bluetooth_scale_connected": True}},
        {"t": 100, "v": 0.2, "systemInfo": {"bluetooth_scale_connected": True}},
        {"t": 200, "v": 0.4, "systemInfo": {"bluetooth_scale_connected": True}},
        {"t": 300, "v": 0.6, "systemInfo": {"bluetooth_scale_connected": True}},
        {"t": 400, "v": 0.8, "systemInfo": {"bluetooth_scale_connected": False}},
    ]
    result = _update_scale_lost_flag(samples, is_brew_by_weight=True, current_flag=False)
    assert result is True


def test_scale_lost_flag_no_trigger_when_not_brew_by_weight() -> None:
    """Outside brew-by-weight mode, the helper never sets the flag.

    JS lines 311-315 only run the ``samples.some(...)`` check when
    ``isBrewByWeight`` is true.
    """
    samples = [
        {"t": 0, "v": 0.0, "systemInfo": {"bluetooth_scale_connected": False}},
    ]
    result = _update_scale_lost_flag(samples, is_brew_by_weight=False, current_flag=False)
    assert result is False


def test_scale_lost_flag_no_trigger_when_all_connected() -> None:
    samples = [
        {"t": 0, "v": 0.0, "systemInfo": {"bluetooth_scale_connected": True}},
        {"t": 100, "v": 0.5, "systemInfo": {"bluetooth_scale_connected": True}},
    ]
    result = _update_scale_lost_flag(samples, is_brew_by_weight=True, current_flag=False)
    assert result is False


def test_scale_lost_flag_ignores_missing_systeminfo() -> None:
    """JS guard: ``s.systemInfo && s.systemInfo.bluetoothScaleConnected === false``.

    Samples without systemInfo (or with None) are skipped — they don't trigger
    the flag.
    """
    samples = [
        {"t": 0, "v": 0.0},  # no systemInfo at all
        {"t": 100, "v": 0.2, "systemInfo": None},
        {"t": 200, "v": 0.4, "systemInfo": {}},  # systemInfo exists but no connectivity field
    ]
    result = _update_scale_lost_flag(samples, is_brew_by_weight=True, current_flag=False)
    assert result is False


def test_scale_lost_flag_accepts_camelcase_spelling() -> None:
    """Forward-compat: helper also reads JS-shaped ``bluetoothScaleConnected``.

    The Python ShotData uses ``bluetooth_scale_connected``, but JS-shaped
    regression-harness fixtures may use the camelCase spelling. The helper
    accepts both.
    """
    samples = [
        {"t": 0, "v": 0.0, "systemInfo": {"bluetoothScaleConnected": False}},
    ]
    result = _update_scale_lost_flag(samples, is_brew_by_weight=True, current_flag=False)
    assert result is True


# ---------------------------------------------------------------------------
# Constants sanity check
# ---------------------------------------------------------------------------


def test_predictive_window_constant() -> None:
    """Lock in the JS-mirrored constant so a future change is loud."""
    assert PREDICTIVE_WINDOW_MS == 4000
