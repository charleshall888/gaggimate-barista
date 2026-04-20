# Plan: surface-weight-flow-g-s-in-transformedsample-flowsummary

## Overview

Additive transformer change: four new weight-flow fields land in `mcp/src/gaggimate_mcp/transformers/shot.py` (one `TransformedSample` per-sample + three `FlowSummary` aggregates) behind a shared `valid()` sample-hygiene predicate, with the server docstring, fixture goldens, and fixture README updated in lock-step. No parser, `/diagnose`, or `/feedback` changes — scope matches the approved spec exactly.

## Tasks

### Task 1: Add new TypedDict fields and rounding-mode pin comment

- **Files**: `mcp/src/gaggimate_mcp/transformers/shot.py`
- **What**: Extend the `FlowSummary` TypedDict with three `Optional[float]` aggregate fields and the `TransformedSample` TypedDict with one `float` per-sample field. Add the R7 rounding-mode pin comment adjacent to the `FlowSummary` declaration so reviewers see the `banker | round-half-to-even` contract near the fields it constrains. This task is schema-only — no logic changes.
- **Depends on**: none
- **Complexity**: simple
- **Context**:
  - `FlowSummary` TypedDict at lines 30–36 currently holds `total_volume_ml`, `avg_flow_ml_s`, `peak_flow_ml_s`, `time_to_first_drip_s: Optional[float]`, `time_to_first_weight_s: Optional[float]`. Add, in order (insertion order in the class body does not affect JSON sort order): `peak_weight_flow_g_s: Optional[float]`, `avg_weight_flow_g_s: Optional[float]`, `time_to_first_nonzero_weight_flow_s: Optional[float]`.
  - `TransformedSample` TypedDict at lines 63–70 currently holds `time_seconds`, `temperature_c`, `pressure_bar`, `flow_ml_s`, `weight_g`, `resistance`. Add `weight_flow_g_s: float` (anywhere in the class body; JSON sort order is alphabetical regardless).
  - R7 comment: a single line (e.g., `# Aggregates use round(x * 10) / 10 — Python 3 banker's rounding (round-half-to-even). Golden fixtures are byte-stable under this mode.`) — must contain the token `banker` OR `round-half-to-even` to pass R7 grep. Place directly above the `FlowSummary` class `class FlowSummary(TypedDict):` line or immediately inside the class docstring scope.
- **Verification**:
  - `grep -c 'weight_flow_g_s: float' mcp/src/gaggimate_mcp/transformers/shot.py` — pass if count ≥ 1
  - `grep -cE 'peak_weight_flow_g_s: Optional\[float\]' mcp/src/gaggimate_mcp/transformers/shot.py` — pass if count = 1
  - `grep -cE 'avg_weight_flow_g_s: Optional\[float\]' mcp/src/gaggimate_mcp/transformers/shot.py` — pass if count = 1
  - `grep -cE 'time_to_first_nonzero_weight_flow_s: Optional\[float\]' mcp/src/gaggimate_mcp/transformers/shot.py` — pass if count = 1
  - `grep -nE 'banker|round-half-to-even' mcp/src/gaggimate_mcp/transformers/shot.py` — pass if ≥ 1 line reported
- **Status**: [x] complete

### Task 2: Populate `weight_flow_g_s` in `select_representative_samples`

