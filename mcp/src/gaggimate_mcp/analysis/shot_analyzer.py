"""Port of AnalyzerService.js lines 208–1006 @ gaggimate v1.8.0.

This module ports the device's native shot-analysis algorithm
(``calculateShotMetrics`` + ``detectAutoDelay`` from ``AnalyzerService.js``)
to Python so the MCP server can classify per-phase exit reasons and estimate
the auto scale-delay without requiring a human-in-the-loop chart inspection
in the browser-side analyzer UI.

Stub scaffold: real implementation is filled in by subsequent tasks. See
``lifecycle/port-ddsa-phaseendstop-algorithm-into-diagnose/spec.md`` for the
full requirements.

Re-syncing shot-analyzer on firmware upgrades
---------------------------------------------

See ``mcp/README.md`` for the full runbook (Prerequisites,
Re-syncing shot-analyzer on firmware upgrades, Adding a new fixture).
The runbook content is fleshed out in Task 15; this docstring section
reserves the heading and points readers to the canonical location.
"""

import math
from typing import TypedDict, Literal, Optional, Sequence, Mapping, Any


# Firmware version this port mirrors. Bump when re-syncing against a new
# AnalyzerService.js (see "Re-syncing shot-analyzer on firmware upgrades"
# runbook in mcp/README.md).
ANALYZER_JS_VERSION = "v1.8.0"

# Numeric constants — values mirror AnalyzerService.js v1.8.0 lines 9-14.
# Predictive auto-delay window: how far ahead (ms) to project weight when
# evaluating predictive volumetric/weight stops.
PREDICTIVE_WINDOW_MS = 4000
# Last-phase fallback thresholds (g): bounds applied when classifying the
# final phase's exit reason in the absence of a definitive target hit.
LAST_PHASE_UNDERSHOOT_MIN_G = 2
LAST_PHASE_UNDERSHOOT_MAX_G = 6
LAST_PHASE_OVERSHOOT_MAX_G = 4
LAST_PHASE_ESTIMATED_DELAY_MAX_MS = 4000


class PhaseExitReason(TypedDict):
    """Per-phase exit-reason classification produced by ``classify_phase_exits``.

    ``unavailable_reason`` is always present (TypedDict emits ``None`` explicitly;
    ``json.dumps`` serializes as ``null``). It is ``None`` whenever
    ``exit_reason_type != "unknown"``.
    """
    exit_reason_type: Literal[
        "weight",
        "volumetric",
        "pressure",
        "flow",
        "pumped",
        "duration",
        "unknown",
    ]
    unavailable_reason: Optional[Literal["profile_unavailable"]]


class AutoDelayEstimate(TypedDict):
    """Auto scale-delay estimate produced by ``estimate_auto_delay``.

    ``delay_ms`` is ``None`` when the estimate is unavailable (e.g. profile
    fetch failure). ``unavailable_reason`` follows the same always-present
    contract as ``PhaseExitReason``.
    """
    delay_ms: Optional[int]
    auto: bool
    unavailable_reason: Optional[Literal["profile_unavailable"]]


class ProfileTarget(TypedDict):
    """A single phase-end stop target as embedded in profile JSON.

    Mirrors the device-native shape: ``type`` names the metric being watched
    (``pumped``, ``pressure``, ``flow``, ``volumetric``, ``weight``, etc.),
    ``operator`` is the comparison (``gte``, ``lte``, ...), and ``value`` is
    the numeric threshold.
    """
    type: str
    operator: str
    value: float


class ProfilePhase(TypedDict, total=False):
    """A single phase entry from a profile JSON document.

    Read as raw JSON (no Pydantic validation) so DDSA accepts ``pump.target``
    values outside the existing ``Literal["pressure", "flow"]`` set — most
    notably ``"power"`` (see spec Non-Requirements §power). ``total=False``
    because some phases (e.g. terminal ``Dripping``) omit ``targets``.
    """
    name: str
    phase: str
    valve: int
    duration: float
    temperature: float
    transition: dict
    pump: dict
    targets: list[ProfileTarget]


class ProfileData(TypedDict, total=False):
    """Raw profile JSON snapshot consumed by DDSA.

    Intentionally a TypedDict (not Pydantic) so the analyzer can accept raw
    device JSON including ``"power"`` pump-mode profiles that the existing
    ``models/profile.py`` Pydantic model rejects (Technical Constraint
    §``ProfileData``).
    """
    id: str
    label: str
    type: str
    description: str
    temperature: float
    favorite: bool
    selected: bool
    utility: bool
    phases: list[ProfilePhase]


