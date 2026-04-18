---
id: "018"
title: "Port DDSA / PhaseEndStop algorithm into /diagnose"
status: open
priority: medium
type: feature
parent: "013"
blocked-by: ["016"]
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-18
---

# Port DDSA / PhaseEndStop algorithm into /diagnose

## What this delivers

`/diagnose` gains autonomous per-phase exit-reason classification (`weight | volumetric | pressure | flow | pumped | time`) and auto-delay estimation, producing output like "brew phase exited on volumetric at t+24.3s with estimated scale delay 1.2s" instead of the current generic stop-target summary.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Decision Record DR-1 (revised), option (a). User chose the full port over the lighter deep-link alternative — explicit willingness to pay the effort + recurring maintenance tax for agent autonomy.

## Source of truth

- Algorithm source (JS): `web/src/pages/ShotAnalyzer/services/AnalyzerService.js` in Gaggimate repo at tag `v1.8.0`
  - ~1007 lines total; `calculateShotMetrics` alone ~700 lines
  - Support functions: `getRegressionWeightRate`, `getPhaseAnchorIndexForWeightRate`, `getPhaseWeightRate`, `getSampleInstantWeightRate`, `isDirectionallyValidLookAhead`, `getLastNonExtendedIndex`, `detectAutoDelay` (separate entry point)
  - Numerical constants: `LAST_PHASE_OVERSHOOT_MAX_G=4g`, `LAST_PHASE_UNDERSHOOT_MIN_G=2g`, `LAST_PHASE_UNDERSHOOT_MAX_G=6g`, `LAST_PHASE_ESTIMATED_DELAY_MAX_MS=4000ms`, `PREDICTIVE_WINDOW_MS` — all are in the JS source, not the English doc
  - Scale-lost-permanently flag propagation across phases
- English doc (partial): `web/src/pages/ShotAnalyzer/docs/PhaseEndStop_Algorithm_English.md` (44 lines — high-level overview only, omits numerical constants and edge cases)

## Acceptance criteria

- Python module (e.g. `mcp/src/gaggimate_mcp/diagnostics/phase_end_stop.py`) exposing a function that takes a transformed shot and returns per-phase exit-reason + auto-delay metadata
- Bit-compatibility check: for each fixture shot from 016, our Python output matches the reference JS output (captured by loading the same shot into the web analyzer and recording its output)
- `/diagnose` skill updated to surface exit-reason language in its output
- Firmware-version citation in the module docstring (e.g. `# Port of AnalyzerService.js @ gaggimate v1.8.0`) so a future reader knows when to re-validate
- A runbook line in research/gaggimate-1-8-0-upgrade/ noting: "re-sync this module on each upstream minor release; diff against `analyzerUtils.js` and `AnalyzerService.js` at the new tag"

## Dependencies

- 016 (regression harness) must land first so we can validate bit-compatibility against fixtures without ad-hoc manual comparison

## Risk notes

- L effort — algorithm is dense numeric code
- Drift risk: every firmware minor release may move the algorithm; document re-sync procedure
- Fidelity risk: a lossy port produces different exit reasons than the device UI and undercuts the value proposition — aim for numerical parity, not paraphrase
