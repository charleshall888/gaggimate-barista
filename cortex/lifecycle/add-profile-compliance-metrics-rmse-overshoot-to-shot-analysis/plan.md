# Plan: Add Profile Compliance Metrics (RMSE + Overshoot) to Shot Analysis

## Overview

All changes live in the transformer layer (`transformers/shot.py` and its test file) plus a documentation update to the diagnose skill. The approach: add a `ComplianceMetrics` TypedDict, implement a `compute_compliance_metrics()` function that operates on raw samples before downsampling, wire it into `transform_shot_for_ai()`, then write tests and update the skill. `server.py` and `parsers/shot.py` are untouched.

## Tasks

### Task 1: Add `ComplianceMetrics` TypedDict and update `TransformedShot`

- **Files**: `mcp/src/gaggimate_mcp/transformers/shot.py`
- **What**: Define the `ComplianceMetrics` TypedDict with five fields and add `compliance_metrics: ComplianceMetrics` to `TransformedShot`. This is a pure data-structure change — no logic yet.
- **Depends on**: none
- **Context**:
  - `ComplianceMetrics` fields: `pressure_rmse_bar: Optional[float]`, `max_pressure_overshoot_bar: Optional[float]`, `max_pressure_undershoot_bar: Optional[float]`, `flow_rmse_ml_s: Optional[float]`, `brew_phase_sample_count: int`
  - Add it in the TypedDict block alongside `PressureSummary`, `FlowSummary`, etc. (lines ~14-52)
  - `TransformedShot` (lines ~77-86) gets one new non-Optional field: `compliance_metrics: ComplianceMetrics`. The function always returns a populated TypedDict; individual inner fields carry the `None` values when data is absent. This is consistent with how `ShotSummary` is always returned by `calculate_summary()`. `Optional` is already imported (needed for the inner fields).
  - Pattern to follow: all existing TypedDicts use `TypedDict` base class with annotated field types; match that style
- **Verification**: `from gaggimate_mcp.transformers.shot import ComplianceMetrics, TransformedShot` succeeds. `TransformedShot.__annotations__` includes `compliance_metrics`. No existing tests break.
- **Status**: [x] complete

---

### Task 2: Implement `compute_compliance_metrics()` and wire into `transform_shot_for_ai()`

- **Files**: `mcp/src/gaggimate_mcp/transformers/shot.py`
- **What**: Add a private `_get_brew_phase_samples()` filter helper and the public `compute_compliance_metrics()` function. Call `compute_compliance_metrics(shot)` inside `transform_shot_for_ai()` and include the result in the returned `TransformedShot`.
- **Depends on**: [1]
- **Context**:
  - **`_get_brew_phase_samples(samples: list[dict]) -> list[dict]`**: Finds `peak_cp = max(s.get('cp', 0.0) for s in samples)`. Returns all samples where `s.get('cp', 0.0) >= peak_cp * 0.5`. If `peak_cp == 0`, returns empty list.
  - **`compute_compliance_metrics(shot: ShotData) -> ComplianceMetrics`**: Always returns a populated `ComplianceMetrics` TypedDict — never returns `None`. Degenerate cases (empty sample list, zero peak pressure) produce a TypedDict with `brew_phase_sample_count=0` and all four metric fields `None`. Calls `_get_brew_phase_samples(shot.samples)`. Computes:
    - `brew_samples_with_tp` = [s for s in brew_samples if 'tp' in s]
    - If `len(brew_samples_with_tp) < 3`: pressure metrics are all `None`
    - Else: `pressure_rmse_bar` = sqrt(mean((s['cp'] - s['tp'])² for each sample)), rounded to 2 dp; `max_pressure_overshoot_bar` = max(0, s['cp'] - s['tp']) across all, rounded to 2 dp; `max_pressure_undershoot_bar` = max(0, s['tp'] - s['cp']) across all, rounded to 2 dp
    - Same None-guard for `tf`: `brew_samples_with_tf` = [s for s in brew_samples if 'tf' in s]; if <3, `flow_rmse_ml_s` is `None`; else RMSE of `pf - tf` rounded to 2 dp (use `s.get('pf', 0.0)` for puck flow)
    - `brew_phase_sample_count` = len(brew_samples) always
    - Returns `ComplianceMetrics(...)` — never returns `None` from the outer function (the TypedDict fields themselves may be `None`)
  - **`math.sqrt`** is already available (`from math import ceil`; add `sqrt` to the same import)
  - **`transform_shot_for_ai()`** (lines ~365-389): after `summary = calculate_summary(shot)` and `phases = process_phases(shot)`, add `compliance = compute_compliance_metrics(shot)`. Include `compliance_metrics=compliance` in the `TransformedShot(...)` constructor call.
  - Place the two new functions after `select_representative_samples()` and before `calculate_summary()` — logical grouping with other helper functions
- **Verification**: Instantiate a `ShotData` with 5 brew-phase samples (cp=7.0, tp=7.5) and 2 preinfusion samples (cp=1.0, tp=2.0) in a Python REPL or quick script. Call `compute_compliance_metrics(shot)`. Confirm: `brew_phase_sample_count=5`, `max_pressure_undershoot_bar≈0.5`, `max_pressure_overshoot_bar=0.0`, `pressure_rmse_bar≈0.5`. Confirm `transform_shot_for_ai(shot)` includes `compliance_metrics` key in output dict.
- **Status**: [x] complete

