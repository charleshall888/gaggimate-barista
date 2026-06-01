# Specification: Add Profile Compliance Metrics (RMSE + Overshoot) to Shot Analysis

## Problem Statement

The `/diagnose` skill currently infers grind direction from pressure curves and taste feedback. It lacks a direct, quantitative signal that compares what the machine actually did against what the profile asked it to do. A shot that consistently overshoots its target pressure by 2 bar is telling us the puck is too dense — without the user needing to describe the taste at all. Profile compliance metrics fill this gap: they give the skill a grind-direction signal derived purely from telemetry, reducing diagnostic ambiguity and enabling faster dialing-in.

## Requirements

1. **Compute `pressure_rmse_bar`** (RMSE of `cp - tp` across brew-phase samples): Acceptance — value is `None` when fewer than 3 brew-phase samples have a `tp` key; otherwise a non-negative float rounded to 2 decimal places.

2. **Compute `max_pressure_overshoot_bar`** (max of `cp - tp` across brew-phase samples, floored at 0): Acceptance — value is `None` under same sparseness condition; otherwise a non-negative float. A value > 1.5 bar is documented as a "grind too fine" signal.

3. **Compute `max_pressure_undershoot_bar`** (max of `tp - cp` across brew-phase samples, floored at 0): Acceptance — `None` or non-negative float. A value > 1.5 bar is documented as a "grind too coarse" signal (in non-bloom context).

4. **Compute `flow_rmse_ml_s`** (RMSE of `pf - tf` across brew-phase samples): Acceptance — `None` when fewer than 3 brew-phase samples have a `tf` key; otherwise a non-negative float rounded to 2 decimal places.

5. **Brew-phase filter**: Only brew-phase samples (those where `cp ≥ 50% of peak cp` across the full shot) are included in all metric computations. Acceptance — pre-infusion and bloom samples (low cp) are excluded; verified by unit test with a two-phase synthetic shot.

6. **None-guard**: If the total count of brew-phase samples with a `tp` key is fewer than 3, all pressure metrics are `None`. Same check for `tf` and flow metric independently. Acceptance — verified by unit test with 0, 1, 2, and 3 qualifying samples.

7. **`ComplianceMetrics` TypedDict**: A new `ComplianceMetrics` TypedDict is added to `transformers/shot.py` with the four metric fields plus `brew_phase_sample_count: int` (informational — number of samples that passed the 50% filter). Acceptance — TypedDict is importable and used in `TransformedShot`.

8. **`TransformedShot` updated**: `compliance_metrics: ComplianceMetrics` is added to the `TransformedShot` TypedDict (non-Optional — the function always returns a populated TypedDict). Acceptance — `analyze_shot` JSON response always includes a `compliance_metrics` object; individual metric fields within it may be `None` when data is absent.

9. **`/diagnose` skill updated**: `SKILL.md` documents the `compliance_metrics` fields, their thresholds (> 1.5 bar overshoot = grind too fine; > 1.5 bar undershoot = grind too coarse), and instructs the skill to surface them in the telemetry summary when non-None. Acceptance — skill file references the field names and thresholds explicitly.

10. **No regressions**: Existing `test_transformers_shot.py` tests continue to pass. `TransformedShot` is backward-compatible (new field is Optional, absent from existing test fixtures is acceptable).

## Non-Requirements

- **No profile fetch during computation.** Phase type identification uses the 50%-of-peak heuristic only. Fetching the profile definition to get exact `brew` phase boundaries is explicitly out of scope.
- **No changes to `parsers/shot.py` or `server.py`.** The metric computation is entirely within the transformer layer.
- **No numpy or scipy.** Pure Python math only (`math.sqrt`, list comprehensions). No new dependencies added.
- **No overshoot threshold enforcement.** The metrics are informational — the skill documents thresholds but does not enforce them as hard rules. Grind direction is a signal, not a command.
- **No separate metric for "undershoot in non-bloom context".** The bloom exclusion is handled by the 50%-of-peak filter. Undershoot is reported as a single value; context-specific interpretation is left to the skill layer.

## Edge Cases

- **Peak cp = 0** (degenerate/empty shot): No brew-phase samples exist; all metrics are `None`. `brew_phase_sample_count = 0`.
- **All samples below 50% threshold** (e.g., shot where pump never fully opened): Same as above — all `None`.
- **No `tp` in any sample** (older firmware without target pressure recording): `pressure_rmse_bar`, `max_pressure_overshoot_bar`, `max_pressure_undershoot_bar` all `None`. `flow_rmse_ml_s` may still be computed if `tf` is present.
- **`tf` absent, `tp` present** (pressure-targeted profile with no flow target): Flow metric is `None`; pressure metrics computed normally.
- **Incomplete shots** (truncated binary file): Metrics are computed on available brew-phase samples. No special handling — partial data is useful.
- **Negative overshoot/undershoot** (impossible by definition since we floor at 0): Not a runtime edge case but should be noted — `max(0, cp - tp)` ensures non-negative values.
- **Flush/cleaning shots** (no puck, open flow path): Peak cp will be very low (1-2 bar). The 50%-of-peak threshold will be correspondingly low, so most samples pass the brew-phase filter. With tp set to 7.5 bar but cp at ~2 bar, `max_pressure_undershoot_bar` will be large (~5+ bar). This is technically correct — the machine did deviate from its profile target — but diagnostically meaningless. Metrics are still computed; correct behavior is for `/diagnose` to only be invoked on real espresso shots.
- **Single-phase shots** (no `PhaseTransition` data, older V4 firmware): All samples are treated as the extraction. The 50%-of-peak filter still applies across the full sample list.

## Technical Constraints

- Implementation belongs in `mcp/src/gaggimate_mcp/transformers/shot.py` — the only layer with access to the raw sample list before downsampling.
- `select_representative_samples()` drops `tp`/`tf` from output; metrics must be computed before that step is called.
- The 50%-of-peak threshold (`cp ≥ peak_cp * 0.5`) is the project-standard heuristic for preinfusion/extraction boundary detection, already used in `calculate_summary()`.
- Tests must follow the pattern in `test_transformers_shot.py`: build a minimal `ShotData` with controlled samples, assert output. No file I/O in tests.

## Open Decisions

- None. All design choices resolved.
