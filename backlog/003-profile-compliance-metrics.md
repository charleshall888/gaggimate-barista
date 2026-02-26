---
title: Add profile compliance metrics (RMSE + overshoot) to shot analysis
status: open
priority: medium
type: feature
tags: [mcp, diagnostics, profiles]
created: 2026-02-26
updated: 2026-02-26
blocks: []
blocked-by: []
---

Compare actual pressure/flow against the profile's target values (`tp`/`tf` sample fields) and report:

| Metric | Meaning |
|--------|---------|
| `pressure_rmse_bar` | RMSE between actual and target pressure. Lower = machine followed profile better. |
| `max_pressure_overshoot_bar` | Largest single overshoot above target. > 1.5 bar is a strong grind-too-fine signal. |
| `max_pressure_undershoot_bar` | Largest single undershoot. > 1.5 bar in non-bloom context = grind too coarse. |
| `flow_rmse_ml_s` | Flow adherence (only when target flow data present). |

These metrics give the `/diagnose` skill a grind-direction signal that doesn't require the user to describe taste — the telemetry tells you directly whether the machine could push water through the puck.

### Critical lesson from upstream

**Scope to brew-phase samples only.** Computing RMSE over all samples (including pre-infusion/bloom) inflates the error and causes false-positive overshoot signals — during bloom phases, actual pressure is intentionally far below the brew-phase target. Filter to brew-phase samples before running the RMSE calculation.

We have explicit phase boundaries in our profiles, so filtering is straightforward. If phases aren't defined, use the 50%-of-peak fallback from the diagnostics module (#2).

### Only compute when target data is present

Check that at least 3 samples have a `tp` key before computing. If not, return `None` rather than zeros.
