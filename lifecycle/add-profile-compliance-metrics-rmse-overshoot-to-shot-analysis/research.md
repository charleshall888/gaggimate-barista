# Research: Add Profile Compliance Metrics (RMSE + Overshoot) to Shot Analysis

## Codebase Analysis

### Where data lives and flows

The shot data pipeline is:

```
Gaggimate device → HTTP binary fetch
  → parsers/shot.py::parse_binary_shot() → ShotData
    → transformers/shot.py::transform_shot_for_ai() → TransformedShot
      → server.py::analyze_shot() → JSON response
        → /diagnose skill → interprets and presents
```

**Raw sample fields**: `tp` (target pressure), `cp` (current pressure), `tf` (target flow), `pf` (puck flow) are parsed directly from the binary `.slog` header via `FIELD_DEFS` in `parsers/shot.py`. They are scaled floats (`uint16 / 10` for pressure, `int16 / 100` for flow). Fields are sparse — they are only present in a sample dict if their bit is set in `fields_mask`.

**The critical gap**: `transformers/shot.py::select_representative_samples()` downsamples to `MAX_SAMPLES_PER_PHASE = 25` and builds `TransformedSample` TypedDicts that only include `pressure_bar`, `flow_ml_s`, etc. — `tp` and `tf` are dropped entirely. Compliance metrics must be computed **before** downsampling, against the raw sample list.

### Phase type identification problem

`ShotData.phases` is a list of `PhaseTransition` objects with `sample_index`, `phase_number`, and `phase_name` (string label from binary header, e.g. `"Gentle Fill"`, `"Bloom"`, `"Ramp"`). There is **no `phase_type` field** (`"preinfusion"`/`"brew"`/`"decline"`). The firmware writes only the human-readable name string.

To identify brew-phase samples, two approaches are viable:

| Approach | Pros | Cons |
|----------|------|------|
| 50%-of-peak heuristic | Already used in `calculate_summary()`; no external calls; synchronous | Imprecise at edges; doesn't account for bloom hold at low pressure |
| Fetch profile by `profile_id` | Exact phase type boundaries; uses profile's `phase` field | Async call; adds complexity to transformer; not all shots have a retrievable profile |

**Recommendation**: Use the 50%-of-peak heuristic (`cp >= peak_cp * 0.5`) as the "brew phase" proxy, consistent with the existing codebase convention. For a 7.5-bar bloom-slide profile this gives a threshold of ~3.75 bar — bloom samples (0 bar) and fill samples (2-2.5 bar) are naturally excluded. This is the fallback the backlog item explicitly endorses.

### Where to implement

Compliance metrics belong in `transformers/shot.py`. It is the only layer with access to the full raw sample list before downsampling. The transformer is synchronous; no profile fetch is needed if we use the heuristic.

Add a new `ComplianceMetrics` TypedDict and a `compute_compliance_metrics(shot: ShotData) -> Optional[ComplianceMetrics]` function. Add `compliance_metrics: Optional[ComplianceMetrics]` to `TransformedShot`. Call it from `transform_shot_for_ai()`.

### Affected files

| File | Change |
|------|--------|
| `mcp/src/gaggimate_mcp/transformers/shot.py` | New `ComplianceMetrics` TypedDict, `compute_compliance_metrics()` function, update `TransformedShot`, call from `transform_shot_for_ai()` |
| `mcp/tests/test_transformers_shot.py` | New tests for `compute_compliance_metrics()` |
| `.claude/skills/diagnose/SKILL.md` | Document how to read and surface the new metrics |

`server.py` and `parsers/shot.py` require **no changes** — the MCP tool already returns the full `TransformedShot` as JSON; adding `compliance_metrics` to that TypedDict is sufficient.

### Diagnose skill integration

The skill already fetches the profile definition via `manage_profile(action="get", profile_id=...)` for shot style classification. It should consume `compliance_metrics` from the `analyze_shot` response when present. The metrics provide a grind-direction signal that doesn't depend on taste description:
- `max_pressure_overshoot_bar > 1.5` → strong "grind too fine" signal
- `max_pressure_undershoot_bar > 1.5` (non-bloom, non-ramp context) → "grind too coarse" signal
- `pressure_rmse_bar` → overall profile adherence quality

### Existing test patterns

`test_transformers_shot.py` already tests `calculate_summary()`, `process_phases()`, `trim_trailing_artifacts()`, and `select_representative_samples()`. New tests should follow the same pattern: build a minimal `ShotData` with controlled samples, call `compute_compliance_metrics()`, assert output.

## Open Questions

1. **`tp`/`tf` sparseness**: If neither `tp` nor `tf` appears in a shot's `fields_mask` (e.g., older firmware), both pressure and flow metrics are `None`. Is this acceptable, or should the function log a warning? The spec says return `None` — this is fine.

2. **Incomplete shots**: The transformer already has `shot.incomplete` logic (skips trailing artifact trimming). Should compliance metrics be computed for incomplete shots? Recommendation: compute anyway — the user may still want RMSE for what was recorded. No special handling needed.

3. **Exact threshold for "brew phase"**: The 50%-of-peak heuristic is validated for bloom-slide profiles (7.5 bar peak → 3.75 bar threshold). For very low-pressure profiles (e.g., a 4-bar flow profile), peak may be low enough that the threshold becomes noisy. For now, accept this as a known limitation; exact phase-type filtering can be added later.

4. **Minimum sample count**: Spec says "at least 3 samples with a `tp` key before computing." This check is per metric — if brew-phase samples have <3 with `tp`, `pressure_rmse_bar` and overshoot fields should be `None`. Same for `tf` and `flow_rmse_ml_s`.
