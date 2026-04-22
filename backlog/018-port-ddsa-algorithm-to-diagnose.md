---
id: "018"
title: "Port DDSA / PhaseEndStop algorithm into /diagnose"
status: in_progress
priority: medium
type: feature
parent: "013"
blocked-by: []
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-21
complexity: complex
criticality: high
spec: lifecycle/port-ddsa-phaseendstop-algorithm-into-diagnose/spec.md
areas: [mcp,tests]
session_id: 9719c67c-3fec-441d-be9f-6e066b61edca
lifecycle_phase: review
---

# Port DDSA / PhaseEndStop algorithm into /diagnose

## What this delivers

`/diagnose` gains autonomous per-phase exit-reason classification (`weight | volumetric | pressure | flow | pumped | time`) and auto-delay estimation, producing output like "brew phase exited on volumetric at t+24.3s with estimated scale delay 1.2s" instead of the current generic stop-target summary. Also: each `/diagnose` response includes a deep-link to the native analyzer (formerly planned as standalone ticket 020, merged here since both changes modify the same skill's output).

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Decision Record DR-1, option (a). User chose the full port over the lighter deep-link alternative — explicit willingness to pay the effort + recurring maintenance tax for agent autonomy.

## Source of truth

- Algorithm source (JS): `web/src/pages/ShotAnalyzer/services/AnalyzerService.js` in Gaggimate repo at tag `v1.8.0`
  - ~1007 lines total; `calculateShotMetrics` alone ~700 lines
  - Support functions: `getRegressionWeightRate`, `getPhaseAnchorIndexForWeightRate`, `getPhaseWeightRate`, `getSampleInstantWeightRate`, `isDirectionallyValidLookAhead`, `getLastNonExtendedIndex`, `detectAutoDelay` (separate entry point)
  - Numerical constants: `LAST_PHASE_OVERSHOOT_MAX_G=4g`, `LAST_PHASE_UNDERSHOOT_MIN_G=2g`, `LAST_PHASE_UNDERSHOOT_MAX_G=6g`, `LAST_PHASE_ESTIMATED_DELAY_MAX_MS=4000ms`, `PREDICTIVE_WINDOW_MS` — all are in the JS source, not the English doc
  - Scale-lost-permanently flag propagation across phases
- English doc (partial): `web/src/pages/ShotAnalyzer/docs/PhaseEndStop_Algorithm_English.md` (44 lines — high-level overview only, omits numerical constants and edge cases)

## Implementation prerequisite: capture reference JS output

Before writing Python, establish how to produce machine-readable DDSA output from the JS reference for each fixture shot. Choose one and document the choice in the module PR:

- **(a) Browser-side export script**: add a one-off client-side helper that dumps `calculateShotMetrics(shot)` output as JSON via browser console; user runs it once per fixture shot and saves output next to the `.slog` as `<shot_id>.reference-js.json`. Low implementation cost, manual capture per fixture.
- **(b) Extract AnalyzerService.js into a Node.js harness**: run the pure functions directly in Node without the browser, pipe `.slog` data through. Higher setup, automatable.
- **(c) Instrument the device's analyzer page**: add a debug endpoint to the dev build that returns DDSA output as JSON. Highest firmware-side coupling.

(a) is recommended unless future ticket work needs continuous re-validation, in which case (b) is preferred.

## Acceptance criteria

### Python module

- Python module at `mcp/src/gaggimate_mcp/diagnostics/phase_end_stop.py` exposing:
  - `classify_phase_exits(transformed_shot) -> list[PhaseExitReason]`
  - `estimate_auto_delay(transformed_shot) -> AutoDelayEstimate`
- Module docstring cites exact firmware tag and source-file line range (e.g. `# Port of AnalyzerService.js lines 208–900 @ gaggimate v1.8.0`).

### Bit-compatibility check

- For each of 016's fixture shots, a reference-js JSON exists alongside (captured via the prerequisite above).
- A test `mcp/tests/test_phase_end_stop_parity.py` runs our Python implementation on each fixture and asserts output matches reference-js JSON with:
  - Exact match on categorical fields (`exit_reason_type`, `phase_number`).
  - `1e-3` absolute tolerance on floats (gram values, seconds, milliseconds).
  - Exact match on auto-delay classification buckets.
- If any fixture fails parity, the test fails — no "close enough" escape hatch.

### /diagnose integration

- `/diagnose` surfaces one exit-reason line per phase in its output.
- `/diagnose` surfaces one auto-delay-estimate line for the whole shot in its output.
- Every `/diagnose` response includes a trailing line: `Interactive chart: http://{GAGGIMATE_HOST}/analyze/{shot_id}` using the same env var MCP already reads. Shot_id formatting verified by opening one real shot via the URL during implementation and confirming it loads.

### Runbook

- Append to `research/gaggimate-1-8-0-upgrade/runbook.md` (create if needed): a section "Re-syncing DDSA on firmware upgrades" with exact steps — diff `AnalyzerService.js` at the new tag, refresh reference-js JSON for fixtures, re-run parity test, fix divergences.

## Dependencies

- 016 (regression harness) — hard block. Provides fixture shots + golden transformer output.

## Supersedes

- Old ticket 020 (deep-link to /analyze/{shot_id}) — merged here. Both changes modify `/diagnose` output and will land in the same PR.

## Risk notes

- L effort — algorithm is ~700 lines of dense numeric code
- Drift risk: every firmware minor release may move the algorithm; runbook step above documents re-sync procedure
- Fidelity risk: a lossy port produces different exit reasons than the device UI and undercuts the value proposition — tolerance is `1e-3`, not paraphrase