---

### Task 3: Write unit tests for `compute_compliance_metrics()`

- **Files**: `mcp/tests/test_transformers_shot.py`
- **What**: Add a `TestComputeComplianceMetrics` test class covering the happy path, the None-guards, the brew-phase filter, and the known edge cases from the spec.
- **Depends on**: [2]
- **Context**:
  - Import `compute_compliance_metrics` from `gaggimate_mcp.transformers.shot` alongside existing imports
  - Build `ShotData` fixtures using the `ShotData` dataclass directly (see how existing tests construct them — no file I/O)
  - Required test cases:
    1. **Happy path**: 5 brew-phase samples with `tp` and `tf`, 2 preinfusion samples without. Confirm all 4 metrics non-None and mathematically correct. Confirm `brew_phase_sample_count=5`.
    2. **Sparse tp (<3 qualifying)**: 2 brew-phase samples with `tp`. Confirm `pressure_rmse_bar`, overshoot, undershoot all `None`. `flow_rmse_ml_s` may still compute if `tf` present.
    3. **No tp at all**: brew-phase samples with no `tp` key. All pressure metrics `None`.
    4. **No tf**: brew-phase samples have `tp` but no `tf`. `flow_rmse_ml_s` is `None`; pressure metrics computed normally.
    5. **Zero peak cp**: all samples have `cp=0.0`. `brew_phase_sample_count=0`, all metrics `None`.
    6. **Brew-phase filter works**: mix of 3 samples at cp=0.5 bar (bloom) and 5 samples at cp=7.5 bar (brew), peak=7.5 bar, threshold=3.75 bar. Confirm only the 5 high-pressure samples are used for metrics.
    7. **Flush/cleaning shot**: all samples have cp≈2.0, tp≈7.5 (profile target far above actual). Confirm `max_pressure_undershoot_bar≈5.5`. No crash.
  - Pattern: each test builds a minimal `ShotData` with only the fields needed; follow `TestCalculateSummary` and `TestTrimTrailingArtifacts` in the same file for the minimal-fixture style
- **Verification**: `cd mcp && python -m pytest tests/test_transformers_shot.py -v` — all tests pass including the new `TestComputeComplianceMetrics` class. No existing test failures.
- **Status**: [x] complete

---

### Task 4: Update `/diagnose` SKILL.md with compliance metrics documentation

- **Files**: `.claude/skills/diagnose/SKILL.md`
- **What**: Document the `compliance_metrics` field in the existing "COMPARE Intended vs Actual" section (§2b), explaining what each metric means and when to surface it in diagnosis.
- **Depends on**: [2]
- **Context**:
  - Target location: §2b (lines ~111-126 in SKILL.md) — already covers "compare each phase's intended parameters against actual telemetry." The compliance metrics fit naturally here.
  - Add a new paragraph after the existing comparison table explaining: when `analyze_shot` returns `compliance_metrics`, use it as a quantitative grind-direction signal alongside the manual phase-by-phase comparison. Thresholds to document:
    - `max_pressure_overshoot_bar > 1.5` → strong "grind too fine" signal (puck resisting flow, machine building pressure above target). Same threshold already present in the universal thresholds table for manual pressure spike detection — this metric makes it automatic.
    - `max_pressure_undershoot_bar > 1.5` → "grind too coarse" signal — **but only when the profile is at steady-state brew pressure**. Do NOT flag during post-bloom ramp phases (ease-in from 0 bar): ramp transitions naturally produce large undershoot values as the machine climbs from 0 to target pressure. Cross-reference with shot style (Bloom profiles always have a ramp). The existing §2b text on post-bloom ramps already covers this nuance — reference it rather than duplicating it.
    - `pressure_rmse_bar`: surface as an overall adherence quality note when non-None. Do not attach a specific threshold — we have no calibrated data yet on what constitutes "good" RMSE for this machine and these profiles. Describe it as: lower is better; a value materially higher than 1 bar is worth noting.
    - `flow_rmse_ml_s`: surface when non-None as informational context only. No specific threshold — flag for future calibration once real shot data is available.
  - Also note: `brew_phase_sample_count` is available if needed for confidence context (e.g., a count of 3-4 suggests metrics are based on very few samples and should be weighted accordingly).
  - Keep the update tightly scoped to §2b — do not restructure the skill or add new sections.
- **Verification**: Read the updated SKILL.md. Confirm the compliance_metrics paragraph is present in §2b and references all four metric field names, the 1.5 bar overshoot/undershoot threshold, the ramp-context caveat for undershoot, and the "no threshold yet" note for RMSE fields. No other sections changed.
- **Status**: [x] complete

---

## Verification Strategy

After all tasks complete:
1. Run the full test suite: `cd mcp && python -m pytest tests/ -v`. All tests pass.
2. Fetch a recent real shot via `analyze_shot(shot_id)` in the MCP tool. Confirm the JSON response includes a `compliance_metrics` key. If the shot used a profile with `tp` data, confirm non-None values. If older firmware without `tp`, confirm `None` values with `brew_phase_sample_count` still present.
3. Invoke `/diagnose` on the same shot and confirm the compliance metrics are referenced in the diagnosis output.
