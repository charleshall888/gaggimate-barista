# Research: Surface `weight_flow_g_s` in TransformedSample + FlowSummary

## Epic Reference

Parent epic: [`research/gaggimate-1-8-0-upgrade/research.md`](../../research/gaggimate-1-8-0-upgrade/research.md), Decision Record **DR-4**. The epic covers the full firmware 1.8.0 adaptation (tickets 013–021); this ticket is scoped narrowly to (a) surfacing an already-parsed per-sample `vf` field through the `analyze_shot` transformer layer, (b) adding three `FlowSummary` aggregates, (c) optionally surfacing a `/diagnose` divergence diagnostic line, and (d) locking transformer outputs with 016's fixture harness. Broader 1.8.0 concerns (DDSA port, drift verification) belong to tickets 018 and 021.

---

## Codebase Analysis

### Files that will change

1. **`mcp/src/gaggimate_mcp/transformers/shot.py`** (primary)
   - `FlowSummary` TypedDict (~lines 30–37): add `peak_weight_flow_g_s`, `avg_weight_flow_g_s`, `time_to_first_nonzero_weight_flow_s`.
   - `TransformedSample` TypedDict (~lines 63–71): add `weight_flow_g_s`.
   - `select_representative_samples()` (~lines 150–184): include `weight_flow_g_s` in the per-sample dict, sourced from parser `vf`.
   - `calculate_summary()` (~lines 261–356): compute the three weight-flow aggregates; mirror the existing `peak_flow_ml_s` / `avg_flow_ml_s` / `time_to_first_drip_s` pattern.
2. **`mcp/src/gaggimate_mcp/server.py`** (~lines 458–510): update the `analyze_shot` docstring to document the four new fields.
3. **`mcp/tests/fixtures/shots/<shot_id>.golden.json`** (3 files from 016): regenerate via `refresh_fixtures.py` so goldens include the new fields in `summary.flow` and every `phases[*].samples[*]`.
4. **`.claude/skills/diagnose/SKILL.md`**: conditional — only if the `/diagnose` divergence line remains in scope after the Open Questions below are resolved.
5. **No parser change.** `parsers/shot.py` already maps `'VF': 8` (line 33) and defines the `FieldDef` (~line 64) with `FLOW_SCALE=100`.

### Relevant existing patterns

- **Derived, unit-converted per-sample fields.** Every `TransformedSample` field is derived from a raw parser field (`ct → temperature_c`, `cp → pressure_bar`, `pf → flow_ml_s`, `v → weight_g`, `pr → resistance`). `weight_flow_g_s` fits this convention; surfacing raw `vf` would break it.
- **Pre-rounded aggregates (1 d.p.).** `peak_flow_ml_s = round(max(flows) * 10) / 10`. Same pattern applies to the weight-flow aggregates — this preserves golden byte-stability per 016 R3.
- **Presence-guarded aggregation.** `flow_ml_s` aggregation uses `[s['pf'] for s in clean_samples if 'pf' in s]` (~lines 276–280, 302–304). The `'vf' in s` guard must be replicated — `sample.get('vf', 0.0)` conflates "field absent" with "zero," and the parser only emits `vf` when bit 8 of `fields_mask` is set.
- **Sparsity → `None`.** Compliance metrics precedent (same file, ~lines 212–258) returns `None` for each metric when fewer than N qualifying samples exist, rather than emitting `0.0`. Mirror this: aggregates must return `None` (and `peak_*` / `avg_*` must allow `Optional[float]`) when no qualifying samples exist.
- **Brew-phase filter.** `ComplianceMetrics` computes over samples where `cp ≥ 50% of peak cp` (compliance R5 from the profile-compliance lifecycle). This pattern may apply to `avg_weight_flow_g_s` to avoid averaging over bloom/idle samples, but **not** to `peak_weight_flow_g_s` or `time_to_first_nonzero_weight_flow_s` (both of which are shot-wide signals by definition).

### Integration points and dependencies

