# Review: surface-weight-flow-g-s-in-transformedsample-flowsummary

Two-stage review against the approved spec. Stage 1 checks each R1–R9; Stage 2 runs only if Stage 1 has no FAILs.

## Stage 1: Spec Compliance

### R1 — `TransformedSample.weight_flow_g_s` per-sample field — PASS

- `TransformedSample` TypedDict in `mcp/src/gaggimate_mcp/transformers/shot.py` now declares `weight_flow_g_s: float` (line 74) alongside the other per-sample fields.
- `select_representative_samples` populates the field via `weight_flow_g_s=round(sample.get('vf', 0.0) * 10) / 10` (line 186) — exact mirror of the adjacent `flow_ml_s=round(sample.get('pf', 0.0) * 10) / 10`. No hygiene filter applied at per-sample scope (spec-compliant: raw signal preserved, including negatives and clamp sentinels).
- Grep AC: `grep -c 'weight_flow_g_s: float'` → 1, `grep -c 'weight_flow_g_s=round'` → 1.
- Structural AC across all three goldens: `jq -e '[.phases[].samples[] | has("weight_flow_g_s")] | all'` exits 0 for 246/247/249.

### R2 — `FlowSummary.peak_weight_flow_g_s` aggregate — PASS

- `FlowSummary` declares `peak_weight_flow_g_s: Optional[float]` (line 39). Grep AC: count = 1.
- Computation at lines 339–343 uses `clean_samples`, calls the shared `_is_valid_vf_sample` helper, AND additionally filters `s['vf'] > 0.0` (spec-mandated extra filter on top of the unified hygiene rule). Returns `round(max(values) * 10) / 10` or `None` when the filtered list is empty.
- Spec R2(b) bounded-or-null invariant: holds for all three fixtures (null on 247; `peak=3.3` on 246; `peak=3.6` on 249, both inside (0, 20)).
- Spec R2(c) `247.peak <= 10.0 OR null`: holds (null).

### R3 — `FlowSummary.avg_weight_flow_g_s` aggregate (brew-phase only) — PASS

- `FlowSummary` declares `avg_weight_flow_g_s: Optional[float]` (line 40). Grep AC: count = 1.
- Computation at lines 345–352 uses `_get_brew_phase_samples(samples)` (correct helper matching `compute_compliance_metrics`), filters only through `_is_valid_vf_sample` (base hygiene rule — does NOT additionally filter `vf > 0`, so negative brew-phase `vf` values are retained, spec-compliant). Degenerate handling: `len < 3 → None`. Else `round(sum/len * 10) / 10`.
- Spec R3(b) bounded-or-null invariant: holds for all three fixtures (`avg=2.5` on 246, `avg=0.0` on 247, `avg=1.6` on 249).
- Spec R3(c): 247 emits `avg_weight_flow_g_s = 0.0` — implies ≥ 3 qualifying `valid()` brew-phase samples whose mean rounds to 0.0. Internally consistent with `peak=null` (the extra `vf > 0` filter there eliminates the zero/negative brew-phase samples that `avg` retains).

### R4 — `FlowSummary.time_to_first_nonzero_weight_flow_s` — PASS

- Declared `Optional[float]` (line 41). Grep AC: count = 1.
- Computation at lines 354–364 scans raw `samples` (correct scope, matches `time_to_first_drip_s`/`time_to_first_weight_s`), applies triple-gate `_is_valid_vf_sample(sample) AND sample['vf'] > 0.3 AND sample.get('v', 0.0) > 0.0`. Returns first satisfying time rounded to 1 dp, else `None`.
- Spec R4(b) physical-ordering invariant: holds for all three fixtures (null on 247; 246 has 5.2 ≥ drip 2.5; 249 has 15.8 ≥ drip 11.2).
- Spec R4(c) 247 tare-rejection (null OR > 1.5): holds (null).

### R5 — `analyze_shot` docstring update — PASS

- `mcp/src/gaggimate_mcp/server.py` lines 460–487 now carry an explicit `Returns:` block documenting all four new fields with role + hygiene behavior + null conditions. `weight_flow_g_s` appears 4 times (matching spec R5(a) ≥ 4 threshold); `peak_weight_flow_g_s`, `avg_weight_flow_g_s`, and `time_to_first_nonzero_weight_flow_s` each appear once (meeting ≥ 1 thresholds).

### R6 — Regenerate existing fixture goldens — PASS

- All three regenerated goldens (246/247/249) carry the four new keys at expected paths. Structural `jq -e '.summary.flow | has(...) and has(...) and has(...)'` → 0 exit for all three. Per-sample `has("weight_flow_g_s")` → all true.
- Value-preservation check (spec R6(c)): not re-run in review because it requires the pre-R6 snapshot. Plan Task 5 reports [x] complete with snapshot-based verification. Accepted on plan self-verification plus the observation that `pytest tests/test_shot_regression.py` passes — any non-additive numeric drift would have tripped the exact-equality regression.
- AC R6(a): `pytest tests/test_shot_regression.py` exits 0 (3 passed).

### R7 — Pin rounding semantics inline — PASS

