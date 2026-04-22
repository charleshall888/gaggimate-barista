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
from typing import TypedDict, Literal, Optional, Sequence, Mapping, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from gaggimate_mcp.parsers.shot import ShotData


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


class PhaseExitReason(TypedDict, total=False):
    """Per-phase exit-reason classification produced by ``classify_phase_exits``.

    Mirrors the per-phase object shape emitted by
    ``calculateShotMetrics`` in ``AnalyzerService.js`` v1.8.0 (see the
    ``analyzedPhases.push({...})`` block at JS lines 847-890). Field names use
    camelCase to match the JS reference output verbatim — the parity test
    (Task 10) walks both Python and JS payloads so divergent key spellings
    would surface as missing fields.

    ``exit_reason_type`` and ``unavailable_reason`` are the two snake_case
    Python-side fields used by downstream consumers (``analyze_shot`` MCP
    response, ``/diagnose`` skill output). They duplicate / wrap the JS
    ``exit.type`` field and add a profile-fetch failure mode the JS source
    does not need to express.

    ``unavailable_reason`` is always present (TypedDict emits ``None``
    explicitly; ``json.dumps`` serializes as ``null``). It is ``None``
    whenever ``exit_reason_type != "unknown"``.

    ``total=False`` so degraded ``profile_unavailable`` outputs (and any
    JS-emitted optional fields like ``targetCalcValues``) can omit the
    ``ShotData``-derived measurements without runtime error.
    """
    # Python-side classification (always emitted)
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

    # JS-mirrored fields (per-phase object emitted by calculateShotMetrics)
    number: str
    name: Optional[str]
    displayName: str
    start: float
    end: float
    duration: float
    water: float
    weight: float
    stats: dict
    exit: dict
    profilePhase: Optional[dict]
    scaleLost: bool
    scalePermanentlyLost: bool
    highScaleDelay: bool
    estimatedScaleDelayMs: Optional[int]
    delayReviewHint: bool
    delayReviewReason: Optional[str]
    delayReviewMs: Optional[int]
    prediction: dict
    targetCalcValues: Optional[dict]


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


# ---------------------------------------------------------------------------
# Inline JS helpers (used by classify_phase_exits)
# ---------------------------------------------------------------------------


def _get_sample_instant_weight_rate(sample: Optional[Mapping[str, Any]]) -> float:
    """Direct port of ``getSampleInstantWeightRate`` (JS lines 133-138).

    Prefer ``vf`` (volumetric flow) when above 0.1 g/s, fall back to ``fl``
    (pump flow), else 0.
    """
    if not sample:
        return 0.0
    vf = sample.get("vf")
    if vf is not None and vf > 0.1:
        return float(vf)
    fl = sample.get("fl")
    if fl is not None and fl > 0.1:
        return float(fl)
    return 0.0


def _is_directionally_valid_look_ahead(
    operator: str, current_value: float, next_value: float
) -> bool:
    """Direct port of ``isDirectionallyValidLookAhead`` (JS lines 140-145)."""
    if not (math.isfinite(current_value) and math.isfinite(next_value)):
        return False
    if operator == "gte":
        return next_value >= current_value
    if operator == "lte":
        return next_value <= current_value
    return True


def _get_last_non_extended_index(samples: Sequence[Mapping[str, Any]]) -> int:
    """Direct port of ``getLastNonExtendedIndex`` (JS lines 147-153)."""
    if not samples:
        return -1
    for i in range(len(samples) - 1, -1, -1):
        sys_info = samples[i].get("systemInfo") or {}
        extended = sys_info.get(
            "extended_recording", sys_info.get("extendedRecording")
        )
        if not extended:
            return i
    return len(samples) - 1


def _format_stop_reason(type_: Optional[str]) -> str:
    """Direct port of ``formatStopReason`` (JS lines 181-195)."""
    if not type_:
        return ""
    t = type_.lower()
    if t == "duration":
        return "Time Stop"
    if t == "pumped":
        return "Water Drawn Stop"
    if t in ("volumetric", "weight"):
        return "Weight Stop"
    if t == "pressure":
        return "Pressure Stop"
    if t == "flow":
        return "Flow Stop"
    return f"{t[0].upper() + t[1:]} Stop"


# Dual-spelling sample-key accessors (Python parser uses snake_case; JS uses
# camelCase). We accept both so the same algorithm runs on Python ShotData
# and on raw JS-shaped fixtures used by harnesses / future replay tools.
def _sample_phase_number(sample: Mapping[str, Any]) -> Optional[int]:
    """Return the sample's phase number, accepting JS or Python spelling."""
    if "phaseNumber" in sample:
        return sample["phaseNumber"]
    if "phase" in sample:
        return sample["phase"]
    return None


def _sample_sys_field(
    sys_info: Optional[Mapping[str, Any]],
    snake: str,
    camel: str,
) -> Any:
    """Read ``sys_info[snake]`` falling back to ``sys_info[camel]``."""
    if not sys_info:
        return None
    if snake in sys_info:
        return sys_info[snake]
    return sys_info.get(camel)


# Map of (snake_case, camelCase) field-name pairs for the systemInfo block.
# Used by the per-phase sysAnomalies + final-sysInfo readers below.
_SYS_FIELD_PAIRS: Sequence[tuple[str, str, str]] = (
    ("sys_shot_vol", "shot_started_volumetric", "shotStartedVolumetric"),
    ("sys_curr_vol", "currently_volumetric", "currentlyVolumetric"),
    ("sys_scale", "bluetooth_scale_connected", "bluetoothScaleConnected"),
    ("sys_vol_avail", "volumetric_available", "volumetricAvailable"),
    ("sys_ext", "extended_recording", "extendedRecording"),
)


