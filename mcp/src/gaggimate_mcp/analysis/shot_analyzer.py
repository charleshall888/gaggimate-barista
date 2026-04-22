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
from typing import TypedDict, Literal, Optional


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
