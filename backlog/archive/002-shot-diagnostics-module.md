---
title: Add shot diagnostics module with physics-informed metrics
status: wontfix
priority: medium
type: feature
tags: [mcp, diagnostics, analysis]
created: 2026-02-26
updated: 2026-02-26
blocks: [3]
blocked-by: [1]
---

Add computed diagnostics to shot analysis — resistance, channeling indicators, and temperature stability — as a new `mcp/src/gaggimate_mcp/diagnostics.py` module (not in `shot.py`). Keep the transformer lean; let the diagnostics module do the physics.

### Metrics worth computing

**Puck resistance** — `R = P / F²` (Darcy model). The master diagnostic metric. Captures grind fineness, puck quality, channeling, and erosion. Report avg, std, slope, and peak timing.

**Channeling indicators** — pressure volatility (std-dev), flow volatility, max pressure drop rate, late-shot flow acceleration. Combine into a risk score: LOW / MODERATE / HIGH / VERY_HIGH.

**Temperature stability** — std-dev of brew-phase temperatures. Already have temp summary stats; this adds the stability angle.

### Key lessons from upstream PR #6 review

- **Trim ramp-up before computing channeling.** Pressure/flow instability during the initial ramp is normal pump behaviour, not channeling. Compute stability metrics only on steady-state samples (e.g. after pressure reaches 80% of target, or trim first 3-5 samples of brew phase).
- **Guard against empty resistance.** If all flow samples are ≤ 0.1 ml/s (choked/stalled shot), `resistance_values` will be empty. Return `null` with a `stalled_shot: true` flag rather than 0.0, which would be annotated as VERY_LOW — the opposite of the actual condition.
- **Only compute on brew-phase samples.** Use phase definitions (or the 50%-of-peak-pressure fallback) to exclude pre-infusion from resistance and channeling metrics.

### Architecture note

Keep this in `diagnostics.py`, not `shot.py`. The transformer's job is data shaping; the diagnostics module's job is metric computation and annotation. Our `shot.py` is 389 lines today — let's not grow it into a god-object.