def _normalize_systeminfo(sys_info: Optional[Mapping[str, Any]]) -> dict:
    """Return a copy of ``sys_info`` keyed by camelCase only.

    Mirrors what the JS reference output emits inside ``stats.sys_*`` and
    inside per-sample ``systemInfo`` blocks. The Python parser stores
    snake_case keys; the helpers normalize on read so the algorithm body can
    work with one canonical spelling regardless of input shape.
    """
    if not sys_info:
        return {}
    out: dict = {}
    if "raw" in sys_info:
        out["raw"] = sys_info["raw"]
    for _stats_key, snake, camel in _SYS_FIELD_PAIRS:
        if camel in sys_info:
            out[camel] = sys_info[camel]
        elif snake in sys_info:
            out[camel] = sys_info[snake]
    return out


def _phase_transitions_to_name_map(raw_shot: Any) -> dict[int, str]:
    """Build a phase-number → phase-name map from ShotData.phases.

    Mirrors the JS:
        shotData.phaseTransitions.forEach(pt => {
          phaseNameMap[pt.phaseNumber] = pt.phaseName;
        });

    Accepts either the Python ``ShotData`` (whose ``phases`` is a list of
    ``PhaseTransition`` dataclasses) or a raw dict-shaped object whose
    ``phaseTransitions`` is a list of ``{phaseNumber, phaseName}`` dicts.
    """
    name_map: dict[int, str] = {}
    transitions = getattr(raw_shot, "phases", None)
    if transitions is None and isinstance(raw_shot, Mapping):
        transitions = raw_shot.get("phaseTransitions") or raw_shot.get("phases")
    if not transitions:
        return name_map
    for pt in transitions:
        # PhaseTransition dataclass
        if hasattr(pt, "phase_number") and hasattr(pt, "phase_name"):
            name_map[pt.phase_number] = pt.phase_name
        # raw JS-shaped dict
        elif isinstance(pt, Mapping):
            num = pt.get("phaseNumber", pt.get("phase_number"))
            nm = pt.get("phaseName", pt.get("phase_name"))
            if num is not None:
                name_map[num] = nm
    return name_map


def _shot_samples(raw_shot: Any) -> Sequence[Mapping[str, Any]]:
    """Extract the samples list from a Python ShotData or raw dict."""
    if isinstance(raw_shot, Mapping):
        return raw_shot.get("samples") or []
    return getattr(raw_shot, "samples", []) or []


def _shot_sample_interval(raw_shot: Any, default: int = 250) -> int:
    """Extract the sample interval (ms), defaulting to 250 to match JS."""
    if isinstance(raw_shot, Mapping):
        return raw_shot.get("sampleInterval") or raw_shot.get("sample_interval") or default
    return getattr(raw_shot, "sample_interval", None) or default


def _build_default_phase_exit(
    *,
    number: int,
    display_name: str,
    name: Optional[str],
    exit_reason_type: str = "unknown",
    unavailable_reason: Optional[str] = None,
) -> PhaseExitReason:
    """Construct a degraded PhaseExitReason for the profile-unavailable path."""
    return PhaseExitReason(
        exit_reason_type=exit_reason_type,  # type: ignore[typeddict-item]
        unavailable_reason=unavailable_reason,  # type: ignore[typeddict-item]
        number=str(number),
        name=name,
        displayName=display_name,
        start=0.0,
        end=0.0,
        duration=0.0,
        water=0.0,
        weight=0.0,
        stats={},
        exit={"reason": None, "type": None},
        profilePhase=None,
        scaleLost=False,
        scalePermanentlyLost=False,
        highScaleDelay=False,
        estimatedScaleDelayMs=None,
        delayReviewHint=False,
        delayReviewReason=None,
        delayReviewMs=None,
        prediction={"finalWeight": None},
        targetCalcValues=None,
    )