- **`analyze_shot` tool** (`server.py` ~lines 458–510): returns the full `TransformedShot` as serialized JSON. Additive field changes propagate automatically — no tool-registration change. Docstring update is the only server-side edit.
- **`/diagnose` skill** (`.claude/skills/diagnose/SKILL.md`): calls `analyze_shot`, reads `summary.flow.*` and `phases[*].samples[*]`, and renders a Telemetry Summary prose block. If a divergence line ships from 015, it lives in this skill's Telemetry Summary section (not in the transformer).
- **`/feedback` skill** (`.claude/skills/feedback/SKILL.md`): does **not** consume `FlowSummary` today; calls `manage_shot_notes`. Adding fields is non-breaking.
- **016 fixture harness** (`mcp/tests/test_shot_regression.py`, `mcp/src/gaggimate_mcp/tools/shot_fixture_walker.py`, `mcp/src/gaggimate_mcp/tools/refresh_fixtures.py`): exact-equality deep-equality walker with field-path assertions; byte-stable JSON via `sort_keys=True, indent=2, trailing newline`. Additive fields require regeneration; all three committed fixtures sort keys alphabetically so new keys interleave with existing ones.
- **Token budget / `analyze_shot` size.** Current per-fixture JSON size is 10–14 KB. Adding `weight_flow_g_s` to every per-sample row (~52–58 samples per shot) adds roughly 1.2 KB, ~9% bloat. This is within the envelope but should be noted for backlog 001 (three-level detail param) sizing.

### Conventions to follow