- **Files**: `mcp/src/gaggimate_mcp/transformers/shot.py`
- **What**: Add one line to the `TransformedSample(...)` constructor call inside `select_representative_samples` so every downsampled phase sample carries `weight_flow_g_s`, sourced from the parser's `vf` field and pre-rounded to 1 decimal place. Mirror the exact pattern of the adjacent `flow_ml_s=round(sample.get('pf', 0.0) * 10) / 10` line. Absent `vf` → `0.0` per existing TypedDict convention (schema-level `float`, not `Optional[float]`).
- **Depends on**: [1]
- **Complexity**: simple
- **Context**:
  - Target region: the `TransformedSample(...)` call at lines 175–182.
  - Add: `weight_flow_g_s=round(sample.get('vf', 0.0) * 10) / 10,` — placed adjacent to `flow_ml_s=...` for reviewer continuity (the two fields are conceptually paired).
  - Do NOT apply the hygiene `valid()` predicate here. Per-sample display values preserve raw signal (including negatives and clamp sentinels) so phase samples remain faithful to the underlying data; hygiene is aggregate-scope only (the spec's Unified Hygiene Rule applies in `calculate_summary`, not in per-sample surfacing).
- **Verification**: `grep -c 'weight_flow_g_s=round' mcp/src/gaggimate_mcp/transformers/shot.py` — pass if count ≥ 1
- **Status**: [x] complete

### Task 3: Implement Unified Hygiene Rule helper and three `FlowSummary` aggregates

- **Files**: `mcp/src/gaggimate_mcp/transformers/shot.py`
- **What**: Add a module-level helper (e.g., `_is_valid_vf_sample(sample: dict) -> bool`) encoding the Unified Hygiene Rule: `'vf' in sample AND abs(sample['vf']) < 20.0 AND sample.get('pf', 0.0) > 0.0`. Compute and include the three new `FlowSummary` fields in `calculate_summary`, each layering additional filters on top of the shared `valid()` predicate per the spec's hygiene-section table. Return `None` for every degenerate case (no qualifying samples; avg requires ≥ 3). The helper MUST be module-level and shared — three duplicated inline lambdas would pass verification but diverge silently on future edits.
- **Depends on**: [2]
- **Complexity**: complex
- **Context**:
  - Helper signature: `def _is_valid_vf_sample(sample: dict) -> bool`. Body: single boolean expression `'vf' in sample and abs(sample['vf']) < 20.0 and sample.get('pf', 0.0) > 0.0`. Place adjacent to `_get_brew_phase_samples` (lines 187–209) for locality.
  - The `abs(vf) < 20.0` constant is pinned to the firmware's `std::int16_t / FLOW_SCALE=100` clamp at ±20.00 g/s (see research §Adversarial Review). A firmware change to this clamp would silently degrade the filter — if the scaling or clamp value ever changes, this hygiene rule must be revisited. The strict-less-than is deliberate per the spec's Unified Hygiene Rule rationale.
  - `peak_weight_flow_g_s` (spec R2): over `clean_samples`, collect `[s['vf'] for s in clean_samples if _is_valid_vf_sample(s) and s['vf'] > 0.0]`. Return `round(max(values) * 10) / 10` or `None` if empty.
  - `avg_weight_flow_g_s` (spec R3): call `_get_brew_phase_samples(shot.samples)` (not `clean_samples` — the brew-phase helper already defines the correct scope); filter via `_is_valid_vf_sample`. Degenerate: `len(values) < 3` → `None`. Else `round(sum(values) / len(values) * 10) / 10`. The rule does NOT additionally filter `vf > 0` — negative `vf` values within the brew phase WOULD be retained as honest scale drift. Note for future reviewers: the committed fixture cohort (246, 247, 249) contains zero brew-phase samples with negative `vf`, so this retained-negatives code path is specified but not regression-tested. A future positive-signal fixture with brew-phase scale drift could close that gap; 015 does not capture one.
  - `time_to_first_nonzero_weight_flow_s` (spec R4): scan raw `samples` (matches the existing `time_to_first_drip_s` / `time_to_first_weight_s` scope at lines 308–321). Return the first time where `_is_valid_vf_sample(sample) AND sample['vf'] > 0.3 AND sample.get('v', 0.0) > 0.0`. Rounding: `round(all_times[i] * 10) / 10`. Return `None` if no sample qualifies.
  - Compute the three new values before the `FlowSummary(...)` call at line 323, then add them to the constructor invocation. Do NOT introduce any code path that emits `0.0` when no qualifying samples exist — `None` is load-bearing per the spec's `ComplianceMetrics` precedent.
  - The `peak_flow_ml_s` and `avg_flow_ml_s` existing lines at 304–305 are the structural template for the per-aggregate pattern; do not reuse their filters (those key off `pf`, not `vf`).
- **Verification**:
  - `grep -c '_is_valid_vf_sample' mcp/src/gaggimate_mcp/transformers/shot.py` — pass if count ≥ 4 (one `def` + one call per aggregate)
  - `grep -c 'peak_weight_flow_g_s=' mcp/src/gaggimate_mcp/transformers/shot.py` — pass if count ≥ 1 (FlowSummary constructor)
  - `grep -c 'avg_weight_flow_g_s=' mcp/src/gaggimate_mcp/transformers/shot.py` — pass if count ≥ 1
  - `grep -c 'time_to_first_nonzero_weight_flow_s=' mcp/src/gaggimate_mcp/transformers/shot.py` — pass if count ≥ 1
- **Status**: [x] complete

### Task 4: Document the four new fields in the `analyze_shot` MCP tool docstring

- **Files**: `mcp/src/gaggimate_mcp/server.py`
- **What**: Extend the `analyze_shot` tool docstring (lines 460–467) with a `Returns:` block that enumerates the four new fields — one per `TransformedSample` (`weight_flow_g_s`) and three per `FlowSummary` (`peak_weight_flow_g_s`, `avg_weight_flow_g_s`, `time_to_first_nonzero_weight_flow_s`) — with a one-line semantic description each. The existing `Returns: JSON string with shot analysis` line may be retained above or absorbed into the new structure.
- **Depends on**: [1]
- **Complexity**: simple
- **Context**:
  - Target function: `async def analyze_shot(shot_id: str) -> str` at server.py line 459.
  - Docstring body spans lines 460–467 today (very terse — 3 short lines).
  - Each new-field description should note: semantic role (what the field means), hygiene behavior (what gets filtered), and for aggregates the degenerate `null` case. Target ≤ 2 lines per field. This docstring is read by MCP clients and AI consumers — keep it succinct, not exhaustive.
  - `weight_flow_g_s` appears once per sample in `phases[*].samples[*]` AND in the `Returns:` block prose — the spec's R5(a) asks for ≥ 4 occurrences across the whole file, which naturally follows from documenting the aggregate trio (each of which names `weight_flow_g_s` in its description) plus the standalone per-sample mention.
- **Verification**:
  - `grep -c 'weight_flow_g_s' mcp/src/gaggimate_mcp/server.py` — pass if count ≥ 4
  - `grep -c 'peak_weight_flow_g_s' mcp/src/gaggimate_mcp/server.py` — pass if count ≥ 1
  - `grep -c 'avg_weight_flow_g_s' mcp/src/gaggimate_mcp/server.py` — pass if count ≥ 1
  - `grep -c 'time_to_first_nonzero_weight_flow_s' mcp/src/gaggimate_mcp/server.py` — pass if count ≥ 1
- **Status**: [x] complete

### Task 5: Snapshot current goldens, regenerate, and verify value-preservation + aggregate correctness

- **Files**: `mcp/tests/fixtures/shots/246.golden.json`, `mcp/tests/fixtures/shots/247.golden.json`, `mcp/tests/fixtures/shots/249.golden.json`
- **What**: Create an ephemeral snapshot directory via `mktemp -d`, copy the three committed goldens into it (gating on `cp` exit status so a failed snapshot does not vacuously satisfy later diffs), run `python -m gaggimate_mcp.tools.refresh_fixtures <shot_id>` (no `--fetch`) for each shot ID, then run the full verification suite. The verification distinguishes three independent classes: (a) structural — every regenerated golden carries all four new keys at the right paths; (b) value-preservation — a jq-normalized diff between the ephemeral snapshot and the regenerated golden yields zero changed lines outside the four new keys; (c) aggregate-correctness — fixture 247 must produce `null` for peak and first-nonzero (empirical result of the Unified Hygiene Rule on its sample set, per critical-review simulation), while fixtures 246 and 249 must produce non-null positive-signal values with a physical-ordering relationship to `time_to_first_drip_s`. Positive-signal checks on healthy fixtures are what actually discriminate a correct implementation from one that filters too aggressively and nulls out everything.
- **Depends on**: [1, 2, 3]
- **Complexity**: simple
- **Context**:
  - **Ephemeral snapshot** (guards against stable-path and silent-failure risks): use `mktemp -d` so each task invocation gets a clean directory; gate `cp` on exit code (`|| exit 1`); and add a positive-signal sanity check that the snapshot actually captured the pre-R6 state — the regenerated golden must differ from the snapshot by at least 4 lines (one per new key, typically more because each key appears in many sample dicts). If `diff_count < 4`, the snapshot-then-regenerate cycle did not actually overwrite anything and the subsequent value-preservation check is meaningless.
  - Snapshot pattern (use a shell variable; do NOT use a stable `/tmp/015-pre-r6/` path):
    ```
    SNAPSHOT_DIR=$(mktemp -d -t 015-pre-r6-XXXXXX)
    for id in 246 247 249; do
      cp "mcp/tests/fixtures/shots/$id.golden.json" "$SNAPSHOT_DIR/$id.golden.json" || exit 1
      test -s "$SNAPSHOT_DIR/$id.golden.json" || exit 1
    done
    ```
  - Regeneration: `cd mcp && python -m gaggimate_mcp.tools.refresh_fixtures 246` (then 247, 249). Each invocation reads the `.slog` and writes the `.golden.json` in-place with the 016 byte-stability convention (`sort_keys=True, indent=2, trailing newline, UTF-8`).
  - Record the `git rev-parse HEAD` commit SHA immediately before regenerating and surface it in the PR description per R6 ("Record the pre-R6 commit SHA in the PR description for reference") — NOT required for this task's verification but expected at the Complete phase.
  - **Value-preservation check** (per-fixture, relies on the ephemeral snapshot): `diff <(jq --sort-keys '.' "$SNAPSHOT_DIR/<id>.golden.json") <(jq --sort-keys '.' mcp/tests/fixtures/shots/<id>.golden.json) | grep -E '^[<>]' | grep -v -E '"(weight_flow_g_s|peak_weight_flow_g_s|avg_weight_flow_g_s|time_to_first_nonzero_weight_flow_s)":' | wc -l` must return 0.
  - **Positive-signal snapshot sanity** (per-fixture, ensures `cp` actually happened): `diff <(jq --sort-keys '.' "$SNAPSHOT_DIR/<id>.golden.json") <(jq --sort-keys '.' mcp/tests/fixtures/shots/<id>.golden.json) | grep -cE '^[<>]'` must return ≥ 4. If this is 0, the snapshot equals the regenerated file — either `cp` silently failed or regeneration was a no-op. Either way, the value-preservation diff above is vacuous.
  - **Fixture 247 aggregate-correctness invariants** (tightened from spec R2(c)/R4(c) based on critical-review empirical analysis): under the Unified Hygiene Rule, 247 has zero samples where `pf > 0 AND vf > 0` coincide. Therefore `peak_weight_flow_g_s` and `time_to_first_nonzero_weight_flow_s` must both regenerate to exactly `null`. The spec's `== null OR bounded` disjunctive invariant is vacuous on 247 (the `== null` clause short-circuits); the strict `== null` assertion below has real discriminating power — any non-null value on 247 signals the hygiene rule did not filter correctly.
  - **Fixture 246 and 249 positive-signal invariants** (new, not in spec — fill the coverage gap the spec explicitly defers): healthy fixtures must produce non-null `peak_weight_flow_g_s` and non-null `time_to_first_nonzero_weight_flow_s`, and the physical-ordering invariant from spec R4(b) — `time_to_first_nonzero_weight_flow_s >= time_to_first_drip_s` — must hold non-trivially (both values non-null). These are the load-bearing checks that a correct hygiene rule survives positive-signal fixtures instead of nulling them out.
- **Verification**:
  - `cd mcp && pytest tests/test_shot_regression.py` — pass if exit 0
  - For each shot_id in {246, 247, 249}: `jq -e '.summary.flow | has("peak_weight_flow_g_s") and has("avg_weight_flow_g_s") and has("time_to_first_nonzero_weight_flow_s")' mcp/tests/fixtures/shots/<id>.golden.json` — pass if exit 0
  - For each shot_id in {246, 247, 249}: `jq -e '[.phases[].samples[] | has("weight_flow_g_s")] | all' mcp/tests/fixtures/shots/<id>.golden.json` — pass if exit 0
  - For each shot_id in {246, 247, 249}: positive-signal snapshot sanity (per Context block, `diff_count ≥ 4`) — pass if output ≥ 4
  - For each shot_id in {246, 247, 249}: value-preservation diff (per Context block) — pass if output is `0`
  - **Fixture 247 peak invariant (tightened to strict null)**: `jq -e '.summary.flow.peak_weight_flow_g_s == null' mcp/tests/fixtures/shots/247.golden.json` — pass if exit 0
  - **Fixture 247 first-nonzero invariant (tightened to strict null)**: `jq -e '.summary.flow.time_to_first_nonzero_weight_flow_s == null' mcp/tests/fixtures/shots/247.golden.json` — pass if exit 0
  - **Fixture 246 positive-signal (peak non-null)**: `jq -e '.summary.flow.peak_weight_flow_g_s != null' mcp/tests/fixtures/shots/246.golden.json` — pass if exit 0
  - **Fixture 246 positive-signal (first-nonzero non-null)**: `jq -e '.summary.flow.time_to_first_nonzero_weight_flow_s != null' mcp/tests/fixtures/shots/246.golden.json` — pass if exit 0
  - **Fixture 246 physical-ordering (non-trivial)**: `jq -e '(.summary.flow.time_to_first_nonzero_weight_flow_s != null) and (.summary.flow.time_to_first_drip_s != null) and (.summary.flow.time_to_first_nonzero_weight_flow_s >= .summary.flow.time_to_first_drip_s)' mcp/tests/fixtures/shots/246.golden.json` — pass if exit 0
  - **Fixture 249 positive-signal (peak non-null)**: `jq -e '.summary.flow.peak_weight_flow_g_s != null' mcp/tests/fixtures/shots/249.golden.json` — pass if exit 0
  - **Fixture 249 positive-signal (first-nonzero non-null)**: `jq -e '.summary.flow.time_to_first_nonzero_weight_flow_s != null' mcp/tests/fixtures/shots/249.golden.json` — pass if exit 0
  - **Fixture 249 physical-ordering (non-trivial)**: `jq -e '(.summary.flow.time_to_first_nonzero_weight_flow_s != null) and (.summary.flow.time_to_first_drip_s != null) and (.summary.flow.time_to_first_nonzero_weight_flow_s >= .summary.flow.time_to_first_drip_s)' mcp/tests/fixtures/shots/249.golden.json` — pass if exit 0
- **Status**: [x] complete

### Task 6: Document hygiene behavior per fixture in the fixture README

- **Files**: `mcp/tests/fixtures/shots/README.md`
- **What**: Add a new subsection (or extend each existing per-fixture subsection) describing which rules of the Unified Hygiene Rule apply on each of the three fixtures and which aggregate outputs result. Stay at the rule level — do NOT prescribe specific numeric timestamps in prose, because grep-for-tokens verification cannot detect prose that contradicts the regenerated goldens. The golden JSON is the source of truth for values; the README documents the classes of filtering logic that drove each fixture's outcome.
- **Depends on**: [5]
- **Complexity**: simple
- **Context**:
  - README structure: three existing per-fixture subsections (`### 249.slog`, `### 246.slog`, `### 247.slog`) at roughly lines 7–23.
  - Add a new top-level section (e.g., `## Weight-flow hygiene behavior`) OR append a short "Weight-flow hygiene" paragraph to each per-fixture block. Either works for the grep checks.
  - Per-fixture prose guidance (rule-level, not timestamp-level):
    - **246 (healthy, complete)**: sufficient samples satisfy the Unified Hygiene Rule to produce non-null `peak_weight_flow_g_s`, non-null `avg_weight_flow_g_s`, and non-null `time_to_first_nonzero_weight_flow_s`. This is the cleanest positive-signal fixture.
    - **247 (pathological / BT-artifact candidate)**: the Unified Hygiene Rule rejects so many samples that both `peak_weight_flow_g_s` and `time_to_first_nonzero_weight_flow_s` regenerate to `null`, and `avg_weight_flow_g_s` is `0.0`. Two filters are doing the rejection work: (a) the `pf > 0` guard eliminates pre-pump tare samples (positive `vf` and `v` before the pump starts); (b) the `abs(vf) < 20.0` strict-less-than clamp filter eliminates firmware int16 clamp-sentinel samples. Both filters are necessary — describe the ROLE of each filter without asserting specific timestamp values (the source of truth for which sample failed which filter is the `.slog` + the hygiene helper, not the README prose). The end result is that 247 exercises the rejection paths but produces null/zero aggregates, not non-null rejection survivors.
    - **249 (healthy bloom-slide, multi-phase)**: most brew-phase samples pass the Unified Hygiene Rule, producing non-null aggregates. The `avg_weight_flow_g_s` aggregate does NOT apply an extra `vf > 0` filter on top of the base hygiene rule — so negative-`vf` samples would be retained during the brew phase — but this committed fixture does not contain any such samples in practice (its negative-`vf` samples all sit in the pre-brew region, pre-filtered by the brew-phase + `pf > 0` gates). A future fixture with genuine brew-phase scale drift would exercise the retained-negatives path; 249 does not.
  - Do not assert specific sample timestamps, `vf`/`v`/`pf` values, or exact aggregate numbers in README prose. Those are golden-JSON content. The README describes rule classes and aggregate-level outcomes only.
  - Misattribution pitfall (from critical review): on fixture 247 at the `vf=20.0` clamp sentinel, the `abs(vf) < 20.0` clamp filter rejects the sample regardless of whether `pf > 0` — do NOT describe this sample as "rejected by the `pf > 0` guard" in prose. It is the clamp filter that fires first; the `pf > 0` guard handles different samples (pre-pump positive-`vf` spikes that are below clamp).
  - Position matters: the per-fixture sections describe each fixture, so per-fixture hygiene notes belong in those sections; a cross-fixture summary sentence under a new heading is optional.
- **Verification**:
  - `grep -c 'weight_flow_g_s' mcp/tests/fixtures/shots/README.md` — pass if count ≥ 1
  - `grep -c 'peak_weight_flow_g_s' mcp/tests/fixtures/shots/README.md` — pass if count ≥ 1
  - `grep -cE 'time_to_first_nonzero_weight_flow_s|avg_weight_flow_g_s' mcp/tests/fixtures/shots/README.md` — pass if count ≥ 1
- **Status**: [x] complete

### Task 7: Full MCP test suite — no-regressions verification

- **Files**: none (verification-only; runs the existing `mcp/tests/` suite)
- **What**: Run the full MCP test suite to confirm no regressions. This is the spec R9 ("No regressions") acceptance gate — ensures that Tasks 1–3's transformer edits and Task 5's golden regeneration have not broken any existing test (`test_transformers_shot.py`, `test_parsers_shot.py`, `test_shot_fixture_walker.py`, the rating/model/diagnostics suites, etc.).
- **Depends on**: [5]
- **Complexity**: simple
- **Context**:
  - Command: `cd mcp && pytest tests/`.
  - Does not depend on Task 6 — README changes are docs-only and not test-covered.
  - If this fails, the most likely culprits are: (a) a hygiene-rule implementation bug producing unexpected aggregate values that contradict the regenerated goldens (unlikely — Task 5 already ran `test_shot_regression.py` against the new goldens); (b) an unrelated test that indirectly relied on `FlowSummary` or `TransformedSample` field counts (unlikely — these are TypedDicts, additive).
  - If the suite fails for a reason NOT covered by the above two categories, stop and report — do not blindly regenerate goldens again or edit tests to accommodate.
- **Verification**: `cd mcp && pytest tests/` — pass if exit 0
- **Status**: [x] complete

## Verification Strategy

End-to-end correctness is established by four independently-load-bearing checks:

1. **Type-surface check (Tasks 1–4 verifications)**: grep-based existence of each new field at each authoring site (TypedDict declaration, per-sample population site, aggregate assignment, docstring mention). Confirms the schema + documentation landed.
2. **Value-preservation check (Task 5, with snapshot-sanity pre-check)**: the `diff_count ≥ 4` sanity check guarantees the ephemeral snapshot actually captured pre-regeneration state; the value-preservation diff then confirms no value changed outside the four new keys.
3. **Aggregate-correctness check (Task 5, positive- and negative-signal)**: fixture 247 must produce strict `null` for peak and first-nonzero (an empirical consequence of the hygiene rule on 247's sample set — any non-null value signals a filtering bug); fixtures 246 and 249 must produce non-null peak and first-nonzero with `time_to_first_nonzero_weight_flow_s >= time_to_first_drip_s`. The strict-null check discriminates against under-filtering bugs (e.g., missing `pf > 0` guard would produce peak=6.9 on 247); the positive-signal checks discriminate against over-filtering bugs that would silently null out healthy fixtures.
4. **Full-suite regression (Task 7)**: `pytest tests/` catches any collateral damage — parser, walker, and unrelated tests must all still pass.

Note the coverage gap (acknowledged but not closed in 015): no committed fixture exercises the "retained-negatives in brew phase" code path for `avg_weight_flow_g_s`, because all three fixtures have their negative `vf` samples in the pre-brew region. A silent "`vf >= 0` filter slipped into `avg`" bug would escape all Task 5 checks on this fixture cohort. This is surfaced in Scope Boundaries; closing it requires a future fixture capture.

## Veto Surface

- **Helper placement and naming.** The plan names the hygiene helper `_is_valid_vf_sample`. The spec uses `valid(sample)` informally. The plan chooses a longer, module-prefixed name for discoverability and to avoid shadowing Python's `valid` (which doesn't exist as a builtin, but the short name carries zero context at call sites). If the user prefers a shorter name or an inline lambda, this can be revised — but inline-lambda-per-aggregate has a maintenance cost the plan explicitly rejects (three lambdas that must stay in sync as hygiene evolves).
- **R7 comment location.** The plan places the R7 banker's-rounding comment near the `FlowSummary` TypedDict (Task 1). The spec allows placement near either the field declarations OR the aggregate-computation block. Placing it near the TypedDict keeps Task 3 focused on logic; reviewers may prefer seeing it adjacent to the `round()` calls themselves. The verification grep passes either way.
- **Task 4 docstring verbosity.** The plan caps each field's prose at ≤ 2 lines to keep the docstring AI-consumer-friendly. If the user wants fuller prose (e.g., quoting the hygiene rule in-line) the docstring grows proportionally; R5's grep AC still passes.
- **Fixture coverage gap (critical review outcome).** The critical review confirmed the committed fixture cohort (246, 247, 249) has structural blind spots for this hygiene rule: (a) fixture 247's pathological samples all have `pf = 0`, so once the `pf > 0` guard fires, the aggregates drop to `null`/`0.0` without exercising a non-null "hygiene-rule-rejected-pathology-but-kept-good-data" survivor; (b) fixture 249's negative-`vf` samples all sit pre-brew, so the brew-phase retained-negatives code path in `avg_weight_flow_g_s` is specified but unexercised. Task 5's verification has been tightened (strict `== null` on 247, positive-signal non-null + physical ordering on 246/249) to extract maximum discriminating power from the cohort, but a silent `vf >= 0` filter slipped into `avg_weight_flow_g_s` would still escape. The user may revisit whether to block 015 on capturing a positive-signal fixture that exercises retained-negatives (scope expansion, likely requires a new `.slog` capture) or ship with the documented gap.
- **Spec-tightening in verification (not in AC).** Spec R2(c) and R4(c) permit a disjunctive `== null OR bounded` invariant on 247. The plan's Task 5 Verification tightens both to strict `== null` — a spec-compliant restriction (still satisfies the disjunction). If future fixture-data changes would make 247 legitimately produce a non-null bounded value, the tightened verification would fail where the spec-level AC would pass. That is the intended behavior (the tightened check has real teeth); if the user believes the disjunctive form is load-bearing for forward compatibility, the strict form can be reverted.

## Scope Boundaries

Mapped from the spec's Non-Requirements (§50–61):

- **No `/diagnose` divergence line.** Explicitly deferred by user decision at Spec interview; not bundled with 018's phase-exit classification.
- **No parser edits.** `mcp/src/gaggimate_mcp/parsers/shot.py` already decodes `vf`.
- **No new fixture captures.** Shot 170 was evicted by the 1.8.0 free-space purge before 016's fixture capture; positive-signal coverage is a future-ticket concern. 015 validates only against the three committed 016 fixtures (246, 247, 249).
- **No `/feedback` skill changes.** The skill does not consume `FlowSummary` today.
- **No new unit-test files.** Existing fixture regression (`test_shot_regression.py`) covers all hygiene rules via the three committed fixtures.
- **No cross-ticket coordination with 001** (three-level detail param). The ~9% JSON bloat is accepted; 001's sizing work proceeds independently.
- **No threshold documentation in `knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md`.** The divergence-threshold prose the original AC referenced was never written and is not a 015 deliverable.

### Known coverage gaps (critical review, not closed in 015)

- **Retained-negatives in `avg_weight_flow_g_s` is specified but not regression-tested.** The Unified Hygiene Rule deliberately does not apply a `vf > 0` filter on top of the base predicate for the `avg` aggregate, so brew-phase negative-`vf` samples are semantically retained as "honest scale drift during extraction." None of fixtures 246, 247, 249 contains a brew-phase sample with negative `vf` — all their negative-`vf` samples sit pre-brew, pre-filtered by the brew-phase + `pf > 0` gates. A silent bug that adds a `vf >= 0` filter to `avg_weight_flow_g_s` would not regress any committed golden. Closing this gap requires a future fixture capture of a shot with genuine brew-phase scale-drift behavior.
- **Fixture 247 exercises the rejection paths but only produces `null` survivors.** Because 247 has no sample where positive `vf` coincides with `pf > 0`, the hygiene rule nulls out all three aggregates. The tightened verification (strict `== null` rather than `== null OR bounded`) extracts maximum discriminating power from this shape, but it cannot verify that a surviving non-null value on another pathological fixture would carry the correct value. A future fixture with a tare spike followed by a legitimate weight-flow signal would cover this.
- **The `abs(vf) < 20.0` clamp value is pinned to current firmware behavior.** A firmware change that shifts the int16 scaling factor or the clamp bounds would silently degrade the filter; no test in this plan would catch it. Sibling ticket 021's BLE-precision drift investigation may surface related issues.
- **Per-sample `weight_flow_g_s = 0.0` default conflates absent with zero.** The spec explicitly chose `sample.get('vf', 0.0)` for consistency with existing per-sample fields (`flow_ml_s`, `temperature_c`) — this latent asymmetry with aggregates (which emit `None` for sparsity) is a spec-level decision, not a plan-phase concern. On current fixtures every sample has `vf` present, so the default never fires; if a future fixture is captured from firmware with a narrower `fields_mask`, per-sample `weight_flow_g_s` will silently report `0.0` everywhere while aggregates correctly report `None`. That inconsistency would require a spec-level revisit (possibly to change per-sample `weight_flow_g_s` to `Optional[float]`).