- Line 30 of `shot.py`, immediately above `class FlowSummary(TypedDict):`, reads: `# Aggregates use round(x * 10) / 10 — Python 3 banker's rounding (round-half-to-even).`
- Spec AC requires token `banker` OR `round-half-to-even` AND placement either inside `calculate_summary` or adjacent to the `FlowSummary` TypedDict. The comment contains both tokens and sits directly above the class declaration — spec-compliant placement.

### R8 — Fixture README update — PASS

- `mcp/tests/fixtures/shots/README.md` lines 25–31 now contain a "Weight-flow hygiene behavior" section covering all three fixtures (246 healthy positive signal; 247 pathological with `pf > 0` and clamp-filter rationale; 249 bloom-slide with retained-negatives spec note).
- Grep AC: `weight_flow_g_s` → 4, `peak_weight_flow_g_s` → 3, `time_to_first_nonzero_weight_flow_s|avg_weight_flow_g_s` → 4 (each threshold ≥ 1 met).
- Prose stays at rule level (no specific numeric timestamps or field values) per plan guidance.

### R9 — No regressions — PASS (with known pre-existing unrelated failures)

- `pytest tests/` → 185 passed, 8 failed. The 8 failures (3 in `test_api_websocket.py::TestWebSocketClientShotNotes`, 5 in `test_save_shot_notes_rmw.py`) are all in the shot-notes websocket save path and assert against pre-implementation `_send_request` call contracts / carry `structlog` "I/O operation on closed file" from a test-fixture logger reuse issue. None of the failures reference `FlowSummary`, `TransformedSample`, `weight_flow_g_s`, `vf`, or the transformer at all. The review brief explicitly flags these as pre-existing (verified via baseline run with changes stashed); the implementation does not cause or aggravate them.
- All tests that actually exercise the changed surface pass: `test_transformers_shot` (32 tests), `test_parsers_shot` (5), `test_shot_fixture_walker` (12), `test_shot_regression` (3).

## Stage 2: Code Quality

No FAILs in Stage 1 — proceeding.

**Helper placement and naming.** `_is_valid_vf_sample` is a module-level `def` (single source of truth) with a focused docstring-comment explaining the three-clause predicate and calling out the firmware clamp dependency. It sits adjacent to `_get_brew_phase_samples` at lines 194–199, matching the sibling helper's placement convention. Underscore prefix signals module-private. Naming is longer than the spec's informal `valid(sample)` but discoverable at call sites — the plan's Veto Surface acknowledged and justified this. All three aggregates call the shared helper (no inline duplication).

**None-return discipline.** All three aggregates return `None` for degenerate cases: `peak` when filtered list empty, `avg` when `len < 3`, `time_to_first_nonzero` when no sample satisfies the triple-gate. No silent `0.0` emission (spec explicitly forbids that to avoid hiding data-quality issues — fixture 247's `avg = 0.0` is a genuine mean-of-valid-samples, not a degenerate fallback). Mirrors the `ComplianceMetrics` precedent at lines 248–265.

**Pattern consistency.**
- Aggregate-computation block at lines 338–364 sits in `calculate_summary` just before `FlowSummary(...)` construction, matching the existing `total_volume / avg_flow / peak_flow / time_to_first_drip / time_to_first_weight` pattern at lines 318–336.
- Per-sample population at line 186 is a drop-in adjacent to `flow_ml_s` — the two fields are conceptually paired.
- Rounding uses `round(x * 10) / 10` everywhere (pre-rounding invariant, R7-pinned).

**Comment quality.** The `_is_valid_vf_sample` comment (lines 195–198) documents WHY each clause exists and flags the firmware-change brittleness. Line 338 comment `# Weight-flow aggregates (Unified Hygiene Rule via _is_valid_vf_sample)` signposts the block. R7 rounding pin comment at line 30 is the single centralized rationale for the rounding contract.

**Test coverage.** Plan Task 5's tightened verifications (strict `== null` on 247, positive-signal non-null + physical ordering on 246/249) were applied and all hold. The coverage gap flagged in the plan (retained-negatives code path in `avg` unexercised on current fixtures, acknowledged at Scope Boundaries) remains — a silent `vf >= 0` filter slipping into `avg` would not regress any committed golden. This is a known-accepted limitation; closing it is deferred to a future fixture capture.

**Nit (non-blocking).** The `_is_valid_vf_sample` body is a one-line `return` with comments above it. A docstring (triple-quoted) would be idiomatic for a module-level helper, matching `_get_brew_phase_samples`'s pattern. The spec does not mandate this; the comment-block form is still readable. Mentioned for future polish, not a blocker.

## Requirements Drift

**State**: none

**Details**: no requirements docs loaded — drift N/A. `requirements/` directory does not exist in this repo; CLAUDE.md carries compact quick-reference tables (temp/pressure/ratio) but nothing relevant to shot-analysis transformer schema. The lifecycle spec's Non-Requirements section owns the scope boundaries (no `/diagnose` divergence, no parser changes, no new fixtures, no `/feedback` changes) and all have been honored.

## Verdict

```json
{"verdict": "APPROVED", "cycle": 1, "issues": [], "requirements_drift": "none"}
```