- `TypedDict`-based TransformedShot (not Pydantic) — additive fields are safe.
- Field naming: `weight_flow_g_s`, `peak_weight_flow_g_s`, `avg_weight_flow_g_s`, `time_to_first_nonzero_weight_flow_s`.
- Type annotations: aggregates are `Optional[float]` (allow `None` under sparsity); per-sample `weight_flow_g_s` is `float`.
- Rounding: Python 3 `round()` (banker's rounding) via `round(x * 10) / 10`. Pin this in a code comment adjacent to the new fields — future Python rounding-mode changes would silently break goldens otherwise.
- Test style: parametrized pytest + deep-equality walker from 016. No new unit-test file required.
- Golden regeneration: `python -m gaggimate_mcp.tools.refresh_fixtures <shot_id>` per fixture.

### Key open codebase questions (for implementation / spec)

- Does the `/diagnose` SKILL.md currently render a flow section, and where does a divergence line belong (inline, new subsection, conditional)?
- Where in `calculate_summary()` are the brew-phase helpers (`_get_brew_phase_samples` or equivalent)? This is the hook for the optional `avg_weight_flow_g_s` brew-phase filter.

---

## Web Research

### Channeling detection via flow/weight divergence

**No single canonical numeric threshold for pump-flow vs weight-flow divergence surfaced in public prior art.** Key findings:

- **Decent DE1's pump model** is considered more accurate than any flow meter for pump-side flow ("can notice very quick transitions such as a channel opening and closing"). Decent's shot analysis community has moved toward **puck-state metrics** — resistance, conductance, conductance derivative — rather than raw pump-vs-weight divergence. ([Decent flow calibration](https://decentespresso.com/blog/perfectly_calibrating_decent_flow_measurements))
- **Visualizer.coffee** implements three puck-integrity curves — puck resistance, puck conductance, and conductance derivative. "The derivative of conductance helps identify transient defects in the puck, such as quick channels that heal." No numeric threshold published. ([Visualizer blog](https://decentespresso.com/blog/httpvisualizercoffee_is_amazing))
- **Damian Brakel's tools** (DSx skin, BT-scale adapter, eWDT, D-Flow) do **not** contain a shot-score channeling detector. The "Damian's shot score" folklore conflates Brakel's UI work with community puck-integrity work.
- **Community rule of thumb**: channeling shows as a "sudden spike around 10 s" in flow, qualitative only.
- **Robert McKeon Aloe's "Post-Shot Quality Metrics"** concludes that measured post-shot metrics "don't correlate well for taste" — no predictive threshold. ([Medium](https://medium.com/data-science/post-shot-quality-metrics-for-espresso-78ca525f0215))

### Gaggimate firmware's own analyzer

The firmware **already separates** pump-side flow and drip-side flow internally:

- `lib/NayrodPID/src/PressureController/PressureController.cpp` tracks `_waterThroughPuckFlowRate` and `_coffeeFlowRate` separately, computes `_puckConductance = waterThroughPuck / sqrt(pressure)` and its derivative.
- A **puck state machine** with hard-coded derivative thresholds (−0.5, −0.1) is used internally for pre-infusion regulation. **Not** a barista-facing channeling detector.
- The 1.8.0 Shot Analyzer UI (PR #585, #602) and DDSA system (PR #606, #630 — the subject of ticket 018) are phase/exit-reason engines. **No `channel` / `divergence` / `lag` token appears in `AnalyzerService.js`.** There is no native analyzer "divergence threshold" to port.

### BT scale noise floor references

- **Resolution**: 0.1 g typical (Acaia Lunar, Bookoo Themis, Felicita Arc).
- **Flow-rate measurement floor**: Acaia Lunar spec 0.1 – 3.4 g/s.
- **Zero drift**: Acaia's manual recommends 2-display-unit (±0.2 g) zero-indication correction.
- **Practical weight-flow detection floor**: ~0.3 g/s given 0.1 g resolution and 3–5 Hz BT update. Below this, differentiating scale readings yields numerical noise.
- CLAUDE.md already records: "spikes, drops to 0 g, or null readings near end-of-shot."

### Pump-flow vs weight-flow physics (mass balance)

Five factors drive legitimate pump-vs-weight divergence that is **not** channeling:

1. **Puck saturation** (first 3–8 g of pumped water absorbs into dry puck before first drip).
2. **Dead volume** (shower screen + group head + portafilter path).
3. **Crema / emulsion** (crema density ~0.3–0.5 g/mL; pump over-reads weight during high-crema phases by ~15%).
4. **Droplet formation** (stair-step scale readings vs smooth pump flow at shot start/end).
5. **Vibe pump non-linearity** (pump output drops from 650 ml/min free-flow to ~260 ml/min at 9 bar).

Gaggimate's `PressureController.cpp` accounts for 1–3 via the `C·dP/dt = pumpFlow − puckFlow` compliance model.

### Threshold proposal (no canonical source)

If a divergence line is shipped despite the findings above, a **defensible but non-authoritative** starting proposal:

- **Noise floor**: `weight_flow_g_s ≥ 0.3 g/s` before values are considered signal.
- **Saturation mask**: ignore divergence until `cup_weight_g ≥ 0.5 g`.
- **Divergence criterion**: `pump_flow − weight_flow > 1.0 g/s` sustained ≥ 2 s during main extraction.
- **Crema allowance**: expect `weight_flow ≈ 0.85 × pump_flow` at steady state.
- **Better alternative**: extend Gaggimate's puck-conductance-derivative signal (already produced by firmware via PR and BR fields) with a barista-visible flag, matching Visualizer's approach. This is the path 018 (DDSA port) implicitly opens.

### Relevant links

- https://github.com/jniebuhr/gaggimate — firmware repo; `PressureController.cpp` (puck-state estimator), `AnalyzerService.js` (phase/exit-reason engine)
- https://github.com/jniebuhr/gaggimate/releases — 1.8.0 release notes
- https://decentespresso.com/blog/httpvisualizercoffee_is_amazing — Visualizer's puck curves
- https://decentespresso.com/blog/perfectly_calibrating_decent_flow_measurements — DE1 pump-model accuracy
- https://medium.com/data-science/post-shot-quality-metrics-for-espresso-78ca525f0215 — null result on post-shot predictors
- https://cdn.acaia.co/web/doc/manuals/lunar/Lunar_MAN_AE7F2605_EN.pdf — Acaia Lunar manual

---

## Requirements & Constraints

### Project-level rules (CLAUDE.md + MEMORY.md)

1. **Never ask the user for cup weight** (CLAUDE.md, Important Notes): "The BT scale often produces artifacts — spikes, drops to 0g, or null readings near end-of-shot. Never ask the user for the weight. Estimate dose out from the last stable weight sample, or fall back to `total_volume_ml × 0.82` (puck absorption). A ±2g estimate is fine for diagnosis and feedback."
2. **Firmware 1.8.0 semantic traps** (CLAUDE.md): `evt:status.bt` semantic flip and `MAX_HISTORY_ENTRIES`→`MIN_FREE_SPACE_BYTES` retention shift. Tangentially relevant — may affect fixtures spanning firmware versions.
3. **Core Rule — channeling fix** (CLAUDE.md): "Sour AND bitter = channeling. Fix puck prep (WDT, distribution, even tamp) — NOT grind. Grinding finer makes channeling worse." **A false-positive channeling diagnostic from `/diagnose` would push the user toward an actively harmful fix.**
4. **Flow meter during bloom ≠ channeling** (MEMORY.md): "Flow meter measures water entering the group head, not exiting the basket. During bloom (pump off, valve open), boiler gravity feed pushes water into the puck. Cup weight 0g = absorption, not through-flow. Only flag if cup weight is also increasing. `time_to_first_drip_s` is flow-meter-based so reports early — use first cup weight appearance instead." This trap applies verbatim to `time_to_first_nonzero_weight_flow_s` if defined naively.
5. **End-of-shot samples are artifacts** (MEMORY.md): residual samples after pump stops are not extraction data.

### DR-4 (research/gaggimate-1-8-0-upgrade/research.md)

- Context correction already landed: `vf` **is** in `.slog`; parser already reads it. The work is "just transformer surfacing."
- Sizing: **XS** (option a chosen). Manual validation against a known historical shot. No fixture test anticipated at DR-4 authoring time — 016 has since closed, so the AC now does mandate fixture-based testing.
- No divergence threshold documented in DR-4 or its follow-up.

### Parent ticket 013 and siblings

- **013**: epic-level coordinator. 014, 016, 017 are closed. **018 (DDSA port) and 021 (drift verification) are open.**
- **016 conventions** (R2–R9): goldens are the complete `TransformedShot`; byte-stable via `json.dumps(sort_keys=True, indent=2)` + trailing newline; EXACT equality on every field (no float tolerance); custom deep-equality walker with field-path error messages; `refresh_fixtures.py` CLI; ≥ 3 fixtures covering ≥ 2 profile types and ≥ 2 coffee origins.
- **018**: open; will port `AnalyzerService.js` `calculateShotMetrics` to Python and surface per-phase `exit_reason_type` (`weight | volumetric | pressure | flow | pumped | time`) in `/diagnose`. The "weight" exit reason is the authoritative native classification of weight-flow termination. A 015 divergence line overlaps with (and may contradict) 018's output.
- **021**: open; investigates mixed-era retention, purge-order invariants, and **BLE-precision float drift (6-digit `std::to_string` ↔ `atof` round-trips)**. `vf` is one of the fields at risk if BLE drift is confirmed — goldens captured now (from whatever firmware era) may shift by ~0.01 g/s after 021's findings land.

### Knowledge base

- `knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md`: covers pre-infusion, distribution, puck saturation. **Does not document a pump-vs-weight divergence threshold.** The AC's "threshold documented in DR-4 follow-up or in EXTRACTION_SCIENCE_REFERENCE.md" is a reference to documents that do not currently contain the threshold.
- `knowledge/EXTRACTION_SCIENCE.md`: qualitative channeling prevention guidance (distribution > tamping > pressure; pre-infusion saturates before extraction). Not threshold-shaped.

### Prior lifecycle precedent (add-profile-compliance-metrics)

Recent ticket added `ComplianceMetrics` to the same transformer file:

- TypedDict fields, `Optional[float]`, returns `None` when fewer than N qualifying samples (pressure RMSE requires ≥3 brew-phase samples with `tp`).
- Brew-phase filter (`cp ≥ 50% of peak cp`) applied only to metrics where that filter is semantically correct.
- `/diagnose` SKILL.md updated to surface the new metrics with documented thresholds when non-None.
- `test_transformers_shot.py` existing unit tests continue to pass (additive change).

This is the closest template for 015.

### Scope boundaries that apply

- **Hard block on 016**: fixture-based regression is a must-have AC ("No 'manual validation acceptable' escape hatch").
- **Three new FlowSummary fields + one new TransformedSample field**: the field count is fixed by AC.
- **Docstring update is inline**: no separate docs ticket.
- **`/diagnose` divergence line is conditional**: open for Spec-time decision (see Open Questions).

---

## Tradeoffs & Alternatives

### Alternative 0 — Ticket proposal

Per-sample `weight_flow_g_s` in `TransformedSample` + three named aggregates in `FlowSummary` + a new `/diagnose` divergence line.

- **Implementation complexity**: moderate. 2–3 files, additive TypedDict changes, aggregate logic mirrors `peak_flow_ml_s`/`avg_flow_ml_s`.
- **Maintainability**: high. Mirrors the `flow_ml_s` pattern exactly.
- **Alignment**: perfect — all `TransformedSample` fields are derived unit-converted values; all `FlowSummary` aggregates are pre-rounded named floats.
- **Extensibility**: excellent. `/feedback` or future tickets can consume `peak_weight_flow_g_s` without re-computing.
- **Test burden**: 3 goldens regenerate; diff review per fixture.
- **Risks**: ownership of the divergence threshold is diffused (see Adversarial Review); pathological `vf` values in existing fixtures may produce garbage aggregates without data hygiene.

### Alternative A — Per-sample only + lazy aggregates in /diagnose

- Rejected. Breaks the `FlowSummary` pattern (aggregates must be present and pre-computed); couples `/diagnose` implementation details to transformer internals; skills have no regression harness equivalent to 016.

### Alternative B — Single `divergence_score` aggregate

- Rejected. Lossy compression; opaque; blocks future consumers from the raw signal; breaks the pattern of named, interpretable fields.

### Alternative C — Raw `vf` without derived `weight_flow_g_s`

- Rejected. Breaks the `TransformedSample` derived-unit convention; pushes unit conversion and interpretation onto every consumer; no shared interpretation.

### Recommendation

**Alternative 0 wins** for the transformer/aggregate portion. The `/diagnose` divergence line is conditional — see Open Questions.

---

## Adversarial Review

### Failure modes surfaced

1. **`vf` sentinel values: signed int16 clamped at ±20.00.** Fixture 247 contains 37 negative `vf` samples (8 at the clamp floor `-20.00`); fixture 249 contains 32 negative values. A naive `peak_weight_flow_g_s = max(vf)` on 247 returns `20.0` from an isolated positive spike at t=1.0 s — before the puck is wet (`pf=0.0`, `cp≈0.4`). A naive `avg_weight_flow_g_s` on 247 returns `-2.67 g/s`. These are garbage outputs that regression tests would memorialize as "correct" goldens, providing false confidence.
2. **BT-scale tare spikes produce false `time_to_first_nonzero`.** Fixture 247's only positive `vf` samples (6.90 at t=0.75 s, 20.00 at t=1.00 s) occur before any water traverses the puck. Naive scan `vf > 0.0` returns t=0.75 s. The real first weight-flow signal in fixture 249 is at t=15.0 s (v=0.1, vf=0.1) — aggregation can't distinguish noise from signal without a noise-floor threshold and cross-validation against cup weight.
3. **`sample.get('vf', 0.0)` conflates absent with zero.** Existing `flow_ml_s` aggregation uses `if 'pf' in s`. Replicating this discipline for `vf` is mandatory; the parser only emits `vf` when bit 8 of `fields_mask` is set.
4. **Bloom-phase false positive.** MEMORY.md flags exactly this trap for `time_to_first_drip_s`. Reproducing it under a new field name is a regression.
5. **Downsampling vs aggregation mismatch.** `select_representative_samples` drops to `MAX_SAMPLES_PER_PHASE=25`. Aggregates run over raw samples, so `peak_weight_flow_g_s` may not appear in any per-phase sample the user inspects.
6. **Float-equality regression risk.** `round(-14.55 * 10) / 10 = -14.6` via banker's rounding. Goldens pinned to Python 3 rounding mode; migration to Decimal or different rounding breaks all goldens silently.
7. **Goldens regenerate trivially — verdicts don't.** Bit-equality tests do not validate correctness. Without human diff review of the regenerated values, garbage goldens (peak=20.0 from scale tare) pass the test.

### Assumptions that may not hold

- **"Three fixtures carry clean `vf` data."** They carry `vf` data, but pathologically: negatives, clamp sentinels, scale-tare spikes dominate. Regression-test passage is a weak assertion without a fourth clean fixture (shot 170 is the candidate per MEMORY.md).
- **"Threshold is portable from native analyzer."** No native analyzer threshold exists — the firmware uses puck conductance derivative, not pump-vs-weight divergence. The AC's reference to "native analyzer" is imprecise.
- **"XS effort."** Factoring in threshold invention, `vf` data-hygiene, rounding-mode pinning, 3 golden diffs under human review, and a `/diagnose` skill section, this is S–M, not XS.

### Anti-patterns and scope creep

- **A non-authoritative `/diagnose` divergence threshold can cause active harm.** False-positive channeling diagnostic → user grinds finer → opposite of CLAUDE.md Core Rule's "fix puck prep, NOT grind." This is worse than imprecise — it's agent advice that moves the user away from the correct fix.
- **Overlap with 018 (DDSA port).** 018 produces authoritative per-phase `exit_reason_type` (including "weight" — the native classification of weight-flow termination). Shipping a heuristic divergence line from 015 pre-empts 018's authoritative output; when 018 lands, either (a) the 015 line is ripped out, or (b) two contradictory diagnostics coexist.

### Interaction risks with 018 and 021

- **018**: the DDSA port's "weight" exit reason subsumes most of what the 015 divergence line would claim. Building the line now risks rework.
- **021**: BLE-precision float drift investigation specifically targets `vf` as one of the fields at risk. Goldens captured now may drift by ~0.01 g/s after 021's findings land; `time_to_first_nonzero_weight_flow_s` at the LSB boundary is most vulnerable.

### Recommended mitigations (forwarded to Spec)

1. **Data hygiene for aggregates (mandatory)**:
   - Drop clamp sentinels (`|vf| >= 20.0`).
   - Presence guard (`'vf' in s`).
   - Noise-floor filter for `time_to_first_nonzero_weight_flow_s` (require `vf > noise_floor` AND cross-validate against non-zero cup weight).
   - Return `None` on zero qualifying samples; never silently emit `0.0`.
2. **Pin rounding mode** with an inline code comment (Python 3 banker's rounding).
3. **Human eyeball on regenerated goldens** before merge (PR checklist line).
4. **Consider adding a fourth clean fixture** (shot 170) to anchor positive assertions rather than only passing over pathological data.
5. **`/diagnose` divergence line: defer or drop** — see Open Questions.
6. **Note the ~9% `analyze_shot` JSON size bloat** in the spec for backlog 001 coordination.

---

## Open Questions

The following questions are not resolvable from codebase/docs alone — they need user judgment at Spec time. Each is explicitly **deferred** to Spec per the Research Exit Gate protocol.

1. **Should the `/diagnose` pump-flow vs weight-flow divergence line ship in this ticket?** The user previously confirmed "keep both transformer + `/diagnose` line in one ticket" at Clarify. The adversarial review surfaces new information: (a) no authoritative threshold source exists (DR-4 follow-up and `knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md` don't contain one; "native analyzer" has no channeling detector to port); (b) a false-positive channeling call actively violates CLAUDE.md Core Rule ("fix puck prep, NOT grind"); (c) 018 (DDSA port, open) will produce the authoritative native classification via per-phase `exit_reason_type`, subsuming most divergence signal. **Deferred: will be resolved at Spec §2a confidence check or at the §4 approval gate — Spec must present the three options (ship line with proposed threshold + warning; drop line and defer to 018; experimental/gated behind a flag) and wait for user decision.**

2. **How should `time_to_first_nonzero_weight_flow_s` define "nonzero"?** Options: (a) strict `vf > 0.0` on raw samples (the naive reading of the field name — will produce scale-tare false positives per the adversarial review); (b) `vf ≥ 0.3 g/s` noise-floor filter (from web research BT-scale analysis); (c) `vf > 0` AND `v > 0` cross-validation (mirrors the `time_to_first_weight_s` pattern). **Deferred: Spec must pick an option, document the rationale, and test the behavior on fixture 247 (where naive would fire at t=0.75 s) to verify it resolves to the correct first-weight-flow event.**

3. **Should `avg_weight_flow_g_s` be shot-wide or brew-phase-filtered?** Shot-wide averages will include bloom and idle samples (likely zero or negative, diluting the average). Brew-phase filter (`cp ≥ 50% peak cp`, following `ComplianceMetrics` R5) yields a more meaningful number. **Deferred: Spec decides the filter scope; document the choice adjacent to the field.**

4. **Should a fourth "clean" fixture (shot 170, the dialed-in 5★ reference per MEMORY.md) be added to 016's fixture set?** Current fixtures carry pathological `vf` data. A clean fixture gives the regression test a positive-signal assertion rather than memorializing noise. **Deferred: Spec decides whether to (a) add a fourth fixture as part of 015, (b) file a follow-up 016-bis ticket, or (c) proceed with 3 fixtures and document the limitation.**

5. **`vf` data-hygiene rules for `peak_weight_flow_g_s` and `avg_weight_flow_g_s`.** The adversarial review mandates: drop clamp sentinels (`|vf| >= 20.0`), presence-guard (`'vf' in s`), return `None` on zero qualifying samples. Spec must formalize these rules as acceptance criteria so they land in code review and are not dropped at implementation time. **Deferred: Spec must enumerate the hygiene rules as explicit R-numbered requirements.**

These five questions are the items Spec must resolve before implementation can proceed. Items (1), (3), and (4) are user-facing decisions; items (2) and (5) are design choices where Spec proposes and the user signs off.