def _run_phase_analysis(
    raw_shot: "ShotData",
    profile_snapshot: ProfileData,
) -> dict[str, Any]:
    """Internal port of ``calculateShotMetrics`` (JS lines 208-991).

    Returns a dict with two keys:

    * ``phases``: ``list[PhaseExitReason]`` — one per observed phase, the
      payload exposed by :func:`classify_phase_exits`.
    * ``auto_delay_settings``: ``{"scaleDelayMs": Optional[int],
      "sensorDelayMs": Optional[int]}`` — the JS ``usedSettings`` object
      consumed by :func:`estimate_auto_delay`. Each value is the average
      delay across all hits, rounded to the nearest 50 ms via
      ``Math.round(sum/count/50)*50``; ``None`` when no hits accumulated.

    Both ``classify_phase_exits`` and ``estimate_auto_delay`` are thin
    wrappers over this single internal pass — neither re-runs the
    expensive per-phase analysis. The accumulators ``sum_scale_delay`` /
    ``count_scale_hits`` / ``sum_sensor_delay`` / ``count_sensor_hits``
    mirror the JS source (lines 263-266) and are incremented at the same
    three sites: the main match (JS:607-611) and the two last-phase
    fallback paths (JS:751-752, 781-782).

    Direct port of the per-phase body of ``calculateShotMetrics``
    (``AnalyzerService.js`` v1.8.0 lines 208-991). Returns one
    :class:`PhaseExitReason` per observed phase in ``raw_shot.samples``
    (grouped by ``phaseNumber`` / ``phase``), mirroring the JS
    ``analyzedPhases.push({...})`` block at JS lines 847-890.

    The composition of helpers mirrors the JS source exactly:
    ``_get_metric_stats`` (JS getMetricStats), ``_get_phase_weight_rate``
    (JS getPhaseWeightRate, which composes
    ``_get_phase_anchor_index_for_weight_rate`` +
    ``_get_regression_weight_rate``), and ``_update_scale_lost_flag``
    (JS lines 310-318 sticky flag).

    The 4 scale-lost check sites (JS lines 407, 447, 545, 624) and the
    2 fallback-path guards (JS lines 691-692, 804) are wired explicitly;
    each uses ``scale_connection_broken_permanently`` updated via
    ``_update_scale_lost_flag`` at the head of every phase iteration.

    Settings used by the port are pinned to the Gaggimate web UI
    defaults (see ``HARNESS_SETTINGS`` in
    ``mcp/tests/fixtures/shots/harness/capture.js`` — ``scaleDelayMs=200``,
    ``sensorDelayMs=200``, ``isAutoAdjusted=True``). The function exposes
    no settings parameter because the consumer (``analyze_shot``) always
    invokes it with the auto-adjust mode; the manual-mode branch is
    ported but unreachable through the public API.

    The ``'duration'`` token is preserved verbatim per spec Technical
    Constraints (NOT renamed to ``'time'``).
    """
    SCALE_DELAY_MS = 200
    SENSOR_DELAY_MS = 200
    IS_AUTO_ADJUSTED = True

    # JS:263-266 — auto-delay accumulators consumed at JS:893-904 to derive
    # ``usedSettings``. Surfaced through this helper so estimate_auto_delay
    # can read them without re-running the per-phase analysis.
    sum_scale_delay: float = 0.0
    count_scale_hits: int = 0
    sum_sensor_delay: float = 0.0
    count_sensor_hits: int = 0

    empty_settings: dict[str, Optional[int]] = {
        "scaleDelayMs": None,
        "sensorDelayMs": None,
    }

    g_samples = _shot_samples(raw_shot)
    if not g_samples:
        # JS line 210-212: defensive guard for empty sample data
        return {"phases": [], "auto_delay_settings": empty_settings}

    sample_interval = _shot_sample_interval(raw_shot)
    global_start_time = g_samples[0]["t"]

    # --- 1. PHASE SEPARATION ---
    phases: dict[int, list[Mapping[str, Any]]] = {}
    phase_name_map = _phase_transitions_to_name_map(raw_shot)

    for sample in g_samples:
        p_num = _sample_phase_number(sample)
        if p_num is None:
            continue
        phases.setdefault(p_num, []).append(sample)

    sorted_phase_keys = sorted(phases.keys())
    if not sorted_phase_keys:
        return {"phases": [], "auto_delay_settings": empty_settings}
    last_phase_key = sorted_phase_keys[-1]

    # --- 2. BREW MODE DETECTION ---
    start_sys_info = g_samples[0].get("systemInfo") or {}
    is_brew_by_weight = (
        _sample_sys_field(
            start_sys_info, "shot_started_volumetric", "shotStartedVolumetric"
        )
        is True
    )

    # Profile-unavailable degradation path: emit one degraded exit per
    # observed phase. This mirrors what Task 11's analyze_shot wrapper does
    # when the profile fetch fails — but classify_phase_exits also exposes it
    # directly so callers passing an empty/unset ProfileData get a clean
    # per-phase response rather than partial real data.
    profile_phases = profile_snapshot.get("phases") if profile_snapshot else None
    if not profile_phases:
        out: list[PhaseExitReason] = []
        for phase_num in sorted_phase_keys:
            samples = phases[phase_num]
            p_start = (samples[0]["t"] - global_start_time) / 1000.0
            p_end = (samples[-1]["t"] - global_start_time) / 1000.0
            raw_name = phase_name_map.get(phase_num)
            display_name = raw_name if raw_name else f"Phase {phase_num}"
            out.append(
                _build_default_phase_exit(
                    number=phase_num,
                    display_name=display_name,
                    name=raw_name,
                    exit_reason_type="unknown",
                    unavailable_reason="profile_unavailable",
                )
            )
            _ = p_start, p_end  # quiet linters
        return {"phases": out, "auto_delay_settings": empty_settings}

    # --- 4. PHASE-BY-PHASE ANALYSIS ---
    analyzed_phases: list[PhaseExitReason] = []
    scale_connection_broken_permanently = False

    for phase_num in sorted_phase_keys:
        samples = phases[phase_num]
        p_start = (samples[0]["t"] - global_start_time) / 1000.0
        p_end = (samples[-1]["t"] - global_start_time) / 1000.0
        duration = p_end - p_start

        is_last_phase = phase_num == last_phase_key
        phase_weight_rate = _get_phase_weight_rate(samples, is_last_phase)

        raw_name = phase_name_map.get(phase_num)
        display_name = raw_name if raw_name else f"Phase {phase_num}"

        # System Info on the last sample of the phase (camelCase-normalized)
        last_sample_in_phase = samples[-1]
        sys_info = _normalize_systeminfo(last_sample_in_phase.get("systemInfo"))

        sys_field_map = (
            ("sys_shot_vol", "shotStartedVolumetric"),
            ("sys_curr_vol", "currentlyVolumetric"),
            ("sys_scale", "bluetoothScaleConnected"),
            ("sys_vol_avail", "volumetricAvailable"),
            ("sys_ext", "extendedRecording"),
        )
        sys_anomalies: dict = {}
        for stats_key, sample_key in sys_field_map:
            final_value = sys_info.get(sample_key)
            if not isinstance(final_value, bool):
                continue
            mismatch_index = -1
            for idx, sample in enumerate(samples):
                norm = _normalize_systeminfo(sample.get("systemInfo"))
                sample_value = norm.get(sample_key)
                if isinstance(sample_value, bool) and sample_value != final_value:
                    mismatch_index = idx
                    break
            if mismatch_index < 0:
                continue
            mismatch_norm = _normalize_systeminfo(
                samples[mismatch_index].get("systemInfo")
            )
            mismatch_sample_value = mismatch_norm.get(sample_key)
            if not isinstance(mismatch_sample_value, bool):
                continue
            sys_anomalies[stats_key] = {
                "sampleInPhase": mismatch_index + 1,
                "sampleCountInPhase": len(samples),
                "value": mismatch_sample_value,
            }

        # Sticky scale-lost flag (JS lines 310-318)
        scale_lost_in_this_phase = False
        if is_brew_by_weight:
            for s in samples:
                norm = _normalize_systeminfo(s.get("systemInfo"))
                if norm.get("bluetoothScaleConnected") is False:
                    scale_lost_in_this_phase = True
                    break
        if scale_lost_in_this_phase:
            scale_connection_broken_permanently = True
        # Defensive: also let the helper update the flag (no-op when already true).
        scale_connection_broken_permanently = _update_scale_lost_flag(
            samples, is_brew_by_weight, scale_connection_broken_permanently
        )

        # --- EXIT REASON & AUTO-DELAY LOGIC ---
        exit_reason: Optional[str] = None
        exit_type: Optional[str] = None
        final_predicted_weight: Optional[float] = None
        target_calc_values: Optional[dict] = None
        profile_phase: Optional[dict] = None
        phase_high_scale_delay = False
        phase_estimated_scale_delay_ms: Optional[int] = None
        phase_delay_review_hint = False
        phase_delay_review_reason: Optional[str] = None
        phase_delay_review_ms: Optional[int] = None

        def set_estimated_scale_delay(delay_ms: Optional[float]) -> None:
            nonlocal phase_estimated_scale_delay_ms, phase_high_scale_delay
            if delay_ms is None or not math.isfinite(delay_ms) or delay_ms < 0:
                return
            rounded_delay = js_round(delay_ms)
            if (
                phase_estimated_scale_delay_ms is None
                or rounded_delay > phase_estimated_scale_delay_ms
            ):
                phase_estimated_scale_delay_ms = rounded_delay
            if is_last_phase and rounded_delay > 2000:
                phase_high_scale_delay = True

        def set_phase_delay_review_hint(
            delay_ms: Optional[float], reason: Optional[str]
        ) -> None:
            nonlocal phase_delay_review_hint, phase_delay_review_reason, phase_delay_review_ms
            if delay_ms is None or not math.isfinite(delay_ms) or delay_ms < 1000:
                return
            rounded_delay = js_round(delay_ms)
            phase_delay_review_hint = True
            phase_delay_review_reason = reason or "manual-check"
            if phase_delay_review_ms is None or rounded_delay > phase_delay_review_ms:
                phase_delay_review_ms = rounded_delay

        if profile_snapshot and profile_phases:
            clean_name = raw_name.strip().lower() if raw_name else ""
            profile_phase = next(
                (
                    p
                    for p in profile_phases
                    if p.get("name", "").strip().lower() == clean_name
                ),
                None,
            )

            if profile_phase:
                prof_dur = profile_phase.get("duration", 0)

                # Time Limit Check (JS lines 360-364)
                if abs(duration - prof_dur) < 0.5 or duration >= prof_dur:
                    exit_reason = "Time Limit"
                    exit_type = "duration"

                profile_targets = profile_phase.get("targets") or []

                # Check target-based exits (JS line 367)
                if profile_targets and (
                    not exit_type or duration < prof_dur - 0.5
                ):
                    found_match = False

                    s_interval = sample_interval or 250
                    s_interval_sec = s_interval / 1000.0
                    current_key_index = sorted_phase_keys.index(phase_num)
                    next_phase_key = (
                        sorted_phase_keys[current_key_index + 1]
                        if 0 <= current_key_index < len(sorted_phase_keys) - 1
                        else None
                    )
                    next_phase_samples = (
                        phases.get(next_phase_key, []) if next_phase_key is not None else []
                    )
                    last_non_extended_index = _get_last_non_extended_index(samples)
                    last_non_extended_sample = (
                        samples[last_non_extended_index]
                        if last_non_extended_index >= 0
                        else samples[-1]
                    )

                    # Anchor: last non-extended sample for last phase, otherwise last sample
                    anchor_idx = (
                        last_non_extended_index
                        if (is_last_phase and last_non_extended_index >= 0)
                        else len(samples) - 1
                    )
                    anchor = samples[anchor_idx]
                    prev_anchor = samples[anchor_idx - 1] if anchor_idx > 0 else anchor

                    # Cumulative pumped water up to anchor
                    anchor_pumped = 0.0
                    for i in range(1, anchor_idx + 1):
                        dt = (samples[i]["t"] - samples[i - 1]["t"]) / 1000.0
                        anchor_pumped += _coerce_number(samples[i].get("fl")) * dt

                    # Prediction setup: weight rate and pressure/flow slopes
                    w_rate = _get_phase_weight_rate(samples, is_last_phase)
                    anchor_dt = (anchor["t"] - prev_anchor["t"]) / 1000.0
                    p_slope = (
                        (anchor.get("cp", 0) - prev_anchor.get("cp", 0)) / anchor_dt
                        if anchor_dt > 0
                        else 0.0
                    )
                    f_slope = (
                        (
                            _coerce_number(anchor.get("fl"))
                            - _coerce_number(prev_anchor.get("fl"))
                        )
                        / anchor_dt
                        if anchor_dt > 0
                        else 0.0
                    )

                    # --- Helper: check targets against given values (JS 402-436) ---
                    def try_targets(
                        p_val: float, f_val: float, w_val: float, pumped: float, delay_ms: float
                    ) -> Optional[dict]:
                        for tgt in profile_targets:
                            is_wt = tgt.get("type") in ("volumetric", "weight")
                            if is_wt and not is_brew_by_weight:
                                continue
                            # JS:407 — scale-lost check site #1
                            if is_wt and scale_connection_broken_permanently:
                                continue
                            if (
                                is_last_phase
                                and is_wt
                                and last_non_extended_sample.get("v", 0)
                                > tgt["value"] + LAST_PHASE_OVERSHOOT_MAX_G
                            ):
                                continue

                            t_type = tgt.get("type")
                            if t_type == "pressure":
                                val = p_val
                            elif t_type == "flow":
                                val = f_val
                            elif is_wt:
                                val = w_val
                            elif t_type == "pumped":
                                val = pumped
                            else:
                                continue

                            hit = False
                            op = tgt.get("operator")
                            if op == "gte" and val >= tgt["value"]:
                                if not (
                                    is_last_phase
                                    and is_wt
                                    and val > tgt["value"] + LAST_PHASE_OVERSHOOT_MAX_G
                                ):
                                    hit = True
                            if op == "lte" and val <= tgt["value"]:
                                hit = True

                            if hit:
                                return {
                                    "target": tgt,
                                    "delayMs": delay_ms,
                                    "predictedWeight": val if is_wt else None,
                                }
                        return None

                    # --- Helper: check targets with direction validation (JS 439-495) ---
                    def try_targets_with_dir(
                        next_sample: Mapping[str, Any], n_steps: int
                    ) -> Optional[dict]:
                        horizon = n_steps * s_interval_sec
                        next_dt = (next_sample["t"] - anchor["t"]) / 1000.0

                        for tgt in profile_targets:
                            is_wt = tgt.get("type") in ("volumetric", "weight")
                            if is_wt and not is_brew_by_weight:
                                continue
                            # JS:447 — scale-lost check site #2
                            if is_wt and scale_connection_broken_permanently:
                                continue
                            if (
                                is_last_phase
                                and is_wt
                                and last_non_extended_sample.get("v", 0)
                                > tgt["value"] + LAST_PHASE_OVERSHOOT_MAX_G
                            ):
                                continue

                            t_type = tgt.get("type")
                            if t_type == "pressure":
                                anchor_val = anchor.get("cp", 0)
                                next_val = next_sample.get("cp", 0)
                                pred_val = max(0.0, anchor.get("cp", 0) + p_slope * horizon)
                            elif t_type == "flow":
                                anchor_val = _coerce_number(anchor.get("fl"))
                                next_val = _coerce_number(next_sample.get("fl"))
                                pred_val = max(
                                    0.0, _coerce_number(anchor.get("fl")) + f_slope * horizon
                                )
                            elif is_wt:
                                anchor_val = anchor.get("v", 0)
                                next_val = next_sample.get("v", 0)
                                pred_val = anchor.get("v", 0) + (
                                    w_rate * horizon if w_rate > 0 else 0
                                )
                            elif t_type == "pumped":
                                anchor_val = anchor_pumped
                                next_val = anchor_pumped + _coerce_number(
                                    next_sample.get("fl")
                                ) * next_dt
                                pred_val = anchor_pumped + max(
                                    0.0, _coerce_number(anchor.get("fl"))
                                ) * horizon
                            else:
                                continue

                            dir_valid = _is_directionally_valid_look_ahead(
                                tgt.get("operator", ""), anchor_val, next_val
                            )
                            val = next_val if dir_valid else pred_val

                            hit = False
                            op = tgt.get("operator")
                            if op == "gte" and val >= tgt["value"]:
                                if not (
                                    is_last_phase
                                    and is_wt
                                    and val > tgt["value"] + LAST_PHASE_OVERSHOOT_MAX_G
                                ):
                                    hit = True
                            if op == "lte" and val <= tgt["value"]:
                                hit = True

                            if hit:
                                return {
                                    "target": tgt,
                                    "delayMs": n_steps * s_interval,
                                    "predictedWeight": val if is_wt else None,
                                }
                        return None

                    # --- Helper: predict at N steps ahead (JS 498-506) ---
                    def predict_at(n_steps: int) -> dict:
                        h = n_steps * s_interval_sec
                        return {
                            "p": max(0.0, anchor.get("cp", 0) + p_slope * h),
                            "f": max(0.0, _coerce_number(anchor.get("fl")) + f_slope * h),
                            "w": anchor.get("v", 0) + (w_rate * h if w_rate > 0 else 0),
                            "pumped": anchor_pumped
                            + max(0.0, _coerce_number(anchor.get("fl"))) * h,
                        }

                    match: Optional[dict] = None

                    if IS_AUTO_ADJUSTED:
                        # AUTO MODE: 4-step detection (JS 510-533)
                        # STEP 1: at anchor (delay=0)
                        match = try_targets(
                            anchor.get("cp", 0),
                            _coerce_number(anchor.get("fl")),
                            anchor.get("v", 0),
                            anchor_pumped,
                            0,
                        )
                        # STEP 2: first next-phase sample
                        if not match and len(next_phase_samples) > 0:
                            match = try_targets_with_dir(next_phase_samples[0], 1)
                        # STEP 3: second next-phase sample
                        if not match and len(next_phase_samples) > 1:
                            match = try_targets_with_dir(next_phase_samples[1], 2)
                        # STEP 4: predictive extrapolation fallback
                        if not match:
                            max_steps = math.ceil(
                                LAST_PHASE_ESTIMATED_DELAY_MAX_MS / s_interval
                            )
                            for step in range(3, max_steps + 1):
                                if match:
                                    break
                                pred = predict_at(step)
                                match = try_targets(
                                    pred["p"],
                                    pred["f"],
                                    pred["w"],
                                    pred["pumped"],
                                    step * s_interval,
                                )
                    else:
                        # MANUAL MODE: predict with user-configured delays (JS 535-580)
                        norm_scale_ms = max(0, SCALE_DELAY_MS or 0)
                        norm_sensor_ms = max(0, SENSOR_DELAY_MS or 0)
                        scale_delay_sec = norm_scale_ms / 1000.0
                        sensor_delay_sec = norm_sensor_ms / 1000.0

                        for tgt in profile_targets:
                            if match:
                                break
                            is_wt = tgt.get("type") in ("volumetric", "weight")
                            if is_wt and not is_brew_by_weight:
                                continue
                            # JS:545 — scale-lost check site #3
                            if is_wt and scale_connection_broken_permanently:
                                continue
                            if (
                                is_last_phase
                                and is_wt
                                and last_non_extended_sample.get("v", 0)
                                > tgt["value"] + LAST_PHASE_OVERSHOOT_MAX_G
                            ):
                                continue

                            t_type = tgt.get("type")
                            delay_ms_val = 0
                            if t_type == "pressure":
                                val = max(
                                    0.0, anchor.get("cp", 0) + p_slope * sensor_delay_sec
                                )
                                delay_ms_val = norm_sensor_ms
                            elif t_type == "flow":
                                val = max(
                                    0.0,
                                    _coerce_number(anchor.get("fl")) + f_slope * sensor_delay_sec,
                                )
                                delay_ms_val = norm_sensor_ms
                            elif is_wt:
                                val = anchor.get("v", 0) + (
                                    w_rate * scale_delay_sec if w_rate > 0 else 0
                                )
                                delay_ms_val = norm_scale_ms
                            elif t_type == "pumped":
                                val = anchor_pumped + max(
                                    0.0, _coerce_number(anchor.get("fl"))
                                ) * sensor_delay_sec
                                delay_ms_val = norm_sensor_ms
                            else:
                                continue

                            hit = False
                            op = tgt.get("operator")
                            if op == "gte" and val >= tgt["value"]:
                                if not (
                                    is_last_phase
                                    and is_wt
                                    and val > tgt["value"] + LAST_PHASE_OVERSHOOT_MAX_G
                                ):
                                    hit = True
                            if op == "lte" and val <= tgt["value"]:
                                hit = True

                            if hit:
                                match = {
                                    "target": tgt,
                                    "delayMs": delay_ms_val,
                                    "predictedWeight": val if is_wt else None,
                                }

                    # --- Process match result (JS 584-678) ---
                    if match:
                        exit_reason = _format_stop_reason(match["target"]["type"])
                        exit_type = match["target"]["type"]
                        final_predicted_weight = match.get("predictedWeight")

                        set_estimated_scale_delay(match["delayMs"])

                        # Review hint (JS 591-594)
                        if IS_AUTO_ADJUSTED and match["delayMs"] >= s_interval * 2:
                            set_phase_delay_review_hint(match["delayMs"], "auto-delay")

                        # JS:605-613 — split match.delayMs into scale vs sensor
                        # bucket based on exit type. Only accumulated when
                        # IS_AUTO_ADJUSTED (always True in this port).
                        if IS_AUTO_ADJUSTED:
                            if exit_type in ("weight", "volumetric"):
                                sum_scale_delay += match["delayMs"]
                                count_scale_hits += 1
                            else:
                                sum_sensor_delay += match["delayMs"]
                                count_sensor_hits += 1

                        found_match = True

                        # Compute calculated values for ALL targets at matched delay
                        if match["delayMs"] > 0:
                            target_calc_values = {}
                            match_step = js_round(match["delayMs"] / s_interval)

                            for tgt in profile_targets:
                                is_wt = tgt.get("type") in ("volumetric", "weight")
                                if is_wt and not is_brew_by_weight:
                                    continue
                                # JS:624 — scale-lost check site #4
                                if is_wt and scale_connection_broken_permanently:
                                    continue

                                next_sample_idx = match_step - 1
                                t_type = tgt.get("type")
                                if (
                                    IS_AUTO_ADJUSTED
                                    and 0 <= next_sample_idx < len(next_phase_samples)
                                ):
                                    ns = next_phase_samples[next_sample_idx]
                                    horizon = match_step * s_interval_sec
                                    next_dt = (ns["t"] - anchor["t"]) / 1000.0
                                    if t_type == "pressure":
                                        anchor_val = anchor.get("cp", 0)
                                        next_val = ns.get("cp", 0)
                                        pred_val = max(
                                            0.0, anchor.get("cp", 0) + p_slope * horizon
                                        )
                                    elif t_type == "flow":
                                        anchor_val = _coerce_number(anchor.get("fl"))
                                        next_val = _coerce_number(ns.get("fl"))
                                        pred_val = max(
                                            0.0,
                                            _coerce_number(anchor.get("fl")) + f_slope * horizon,
                                        )
                                    elif is_wt:
                                        anchor_val = anchor.get("v", 0)
                                        next_val = ns.get("v", 0)
                                        pred_val = anchor.get("v", 0) + (
                                            w_rate * horizon if w_rate > 0 else 0
                                        )
                                    elif t_type == "pumped":
                                        anchor_val = anchor_pumped
                                        next_val = anchor_pumped + _coerce_number(
                                            ns.get("fl")
                                        ) * next_dt
                                        pred_val = anchor_pumped + max(
                                            0.0, _coerce_number(anchor.get("fl"))
                                        ) * horizon
                                    else:
                                        continue
                                    dir_valid = _is_directionally_valid_look_ahead(
                                        tgt.get("operator", ""), anchor_val, next_val
                                    )
                                    calc_val = next_val if dir_valid else pred_val
                                else:
                                    h = match["delayMs"] / 1000.0
                                    if t_type == "pressure":
                                        calc_val = max(
                                            0.0, anchor.get("cp", 0) + p_slope * h
                                        )
                                    elif t_type == "flow":
                                        calc_val = max(
                                            0.0,
                                            _coerce_number(anchor.get("fl")) + f_slope * h,
                                        )
                                    elif is_wt:
                                        calc_val = anchor.get("v", 0) + (
                                            w_rate * h if w_rate > 0 else 0
                                        )
                                    elif t_type == "pumped":
                                        calc_val = anchor_pumped + max(
                                            0.0, _coerce_number(anchor.get("fl"))
                                        ) * h
                                    else:
                                        continue

                                target_calc_values[t_type] = {
                                    "value": calc_val,
                                    "isStopReason": tgt is match["target"],
                                }

                    # --- FALLBACK: LAST PHASE SPECIAL LOGIC (JS 687-800) ---
                    if (
                        not found_match
                        and is_last_phase
                        and IS_AUTO_ADJUSTED
                        and is_brew_by_weight
                        # JS:691-692 — scale-lost fallback guard #1
                        and not scale_connection_broken_permanently
                    ):
                        weight_target = next(
                            (
                                t
                                for t in profile_targets
                                if t.get("type") in ("weight", "volumetric")
                            ),
                            None,
                        )

                        if weight_target:
                            final_sample = samples[-1]
                            final_w = final_sample.get("v", 0)
                            last_non_extended_index_fb = _get_last_non_extended_index(samples)
                            stop_sample = (
                                samples[last_non_extended_index_fb]
                                if last_non_extended_index_fb >= 0
                                else final_sample
                            )
                            stop_w = stop_sample.get("v", 0)

                            if (
                                stop_w
                                > weight_target["value"] + LAST_PHASE_OVERSHOOT_MAX_G
                            ):
                                # No weight-stop fallback when manually overshot.
                                pass
                            else:
                                current_rate = phase_weight_rate
                                overshoot = stop_w - weight_target["value"]
                                undershoot_at_end = weight_target["value"] - final_w
                                stop_instant_rate = _get_sample_instant_weight_rate(
                                    stop_sample
                                )

                                rate_candidates = [
                                    r
                                    for r in (current_rate, stop_instant_rate)
                                    if r is not None and math.isfinite(r) and r > 0.1
                                ]
                                conservative_rate = (
                                    min(rate_candidates) if rate_candidates else 0
                                )

                                stopped_above_target_in_range = (
                                    0 <= overshoot <= LAST_PHASE_OVERSHOOT_MAX_G
                                )

                                # Fallback A: stopped above target (JS 738-762)
                                if stopped_above_target_in_range and current_rate > 0.1:
                                    calculated_delay = max(
                                        0.0, (overshoot / current_rate) * 1000.0
                                    )
                                    if calculated_delay <= LAST_PHASE_ESTIMATED_DELAY_MAX_MS:
                                        set_estimated_scale_delay(calculated_delay)
                                        exit_reason = _format_stop_reason(
                                            weight_target["type"]
                                        )
                                        exit_type = weight_target["type"]
                                        final_predicted_weight = weight_target["value"]
                                        # JS:751-752 — fallback-overshoot delay
                                        # always accumulates into the scale bucket
                                        # (weight target only).
                                        sum_scale_delay += calculated_delay
                                        count_scale_hits += 1
                                        set_phase_delay_review_hint(
                                            calculated_delay, "fallback-overshoot"
                                        )

                                # Fallback B: finished below target (JS 766-797)
                                stopped_below_target_high_delay_candidate = (
                                    LAST_PHASE_UNDERSHOOT_MIN_G
                                    <= undershoot_at_end
                                    <= LAST_PHASE_UNDERSHOOT_MAX_G
                                )
                                if (
                                    not exit_type
                                    and stopped_below_target_high_delay_candidate
                                    and conservative_rate > 0.1
                                ):
                                    estimated_delay = (
                                        undershoot_at_end / conservative_rate
                                    ) * 1000.0
                                    if (
                                        estimated_delay > 2000
                                        and estimated_delay <= LAST_PHASE_ESTIMATED_DELAY_MAX_MS
                                    ):
                                        set_estimated_scale_delay(estimated_delay)
                                        exit_reason = _format_stop_reason(
                                            weight_target["type"]
                                        )
                                        exit_type = weight_target["type"]
                                        final_predicted_weight = weight_target["value"]
                                        # JS:781-782 — fallback-undershoot delay
                                        # also accumulates into the scale bucket.
                                        sum_scale_delay += estimated_delay
                                        count_scale_hits += 1
                                        set_phase_delay_review_hint(
                                            estimated_delay, "fallback-undershoot"
                                        )

                    # Independent high-delay warning detection (JS 802-835)
                    if (
                        is_last_phase
                        and is_brew_by_weight
                        # JS:804 — scale-lost fallback guard #2
                        and not scale_connection_broken_permanently
                    ):
                        weight_target = next(
                            (
                                t
                                for t in profile_targets
                                if t.get("type") in ("weight", "volumetric")
                            ),
                            None,
                        )
                        if weight_target:
                            final_sample = samples[-1]
                            final_w = final_sample.get("v", 0)
                            last_non_extended_index_hd = _get_last_non_extended_index(
                                samples
                            )
                            stop_sample = (
                                samples[last_non_extended_index_hd]
                                if last_non_extended_index_hd >= 0
                                else final_sample
                            )
                            stop_w = stop_sample.get("v", 0)
                            stop_instant_rate = _get_sample_instant_weight_rate(stop_sample)
                            rate_candidates = [
                                r
                                for r in (phase_weight_rate, stop_instant_rate)
                                if r is not None and math.isfinite(r) and r > 0.1
                            ]
                            conservative_rate = (
                                min(rate_candidates) if rate_candidates else 0
                            )
                            abs_delta = abs(final_w - weight_target["value"])

                            if (
                                stop_w <= weight_target["value"] + LAST_PHASE_OVERSHOOT_MAX_G
                                and conservative_rate > 0.1
                                and LAST_PHASE_UNDERSHOOT_MIN_G
                                <= abs_delta
                                <= LAST_PHASE_UNDERSHOOT_MAX_G
                            ):
                                estimated_delay = (abs_delta / conservative_rate) * 1000.0
                                if estimated_delay <= LAST_PHASE_ESTIMATED_DELAY_MAX_MS:
                                    set_estimated_scale_delay(estimated_delay)

        # --- PHASE METRICS (JS 840-845) ---
        p_water_pumped = 0.0
        for i in range(1, len(samples)):
            dt = (samples[i]["t"] - samples[i - 1]["t"]) / 1000.0
            p_water_pumped += _coerce_number(samples[i].get("fl")) * dt

        # --- ASSEMBLE PER-PHASE OUTPUT (JS 847-890) ---
        stats = {
            "p": _get_metric_stats(samples, "cp"),
            "tp": _get_metric_stats(samples, "tp"),
            "f": _get_metric_stats(samples, "fl"),
            "pf": _get_metric_stats(samples, "pf"),
            "tf": _get_metric_stats(samples, "tf"),
            "t": _get_metric_stats(samples, "ct"),
            "tt": _get_metric_stats(samples, "tt"),
            "w": _get_metric_stats(samples, "v"),
            "wf": _get_metric_stats(samples, "vf"),
            "sys_raw": sys_info.get("raw"),
            "sys_shot_vol": sys_info.get("shotStartedVolumetric"),
            "sys_curr_vol": sys_info.get("currentlyVolumetric"),
            "sys_scale": sys_info.get("bluetoothScaleConnected"),
            "sys_vol_avail": sys_info.get("volumetricAvailable"),
            "sys_ext": sys_info.get("extendedRecording"),
        }
        if sys_anomalies:
            stats["sys_anomalies"] = sys_anomalies

        phase_exit: PhaseExitReason = PhaseExitReason(
            exit_reason_type=(exit_type if exit_type else "unknown"),  # type: ignore[typeddict-item]
            unavailable_reason=None,
            number=str(phase_num),
            name=raw_name,
            displayName=display_name,
            start=p_start,
            end=p_end,
            duration=duration,
            water=p_water_pumped,
            weight=samples[-1].get("v", 0),
            stats=stats,
            exit={"reason": exit_reason, "type": exit_type},
            profilePhase=profile_phase,
            scaleLost=scale_lost_in_this_phase,
            scalePermanentlyLost=scale_connection_broken_permanently,
            highScaleDelay=phase_high_scale_delay,
            estimatedScaleDelayMs=phase_estimated_scale_delay_ms,
            delayReviewHint=phase_delay_review_hint,
            delayReviewReason=phase_delay_review_reason,
            delayReviewMs=phase_delay_review_ms,
            prediction={"finalWeight": final_predicted_weight},
            targetCalcValues=target_calc_values,
        )
        analyzed_phases.append(phase_exit)

    # JS:893-904 — derive average scale/sensor delays from accumulators.
    # ``Math.round(sum/count/50)*50`` rounds the per-hit average to the
    # nearest 50 ms bucket. When no hits accumulated under auto-adjust,
    # the JS source falls back to the manual-mode seed (line 894-895:
    # ``avgScaleDelay = scaleDelayMs``); the Python port surfaces that
    # gap as ``None`` instead, matching the AutoDelayEstimate contract
    # (``delay_ms: Optional[int]``) and Task 9's no-valid-estimate spec.
    avg_scale_delay: Optional[int] = (
        js_round(sum_scale_delay / count_scale_hits / 50) * 50
        if (IS_AUTO_ADJUSTED and count_scale_hits > 0)
        else None
    )
    avg_sensor_delay: Optional[int] = (
        js_round(sum_sensor_delay / count_sensor_hits / 50) * 50
        if (IS_AUTO_ADJUSTED and count_sensor_hits > 0)
        else None
    )

    return {
        "phases": analyzed_phases,
        "auto_delay_settings": {
            "scaleDelayMs": avg_scale_delay,
            "sensorDelayMs": avg_sensor_delay,
        },
    }