def js_round(value: float) -> int:
    """Round ``value`` to the nearest integer matching JS ``Math.round`` semantics.

    Python's built-in ``round`` uses banker's rounding (``round(0.5) == 0``,
    ``round(2.5) == 2``), which would produce off-by-one errors versus the
    AnalyzerService.js reference. JS ``Math.round`` rounds halves toward
    positive infinity: ``Math.round(0.5) === 1``, ``Math.round(-0.5) === 0``,
    ``Math.round(2.5) === 3``, ``Math.round(-2.5) === -2``.

    This helper is the foundational rounding primitive used by every
    ``Math.round`` call site in AnalyzerService.js v1.8.0 (lines 407, 447,
    545, 624, 691-692, 804). It is imported by all subsequent DDSA porting
    work (helpers, ``classify_phase_exits``, ``estimate_auto_delay``).
    """
    return math.floor(value + 0.5)


def _coerce_number(value: Any) -> float:
    """Coerce a sample value to a float, treating ``None`` as ``0``.

    Mirrors JS loose-equality null check: ``if (val == null) val = 0``
    (AnalyzerService.js lines 33-34, 41).
    """
    if value is None:
        return 0.0
    return float(value)


def _get_metric_stats(samples: Sequence[Mapping[str, Any]], key: str) -> dict[str, float]:
    """Calculate statistics for a metric across samples.

    Direct port of ``getMetricStats`` (AnalyzerService.js lines 22-64).
    Returns dict with keys ``start``, ``end``, ``min``, ``max``, ``avg``.

    Time-weighted average uses the sample-to-sample dt (in seconds) derived
    from ``samples[i].t`` (milliseconds). For single-sample phases where
    ``totalTime == 0``, the avg falls back to the start value (line 61).
    """
    min_val = math.inf
    max_val = -math.inf
    weighted_sum = 0.0
    total_time = 0.0

    # Start and End values
    start = samples[0].get(key)
    end = samples[-1].get(key)

    # Loose-equality null/undefined guard (JS lines 33-34)
    if start is None:
        start = 0
    if end is None:
        end = 0
    start = float(start)
    end = float(end)

    # Min, Max, and Time-Weighted Average
    for i in range(len(samples)):
        val = _coerce_number(samples[i].get(key))

        if val < min_val:
            min_val = val
        if val > max_val:
            max_val = val

        # Time-weighted average using delta between consecutive samples
        if i > 0:
            dt = (samples[i]["t"] - samples[i - 1]["t"]) / 1000.0
            if dt > 0:
                weighted_sum += val * dt
                total_time += dt

    # Safety for Infinity (no valid samples processed)
    if min_val == math.inf:
        min_val = 0.0
    if max_val == -math.inf:
        max_val = 0.0

    avg = (weighted_sum / total_time) if total_time > 0 else start

    return {
        "start": start,
        "end": end,
        "min": min_val,
        "max": max_val,
        "avg": avg,
    }


def _get_phase_anchor_index_for_weight_rate(
    samples: Sequence[Mapping[str, Any]],
    is_last_phase: bool,
) -> int:
    """Pick the sample index used as prediction anchor for the phase.

    Direct port of ``getPhaseAnchorIndexForWeightRate`` (AnalyzerService.js
    lines 71-80). For the last phase, prefer the last non-extended-recording
    sample to avoid tail-rate artifacts from post-stop drip logging.

    Returns ``-1`` when ``samples`` is empty.

    Note: the Python ``ShotData`` stores ``systemInfo`` as a dict with the
    snake_case key ``extended_recording`` (vs. JS ``extendedRecording``) — see
    ``parsers/shot.py``. We accept both spellings for forward-compat with raw
    JS-shaped fixtures used in regression harnesses.
    """
    if not samples:
        return -1
    if not is_last_phase:
        return len(samples) - 1

    for i in range(len(samples) - 1, -1, -1):
        sys_info = samples[i].get("systemInfo") or {}
        extended = sys_info.get("extended_recording", sys_info.get("extendedRecording"))
        if not extended:
            return i
    return len(samples) - 1