def classify_phase_exits(
    raw_shot: "ShotData",
    profile_snapshot: ProfileData,
) -> list[PhaseExitReason]:
    """Classify why each phase ended.

    Thin wrapper over :func:`_run_phase_analysis` that returns only the
    per-phase exit-reason list (the JS ``phases`` field of
    ``calculateShotMetrics`` output). The auto-delay average is computed
    in the same internal pass and exposed separately via
    :func:`estimate_auto_delay`.

    See ``_run_phase_analysis`` for the full algorithm port (JS lines
    208-991), helper composition, scale-lost-flag wiring, and constraints.
    """
    return _run_phase_analysis(raw_shot, profile_snapshot)["phases"]


def estimate_auto_delay(
    raw_shot: "ShotData",
    profile_snapshot: ProfileData,
    manual_delay_ms: Optional[int] = None,
) -> AutoDelayEstimate:
    """Estimate the auto scale-delay for a shot.

    Direct port of ``detectAutoDelay`` (``AnalyzerService.js`` v1.8.0
    lines 993-1006).

    When ``manual_delay_ms`` is provided, short-circuits without
    estimation and returns ``{"delay_ms": manual_delay_ms, "auto": False,
    "unavailable_reason": None}`` — Python-specific simplification of the
    JS contract (the JS source seeds calculateShotMetrics with
    ``manualDelay`` and still runs the optimization loop; the Python
    surface treats a configured manual delay as authoritative).

    Otherwise delegates to :func:`_run_phase_analysis` (sharing the
    Task 8a/8b helper composition via module scope, so neither
    ``classify_phase_exits`` nor this function re-runs the per-phase
    analysis when both are called) and returns the
    ``usedSettings.scaleDelayMs`` value as the auto-detected delay.
    ``delay_ms`` is an ``int`` (rounded to the nearest 50 ms by the
    internal helper) or ``None`` when no scale hits accumulated and
    therefore no estimate is available.
    """
    if manual_delay_ms is not None:
        return AutoDelayEstimate(
            delay_ms=manual_delay_ms,
            auto=False,
            unavailable_reason=None,
        )

    analysis = _run_phase_analysis(raw_shot, profile_snapshot)
    settings = analysis["auto_delay_settings"]
    scale_delay_ms = settings.get("scaleDelayMs")

    # ``_run_phase_analysis`` produces ``scaleDelayMs`` via ``js_round(...) * 50``
    # which is already a Python ``int``; coerce defensively (NaN/inf cannot
    # reach this branch — guarded by ``count_scale_hits > 0`` upstream) to
    # satisfy R17's strict-``int`` contract enforced by
    # test_analyze_shot_ddsa_response.py.
    if scale_delay_ms is None:
        delay_ms: Optional[int] = None
    elif isinstance(scale_delay_ms, int):
        delay_ms = scale_delay_ms
    else:
        delay_ms = js_round(scale_delay_ms)

    return AutoDelayEstimate(
        delay_ms=delay_ms,
        auto=True,
        unavailable_reason=None,
    )