def _get_regression_weight_rate(
    samples: Sequence[Mapping[str, Any]],
    end_index: int,
    window_ms: int = PREDICTIVE_WINDOW_MS,
) -> float:
    """Backend-like weight-rate estimation via linear regression.

    Direct port of ``getRegressionWeightRate`` (AnalyzerService.js lines
    87-125). Computes the linear-regression slope of weight (``v``) over
    time across the last ``window_ms`` of samples up to ``end_index``.

    Returns weight rate in g/s. Returns 0 when:
    - ``end_index`` is out of range
    - the window contains fewer than 2 samples
    - the time-deviation sum-of-squares is below 1e-10 (degenerate regression)
    - the resulting slope is non-positive (no meaningful weight gain)
    """
    if end_index < 1 or end_index >= len(samples):
        return 0.0

    end_time = samples[end_index]["t"]
    cutoff = end_time - window_ms

    start_index = end_index
    while start_index > 0 and samples[start_index - 1]["t"] > cutoff:
        start_index -= 1

    count = end_index - start_index + 1
    if count < 2:
        return 0.0

    t_mean = 0.0
    v_mean = 0.0
    for i in range(start_index, end_index + 1):
        t_mean += samples[i]["t"]
        v_mean += _coerce_number(samples[i].get("v"))
    t_mean /= count
    v_mean /= count

    tdev2 = 0.0
    tdev_vdev = 0.0
    for i in range(start_index, end_index + 1):
        t_dev = samples[i]["t"] - t_mean
        v_dev = _coerce_number(samples[i].get("v")) - v_mean
        tdev_vdev += t_dev * v_dev
        tdev2 += t_dev * t_dev

    if tdev2 < 1e-10:
        return 0.0

    volume_per_millisecond = tdev_vdev / tdev2
    if volume_per_millisecond <= 0:
        return 0.0

    return volume_per_millisecond * 1000.0  # g/ms -> g/s


def _get_phase_weight_rate(
    samples: Sequence[Mapping[str, Any]],
    is_last_phase: bool,
) -> float:
    """Compute the per-phase weight rate (g/s) for prediction.

    Direct port of ``getPhaseWeightRate`` (AnalyzerService.js lines 127-131).
    Composes ``_get_phase_anchor_index_for_weight_rate`` (anchor selection)
    with ``_get_regression_weight_rate`` (4-second regression slope).

    Documented contract:
    - For non-last phases, the anchor is always ``len(samples) - 1`` (the
      last sample in the phase).
    - For the last phase, the anchor is the last non-extended-recording
      sample, falling back to ``len(samples) - 1`` if all samples are
      extended.
    - Returns 0 when the anchor is invalid or the regression is degenerate.
    """
    anchor_index = _get_phase_anchor_index_for_weight_rate(samples, is_last_phase)
    if anchor_index < 0:
        return 0.0
    return _get_regression_weight_rate(samples, anchor_index, PREDICTIVE_WINDOW_MS)


def _update_scale_lost_flag(
    phase_samples: Sequence[Mapping[str, Any]],
    is_brew_by_weight: bool,
    current_flag: bool,
) -> bool:
    """Sticky update for the ``scaleConnectionBrokenPermanently`` flag.

    Direct port of the per-phase scale-lost detection block at
    AnalyzerService.js lines 310-318::

        let scaleLostInThisPhase = false;
        if (isBrewByWeight) {
          scaleLostInThisPhase = samples.some(
            s => s.systemInfo && s.systemInfo.bluetoothScaleConnected === false,
          );
        }
        if (scaleLostInThisPhase) {
          scaleConnectionBrokenPermanently = true;
        }

    The flag is *sticky*: once True, it stays True for the remainder of the
    shot. This drives the four "skip weight target" check sites at JS lines
    407, 447, 545, 624 (``if (isWt && scaleConnectionBrokenPermanently) continue;``)
    and the two fallback-path guards at lines 691-692 and 804
    (``!scaleConnectionBrokenPermanently``) which prevent the last-phase
    weight-stop fallback from firing once the BT scale has dropped.

    Note on Python field-name mapping: ``ShotData.samples`` carries a
    ``systemInfo`` dict whose connectivity flag is ``bluetooth_scale_connected``
    (snake_case, see ``parsers/shot.py``). We accept both that spelling and
    the camelCase JS spelling so the helper works against both Python-parsed
    samples and raw JS-shaped fixtures.
    """
    if current_flag:
        return True
    if not is_brew_by_weight:
        return current_flag

    for sample in phase_samples:
        sys_info = sample.get("systemInfo")
        if not sys_info:
            continue
        # JS strict equality: bluetoothScaleConnected === false
        connected = sys_info.get(
            "bluetooth_scale_connected",
            sys_info.get("bluetoothScaleConnected"),
        )
        if connected is False:
            return True
    return current_flag
