# Plan: port-ddsa-phaseendstop-algorithm-into-diagnose

## Overview

Port Gaggimate v1.8.0's `calculateShotMetrics` + `detectAutoDelay` from `AnalyzerService.js` into a new stdlib-only Python module at `mcp/src/gaggimate_mcp/analysis/shot_analyzer.py`, prove 1e-3 parity against reference-JS output via a Node harness that produces `.reference-js.json` sidecars for the three existing fixtures, extend `analyze_shot`'s MCP response with `phase_exits`/`auto_delay`/`analyzer_url`, and surface the new fields in the `/diagnose` Response Format. Tasks are ordered so harness + reference-JS sidecars exist before the parity test runs against the Python port, and so the TypedDicts + `js_round` are in place before the main algorithm port. Task 8 is split by structural seam (helpers → main algorithm) so each sub-task has real unit-level verification rather than a signature-only gate.

## Tasks

### Task 1: Create analysis/ package scaffold
- **Files**: `mcp/src/gaggimate_mcp/analysis/__init__.py` (new), `mcp/src/gaggimate_mcp/analysis/shot_analyzer.py` (new, stub)
- **What**: Create the new namespace so `diagnostics.py` stays untouched (R16). Module docstring opens with `Port of AnalyzerService.js lines 208–1006 @ gaggimate v1.8.0` and reserves the `Re-syncing shot-analyzer on firmware upgrades` subsection (short-form reference pointing at `mcp/README.md` — content fleshed out in Task 15). `__init__.py` is empty.
- **Depends on**: none
- **Complexity**: simple
- **Context**: Namespace parallels existing `mcp/src/gaggimate_mcp/transformers/`. Do NOT rename or restructure `mcp/src/gaggimate_mcp/diagnostics.py` — the research doc's original proposal was rejected in favor of a non-colliding namespace.
- **Verification**: `python -c "import gaggimate_mcp.analysis.shot_analyzer"` — pass if exit 0. AND `uv run pytest mcp/tests/test_shot_regression.py` — pass if exit 0 (the new package must not perturb pytest autodiscovery, fixture paths, or import order for the existing regression test — this is a cheap early gate on package-level side effects).
- **Status**: [ ] pending

### Task 2: Define TypedDicts, constants, ANALYZER_JS_VERSION
- **Files**: `mcp/src/gaggimate_mcp/analysis/shot_analyzer.py`
- **What**: Add the five numeric constants (`PREDICTIVE_WINDOW_MS=4000`, `LAST_PHASE_UNDERSHOOT_MIN_G=2`, `LAST_PHASE_UNDERSHOOT_MAX_G=6`, `LAST_PHASE_OVERSHOOT_MAX_G=4`, `LAST_PHASE_ESTIMATED_DELAY_MAX_MS=4000`) + `ANALYZER_JS_VERSION = "v1.8.0"`. Add TypedDicts: `PhaseExitReason` (`exit_reason_type: Literal["weight","volumetric","pressure","flow","pumped","duration","unknown"]`, `unavailable_reason: Optional[Literal["profile_unavailable"]]` — key always present), `AutoDelayEstimate` (`delay_ms: Optional[int]`, `auto: bool`, `unavailable_reason: Optional[Literal["profile_unavailable"]]`), `ProfileData`, `ProfilePhase`, `ProfileTarget`. `ProfilePhase.pump.target` is a plain `str` (not `Literal`) to accept `"power"` — spec Non-Requirements §power.
- **Depends on**: [1]
- **Complexity**: simple
- **Context**: Signatures — `class PhaseExitReason(TypedDict)` with field list matching R5. Reference `mcp/src/gaggimate_mcp/transformers/shot.py` TypedDict style. Do NOT route `ProfileData` through `mcp/src/gaggimate_mcp/models/profile.py` Pydantic — DDSA deliberately reads raw JSON (Technical Constraint §`ProfileData`).
- **Verification**: `grep -c 'TypedDict' mcp/src/gaggimate_mcp/analysis/shot_analyzer.py` — pass if count ≥ 5. `grep -E 'PREDICTIVE_WINDOW_MS *= *4000|LAST_PHASE_UNDERSHOOT_MIN_G *= *2|LAST_PHASE_UNDERSHOOT_MAX_G *= *6|LAST_PHASE_OVERSHOOT_MAX_G *= *4|LAST_PHASE_ESTIMATED_DELAY_MAX_MS *= *4000|ANALYZER_JS_VERSION *= *.v1.8.0.' mcp/src/gaggimate_mcp/analysis/shot_analyzer.py | wc -l` — pass if count = 6.
- **Status**: [ ] pending

### Task 3: Implement `js_round` helper + `test_js_round.py`
- **Files**: `mcp/src/gaggimate_mcp/analysis/shot_analyzer.py`, `mcp/tests/test_js_round.py` (new)
- **What**: Implement `def js_round(value: float) -> int` with half-away-from-zero semantics (matches JS `Math.round`, differs from Python `round`'s banker's-rounding). Write unit test covering the five canonical cases from R3.
- **Depends on**: [1]
- **Complexity**: simple
- **Context**: Reference asserts: `js_round(0.5) == 1`, `js_round(-0.5) == 0`, `js_round(2.5) == 3`, `js_round(-2.5) == -2`, `js_round(24.5) == 25`. Implementation sketch: `math.floor(value + 0.5)` for non-negative, `-math.floor(-value + 0.5)` for negative, with an `if value >= 0` branch.
- **Verification**: `uv run pytest mcp/tests/test_js_round.py -v` — pass if exit 0, 5 asserts green.
- **Status**: [ ] pending

### Task 4: Vendor JS harness files + package.json
- **Files**: `mcp/tests/fixtures/shots/harness/analyzer-service.v1.8.0.js` (new), `mcp/tests/fixtures/shots/harness/parse-binary-shot.v1.8.0.js` (new), `mcp/tests/fixtures/shots/harness/package.json` (new)
- **What**: Download `web/src/pages/ShotAnalyzer/services/AnalyzerService.js` and `web/src/pages/ShotHistory/parseBinaryShot.js` from gaggimate repo at tag `v1.8.0`, save verbatim (no edits) under filenames embedding the version. Write `package.json` with `"type": "module"`, `"engines": {"node": ">=20.17.0"}`, zero runtime deps.
- **Depends on**: none
- **Complexity**: simple
- **Context**: Source URLs — `https://raw.githubusercontent.com/jniebuhr/gaggimate/v1.8.0/web/src/pages/ShotAnalyzer/services/AnalyzerService.js` and `.../web/src/pages/ShotHistory/parseBinaryShot.js`. Research note: `parseBinaryShot.js` is required because `calculateShotMetrics` expects pre-parsed samples, not `.slog` bytes.
- **Verification**: `ls mcp/tests/fixtures/shots/harness/analyzer-service.v1.8.0.js mcp/tests/fixtures/shots/harness/parse-binary-shot.v1.8.0.js mcp/tests/fixtures/shots/harness/package.json` — pass if exit 0 (all three present). `node -e "import('./mcp/tests/fixtures/shots/harness/analyzer-service.v1.8.0.js').then(m => console.log(typeof m.calculateShotMetrics))"` — pass if stdout is `function`.
- **Status**: [ ] pending

### Task 5: Write Node `capture.js` entry script
- **Files**: `mcp/tests/fixtures/shots/harness/capture.js` (new)
- **What**: CLI entry — `node capture.js <shot_id>` runs for one fixture; `node capture.js --all` iterates `mcp/tests/fixtures/shots/*.slog`. For each: read `<shot_id>.slog` bytes, pass through vendored `parseBinaryShot` to produce `shotData`; read `<shot_id>.profile.json` verbatim as `profileData`; call `calculateShotMetrics(shotData, profileData, HARNESS_SETTINGS)` where `HARNESS_SETTINGS = {scaleDelayMs: 200, sensorDelayMs: 200, isAutoAdjusted: true}`. These three values are authoritative per spec R8 and match the live device's v1.8.0 web UI defaults (verified during 018 research); the inline comment at `HARNESS_SETTINGS`'s declaration cites `web/src/pages/ShotAnalyzer/index.jsx:~111-112 @ v1.8.0` as the original authoring location for future-reviewer context — overnight is NOT required to verify those exact line numbers (index.jsx is not vendored in Task 4). Write output via canonical serializer (`JSON.stringify` with recursively-sorted keys + 2-space indent) to `<shot_id>.reference-js.json`.
- **Depends on**: [4]
- **Complexity**: simple
- **Context**: Canonical serializer helper sketch: recursive `sortKeys(obj)` that sorts object keys alphabetically, then `JSON.stringify(sortKeys(result), null, 2)`. Script must be runnable from repo root; use `import.meta.url` / `fileURLToPath` for path resolution. `HARNESS_SETTINGS` is declared at module top with the citation comment so R-drift-risk is mitigated by local readability.
- **Verification**: `node mcp/tests/fixtures/shots/harness/capture.js --all` — pass if exit 0 and all three `.reference-js.json` files are written (verified by Task 6).
- **Status**: [ ] pending

### Task 6: Generate reference-JS sidecars for 246/247/249
- **Files**: `mcp/tests/fixtures/shots/246.reference-js.json` (new), `mcp/tests/fixtures/shots/247.reference-js.json` (new), `mcp/tests/fixtures/shots/249.reference-js.json` (new)
- **What**: Run `node mcp/tests/fixtures/shots/harness/capture.js --all` from repo root. Commit the three emitted files verbatim.
- **Depends on**: [5]
- **Complexity**: simple
- **Context**: The `.profile.json` sidecars already exist (pre-committed 2026-04-21 via live device capture — see R6). No device needed. Re-run of capture.js against unchanged inputs must produce byte-identical output (canonical serializer guarantee).
- **Verification**: `ls mcp/tests/fixtures/shots/{246,247,249}.reference-js.json` — pass if exit 0 (all three exist). Idempotency check: `node mcp/tests/fixtures/shots/harness/capture.js --all && git diff --exit-code mcp/tests/fixtures/shots/*.reference-js.json` — pass if exit 0 (re-run leaves no diff; note this verifies determinism, not correctness — reference-JS IS the normative oracle).
- **Status**: [ ] pending

### Task 7: Extend `shot_fixture_walker.py` with tolerance parameters
- **Files**: `mcp/tests/fixtures/shots/shot_fixture_walker.py`
- **What**: Add two optional params to `compare()` and `assert_equal()`: `float_tol: float = 0.0` and `per_field_tol: Optional[dict[str, float]] = None`. When `float_tol > 0` and both `expected` and `actual` are floats, compare via `math.isclose(expected, actual, abs_tol=float_tol, rel_tol=0.0)`. When `per_field_tol` maps a path string to a float, the override wins; when the path maps to `None` or the sentinel `EXACT`, strict `==` applies even under `float_tol > 0`. NaN-aware: `(math.isnan(expected) and math.isnan(actual))` compares equal. Integer-typed fields always use strict `==` (Python `==` already handles this; no coercion). On mismatch, the walker's existing mismatch-message format is preserved AND extended to include the field path + expected + actual + (if applicable) the tolerance that was in effect.
- **Depends on**: none
- **Complexity**: simple
- **Context**: Define `EXACT` as a module-level sentinel (e.g., `EXACT = object()`). Default behavior with `float_tol=0.0` must be byte-identical to pre-change — 016's regression contract is preserved by keeping both params opt-in. Field-path string format should match the walker's existing mismatch-message convention.
- **Verification**: `uv run pytest mcp/tests/test_shot_fixture_walker.py` — pass if exit 0 (existing tests unchanged).
- **Status**: [ ] pending

### Task 8a: Port DDSA helpers + unit tests (scale-lost propagation covered)
- **Files**: `mcp/src/gaggimate_mcp/analysis/shot_analyzer.py`, `mcp/tests/test_shot_analyzer_helpers.py` (new)
- **What**: Port the four named helpers from `AnalyzerService.js` to module-private Python functions (underscore-prefixed so `classify_phase_exits` and `estimate_auto_delay` can reuse them without exposing a public API): `_get_metric_stats` (JS `getMetricStats`, line 21), `_get_phase_anchor_index_for_weight_rate` (JS `getPhaseAnchorIndexForWeightRate`, line 72), `_get_regression_weight_rate` (JS `getRegressionWeightRate`, line 86), `_get_phase_weight_rate` (JS `getPhaseWeightRate`, line 125). Replace every JS `Math.round` with `js_round` (R3). Implement the scale-lost-permanently sticky-flag helper (`_update_scale_lost_flag` or equivalent) used by the 4 check sites + 2 fallback paths at JS lines 407, 447, 545, 624, 691–692, 804. Write `test_shot_analyzer_helpers.py` with unit tests for each helper (including synthetic inputs for scale-lost flag propagation — no fixture dependency) covering: (a) `_get_metric_stats` on a known 10-sample window returns correct min/max/avg; (b) `_get_regression_weight_rate` on a linear weight ramp returns the expected slope; (c) `_get_phase_weight_rate` on a last-phase vs. non-last-phase returns the documented contract; (d) scale-lost flag stays `True` once set (sticky); (e) scale-lost flag triggers correctly on cumulative weight drop. The unit tests are compared against hand-computed expected values, not reference-JS output — this gates Task 8a on logic correctness, not on reference-JS availability.
- **Depends on**: [2, 3]
- **Complexity**: complex
- **Context**: `ShotData` is the existing dataclass at `mcp/src/gaggimate_mcp/parsers/shot.py:105` (verified via grep) — DDSA operates on raw ~100 ms samples (Research §Critical gap), NOT downsampled `TransformedShot`. Reference the vendored JS at `mcp/tests/fixtures/shots/harness/analyzer-service.v1.8.0.js` during the port for line-by-line translation. Helpers should NOT import from each other circularly; if a scale-lost site needs a helper, inline the site inside the helper's caller.
- **Verification**: `uv run pytest mcp/tests/test_shot_analyzer_helpers.py -v` — pass if exit 0, all unit tests green (including ≥ 2 scale-lost flag propagation cases). `grep -nE '^[[:space:]]*round\(' mcp/src/gaggimate_mcp/analysis/shot_analyzer.py` — pass if no output (no bare `round()` calls).
- **Status**: [ ] pending

### Task 8b: Port `classify_phase_exits` main algorithm
- **Files**: `mcp/src/gaggimate_mcp/analysis/shot_analyzer.py`
- **What**: Port the main body of `calculateShotMetrics` (JS lines 208–991) to `def classify_phase_exits(raw_shot: ShotData, profile_snapshot: ProfileData) -> list[PhaseExitReason]`. Reuse the private helpers from Task 8a (`_get_metric_stats`, `_get_phase_anchor_index_for_weight_rate`, `_get_regression_weight_rate`, `_get_phase_weight_rate`, `_update_scale_lost_flag`). Implement the predictive-window regression logic. Preserve the `'duration'` exit-reason token verbatim (not `'time'`). Wire the 4 scale-lost check sites + 2 fallback paths at the JS line locations from the spec's Technical Constraints (`407, 447, 545, 624, 691–692, 804`).
- **Depends on**: [8a]
- **Complexity**: complex
- **Context**: Re-use Task 8a's private helpers rather than re-implementing — the port is an integration task over helpers, not a full translation. Output shape is `list[PhaseExitReason]` (one per phase of `raw_shot.phases`). Handle empty `profile_snapshot.phases` and `raw_shot.phases` mismatches per the JS source's guards.
- **Verification**: `python -c "from gaggimate_mcp.analysis.shot_analyzer import classify_phase_exits; import inspect; sig = inspect.signature(classify_phase_exits); assert list(sig.parameters) == ['raw_shot', 'profile_snapshot'], sig"` — pass if exit 0 (function signature matches R4). `grep -nE '^[[:space:]]*round\(' mcp/src/gaggimate_mcp/analysis/shot_analyzer.py` — pass if no output (still no bare `round()` after integration).
- **Status**: [ ] pending

### Task 9: Port `estimate_auto_delay`
- **Files**: `mcp/src/gaggimate_mcp/analysis/shot_analyzer.py`
- **What**: Port `detectAutoDelay` (JS lines 993–1006). Signature: `def estimate_auto_delay(raw_shot: ShotData, profile_snapshot: ProfileData, manual_delay_ms: Optional[int] = None) -> AutoDelayEstimate`. When `manual_delay_ms` is provided, return `{"delay_ms": manual_delay_ms, "auto": False, "unavailable_reason": None}` without estimation. Otherwise reuse Task 8a's private helpers to compute the auto-delay estimate and return `{"delay_ms": <int via js_round>, "auto": True, "unavailable_reason": None}`. Do NOT re-call `classify_phase_exits`; share private helpers via module scope.
- **Depends on**: [8b]
- **Complexity**: simple
- **Context**: The 14 JS lines are short but operate on derived metrics — Task 8a's helpers provide the shared primitives. `delay_ms` must be an `int` or `None` — never `float` (R17 asserts this). `AutoDelayEstimate` TypedDict from Task 2.
- **Verification**: `python -c "from gaggimate_mcp.analysis.shot_analyzer import estimate_auto_delay, AutoDelayEstimate; import inspect; sig = inspect.signature(estimate_auto_delay); assert list(sig.parameters) == ['raw_shot', 'profile_snapshot', 'manual_delay_ms'], sig"` — pass if exit 0.
- **Status**: [ ] pending

### Task 10: Parity test `test_phase_end_stop_parity.py`
- **Files**: `mcp/tests/test_phase_end_stop_parity.py` (new)
- **What**: Parametrize over `mcp/tests/fixtures/shots/*.slog` (glob; no hard-coded fixture list). For each: load `.slog` → parse to `ShotData`; load sibling `<shot_id>.profile.json` → parse to `ProfileData`; if either sibling is missing, call `pytest.fail(...)` with a message naming the missing path AND pointing at the `## Adding a new fixture` section of `mcp/README.md` (Task 15). Run `classify_phase_exits` and `estimate_auto_delay`; load `<shot_id>.reference-js.json`; compare both Python outputs against the reference via `shot_fixture_walker.compare()` with `float_tol=1e-3` and a module-level `PER_FIELD_TOL` dict. `PER_FIELD_TOL` forces strict `==` (sentinel `EXACT`) on every R11-listed field: `auto_delay.delay_ms`, `phases[*].estimated_scale_delay_ms`, `phases[*].match_step`, AND every field produced by a JS `Math.round` call (the port emits at minimum 6 such fields corresponding to the 6 `Math.round` sites at JS lines 407, 447, 545, 624, 691–692, 804 — if the port produces fewer such fields, the `EXACT` list shrinks accordingly). Every `PER_FIELD_TOL` entry carries an inline `#` comment directly above it that includes BOTH the JS source line AND a one-line root-cause note (e.g., `# JS:624 — accumulation order differs at end-of-shot under flow=0 samples`). Entries with only a JS line and no root-cause note are invalid and fail PR review; comments must explain WHY the tolerance is needed, not just WHERE in the JS source.
- **Depends on**: [6, 7, 8b, 9]
- **Complexity**: complex
- **Context**: Follow the gold-standard pattern in `mcp/tests/test_shot_regression.py` (parametrize over `FIXTURE_DIR.glob("*.slog")`, `.stem` as id, `pytest.fail` on missing sibling). `PER_FIELD_TOL` is a `dict[str, Union[float, object]]` where `EXACT` sentinel values force strict equality. Use `from mcp.tests.fixtures.shots.shot_fixture_walker import compare, EXACT`. On failure, the walker's mismatch message (Task 7) reports field path + expected + actual + effective tolerance; this is what overnight uses to route recovery (see Verification Strategy → Recovery Routing).
- **Verification**: `uv run pytest mcp/tests/test_phase_end_stop_parity.py -v` — pass if exit 0, all three fixtures green. `grep -c 'EXACT' mcp/tests/test_phase_end_stop_parity.py` — pass if count ≥ 7 (3 named fields from R11 plus at least 4 of the 6 Math.round-produced fields; ≥ 7 surfaces under-coverage if the Math.round-producing fields are missed). `grep -B 1 '".*":.*[0-9]' mcp/tests/test_phase_end_stop_parity.py | grep -c '^#'` — pass if count equals the number of non-EXACT numeric entries in `PER_FIELD_TOL`.
- **Status**: [ ] pending

### Task 11: Extend `analyze_shot` MCP tool response
- **Files**: `mcp/src/gaggimate_mcp/server.py`
- **What**: In `analyze_shot`, after `http_client.fetch_shot` returns `shot_data`, invoke `classify_phase_exits(shot_data, profile_snapshot)` and `estimate_auto_delay(shot_data, profile_snapshot)` BEFORE `transform_shot_for_ai` runs. Fetch `profile_snapshot` via `await ws_client.load_profile(shot_data.profile_id)` — this is the specific internal symbol (grep-verified at `mcp/src/gaggimate_mcp/server.py:178` inside the existing `manage_profile` tool's `action='get'` branch). The `ws_client` module-global is defined at `server.py:33` (`ws_client = GaggimateWebSocketClient(config)`); reuse it directly rather than inventing a new fetch path. On any profile-fetch failure (network, missing UUID, renamed, WebSocket error): emit one `PhaseExitReason` per phase in `shot_data.phases` with `exit_reason_type="unknown"` and `unavailable_reason="profile_unavailable"`; set `auto_delay={"delay_ms": None, "auto": False, "unavailable_reason": "profile_unavailable"}`. No retries, no backoff. Always construct `analyzer_url = f"http://{config.host}/analyze/{shot_id.lstrip('0') or '0'}"` using the pre-normalization `shot_id` input parameter (not `normalized_id`, not `TransformedShot.shot_id`). Add top-level keys `phase_exits`, `auto_delay`, `analyzer_url` to the response dict. Extend the tool docstring with field-by-field descriptions matching the `weight_flow_g_s` doc depth.
- **Depends on**: [9]
- **Complexity**: simple
- **Context**: `GaggimateConfig.gaggimate_host` at `mcp/src/gaggimate_mcp/config.py:7-17,42-45` exposes `.host`. `analyze_shot` is at `mcp/src/gaggimate_mcp/server.py:458-530`. Existing keys (`success`, `shot`, `rating`, `incomplete`, `error`, `error_code`, `suggestion`, `exception_type`) remain unchanged — additive only. `ws_client.load_profile` returns a dict matching the device profile JSON shape (raw device output); cast/adapt to `ProfileData` as needed.
- **Verification**: `grep -cE '"phase_exits"|"auto_delay"|"analyzer_url"' mcp/src/gaggimate_mcp/server.py` — pass if count ≥ 3 (all three keys assigned in the response dict). Note: real correctness of the response is gated by Task 12's end-to-end test; this grep is the task-local smoke check.
- **Status**: [ ] pending

### Task 12: End-to-end `analyze_shot` DDSA response test
- **Files**: `mcp/tests/test_analyze_shot_ddsa_response.py` (new)
- **What**: Mock `http_client.fetch_shot` and `ws_client.load_profile` to return committed fixture data. Invoke `analyze_shot`, parse the returned JSON via `json.loads`, assert: (a) `phase_exits`, `auto_delay`, `analyzer_url` keys present; (b) `auto_delay["delay_ms"]` is `int` or `None` — explicitly reject `float`, `"NaN"`, `"Infinity"`; (c) each `phase_exits[*]` has `exit_reason_type`, `phase_number`, `unavailable_reason`; (d) `analyzer_url` matches `r"^http://[^/]+/analyze/\d+$"` on numeric-shot-id; (e) parametrized case with `shot_id="abc"` succeeds with URL ending in `/analyze/abc`. Add a degradation case: `ws_client.load_profile` raises → `phase_exits[*].exit_reason_type == "unknown"`, `phase_exits[*].unavailable_reason == "profile_unavailable"`, `analyzer_url` still renders.
- **Depends on**: [11]
- **Complexity**: simple
- **Context**: Async mocking pattern — follow `mcp/tests/test_save_shot_notes_rmw.py` (`AsyncMock`, `monkeypatch`, `importlib.reload`). JSON `NaN`/`Infinity` check: `assert "NaN" not in raw_json_str and "Infinity" not in raw_json_str` after `json.dumps(..., allow_nan=False)` OR via explicit type checks on parsed values.
- **Verification**: `uv run pytest mcp/tests/test_analyze_shot_ddsa_response.py -v` — pass if exit 0, all parametrized cases + degradation case green.
- **Status**: [ ] pending

### Task 13: `ANALYZER_JS_VERSION` consistency test
- **Files**: `mcp/tests/test_analyzer_version_consistency.py` (new)
- **What**: Import `ANALYZER_JS_VERSION` from `gaggimate_mcp.analysis.shot_analyzer`. Glob `mcp/tests/fixtures/shots/harness/analyzer-service.*.js` and `.../parse-binary-shot.*.js`. Assert both globs return at least one file AND the matched filenames contain the version string (e.g., `analyzer-service.v1.8.0.js` when `ANALYZER_JS_VERSION == "v1.8.0"`). Test fails loudly when a future re-sync updates one side without the other.
- **Depends on**: [2, 4]
- **Complexity**: simple
- **Context**: Use `pathlib.Path(__file__).parent / "fixtures" / "shots" / "harness"` for glob root.
- **Verification**: `uv run pytest mcp/tests/test_analyzer_version_consistency.py -v` — pass if exit 0.
- **Status**: [ ] pending

### Task 14: Update `/diagnose` skill Response Format
- **Files**: `.claude/skills/diagnose/SKILL.md`
- **What**: Locate the `### Phase Comparison` heading inside the `## Response Format` template block. Extend it with a per-phase bullet template: `- **Phase {n} ({name}):** exited on {exit_reason_type} at t+{elapsed_s}s ({target summary})`. Add a trailing bullet `- **Estimated scale delay:** {delay_s}s ({auto | manual})`. After `### What to Watch For`, append a final line `Interactive chart: {analyzer_url}`. Add a fallback rendering rule: when a phase's `exit_reason_type == "unknown"` AND `unavailable_reason == "profile_unavailable"`, render that phase's bullet as `- **Phase {n} ({name}):** exit reason unavailable (profile unavailable)` and always emit the deep-link line.
- **Depends on**: [11]
- **Complexity**: simple
- **Context**: Heading targets — use section headings (`### Phase Comparison`, `### What to Watch For`), not line numbers; line ranges in spec are approximate. No behavior change to the "2b. COMPARE Intended vs Actual" section or the `<claims>` block.
- **Verification**: `grep -c 'exited on' .claude/skills/diagnose/SKILL.md` — pass if count ≥ 1. `grep -c 'Estimated scale delay' .claude/skills/diagnose/SKILL.md` — pass if count ≥ 1. `grep -c 'Interactive chart:' .claude/skills/diagnose/SKILL.md` — pass if count ≥ 1. `grep -c 'profile unavailable' .claude/skills/diagnose/SKILL.md` — pass if count ≥ 1.
- **Status**: [ ] pending

### Task 15: Create `mcp/README.md`
- **Files**: `mcp/README.md` (new)
- **What**: Three top-level sections in order — `## Prerequisites` (Node ≥20.17.0 with macOS + Linux install hints; note that `engines` is advisory); `## Re-syncing shot-analyzer on firmware upgrades` (7 ordered steps per R14); `## Adding a new fixture` (5 ordered steps per R14, plus draft-PR fallback for contributors without Node). Append a `## Known coverage gaps` list with five items (flow-target-only Turbo, pure power-target, decaf/dark-roast, cross-era, scale-lost mid-shot) — not gating 018 but documented for future fixtures. Short-form reference in `shot_analyzer.py`'s module docstring already points here (Task 1 stubbed it).
- **Depends on**: [5, 11]
- **Complexity**: simple
- **Context**: `mcp/README.md` does not currently exist — it is created by this task. The repo-root `README.md` is unchanged (ADDED list in spec).
- **Verification**: `grep -c '^## Prerequisites' mcp/README.md` = 1; `grep -c '^## Re-syncing shot-analyzer on firmware upgrades' mcp/README.md` = 1; `grep -c '^## Adding a new fixture' mcp/README.md` = 1; `grep -c '^## Known coverage gaps' mcp/README.md` = 1 — all four checks must pass.
- **Status**: [ ] pending

### Task 16: Full test sweep + regression check
- **Files**: none (invocation only)
- **What**: Run full MCP pytest suite. Verify the existing regression test (`test_shot_regression.py`) passes unchanged, `test_shot_fixture_walker.py` passes unchanged, and the five new test files are green (`test_js_round.py`, `test_shot_analyzer_helpers.py`, `test_phase_end_stop_parity.py`, `test_analyze_shot_ddsa_response.py`, `test_analyzer_version_consistency.py`). Verify `mcp/src/gaggimate_mcp/diagnostics.py` was not modified.
- **Depends on**: [10, 12, 13, 14, 15]
- **Complexity**: simple
- **Context**: This is the end-of-feature smoke gate — if anything regresses, the feature is not complete.
- **Verification**: `uv run pytest mcp/tests/` — pass if exit 0. `git diff HEAD -- mcp/src/gaggimate_mcp/diagnostics.py` — pass if no output (R16).
- **Status**: [ ] pending

## Verification Strategy

End-to-end: `uv run pytest mcp/tests/` exits 0, covering the seven gating tests (test_shot_regression, test_shot_fixture_walker, test_js_round, test_shot_analyzer_helpers, test_phase_end_stop_parity, test_analyze_shot_ddsa_response, test_analyzer_version_consistency). Node harness is verified by re-running `node capture.js --all` and confirming `git diff --exit-code` on the three reference-JS sidecars. Skill-output changes are prose-to-Claude (not machine-tested, per Non-Requirements); verification is grep for the new template tokens in `SKILL.md`. Deep-link construction is covered by Task 12's URL regex assertion. `diagnostics.py` untouched is asserted by Task 16's `git diff`.

### Recovery Routing

Per-task verification is a local smoke check; logic correctness lives in Tasks 8a (helper unit tests), 10 (parity), 12 (response round-trip), and 16 (full sweep). When a downstream test fails, overnight routes recovery as follows BEFORE considering any tolerance-widening response:

- **Task 8a unit-test failure**: bug is in a specific helper. Re-read the cited JS source line for that helper and fix the Python port in place. Do not proceed to Task 8b until Task 8a is green.
- **Task 8b signature check failure (Task 8b verification)**: function does not exist or signature mismatch. Re-read Task 8b's `What` field and ensure `classify_phase_exits(raw_shot, profile_snapshot)` is the public entry.
- **Task 10 parity failure (divergence on field X of fixture Y)**:
  1. Read walker mismatch message → identify field path + expected + actual + effective tolerance.
  2. If divergence > 1e-3: open vendored `analyzer-service.v1.8.0.js` at the site corresponding to field X. Compare the Python port line-by-line. Fix the port in place.
  3. If divergence is within (1e-12, 1e-3] AND the JS source at that site uses a pattern genuinely subject to accumulation-order drift (sum-of-squares, iterative regression accumulator): add a `PER_FIELD_TOL` entry with an inline `#` comment containing BOTH the JS source line AND a one-line root-cause note. Adding `PER_FIELD_TOL` entries is the LAST resort, not the first response.
  4. If divergence is on an integer or `Math.round`-output field: add to `EXACT` set; never tolerance-widen a rounded integer field.
- **Task 10 missing-sidecar failure**: `pytest.fail` message names the missing `.profile.json` or `.reference-js.json`. The `.profile.json` sidecars are pre-committed (2026-04-21); if missing, the cause is a lost commit or merge conflict — do NOT re-capture from device. The `.reference-js.json` sidecars come from Task 6; re-run `node capture.js --all`.
- **Task 12 assertion failure (round-trip)**: bug is in Task 11's response construction. Re-read Task 11's `What` and ensure `ws_client.load_profile(shot_data.profile_id)` is called, error paths set `unavailable_reason="profile_unavailable"`, and `analyzer_url` uses pre-normalization `shot_id`.
- **Task 16 regression failure on `test_shot_regression.py`**: new `analysis/` package import perturbed pytest discovery. Re-run Task 1's verification command (`uv run pytest mcp/tests/test_shot_regression.py`) to confirm reproducibility, then audit `mcp/src/gaggimate_mcp/analysis/__init__.py` and module-level side effects in `shot_analyzer.py`.

## Veto Surface

- **Task 8 split by helper function, not by line-range**. Task 8a (helpers + unit tests) + Task 8b (main `classify_phase_exits` integrating helpers) follows named structural seams in the JS source. This replaces the original plan's atomicity stance and provides real per-sub-task verification. The split adds one test file (`test_shot_analyzer_helpers.py`) but removes the "escalate to a follow-up" escape hatch that had no operational mechanism.
- **`ProfileData` as TypedDict, not Pydantic**. Deliberate bypass of `models/profile.py`'s `Literal["pressure","flow"]` so `"power"` phases (fixture 249 suspected) don't raise at validation time. Pinned by spec's Technical Constraints and Non-Requirements; surfaced here because a future profile-model reconciliation would change this.
- **Parity tolerance fixed at 1e-3 globally, per-field exemptions via allowlist + root-cause-in-comment discipline**. `PER_FIELD_TOL` entries require inline `#` comments containing BOTH the JS source line AND a one-line root-cause note explaining WHY the tolerance is needed — not just WHERE in the JS source. Entries are NOT the first-response to parity failure (see Recovery Routing). Alternative (global 1e-2 tolerance) was rejected during Spec. If overnight finds itself adding >3 `PER_FIELD_TOL` entries during a single session, that is a signal to halt and surface to the user — not a signal to keep adding.
- **No skill-output rendering test**. Enforcement of the new `### Phase Comparison` bullets is prose-to-Claude in SKILL.md, same model as every other skill field — no automated test catches drift if Claude reflows the template. Manual review during session use is the backstop. Pinned by spec Non-Requirements.
- **HARNESS_SETTINGS values are authoritative per spec R8 + Research, not per index.jsx line-verbatim**. Task 5's citation to `index.jsx:~111-112` is for future-reviewer context only — the three values (`scaleDelayMs: 200, sensorDelayMs: 200, isAutoAdjusted: true`) were verified against the live device during 018 research and are pinned by spec R8.

## Scope Boundaries

Excluded (from spec's Non-Requirements): firmware-startup mDNS check, CI integration (`.github/workflows/` stays absent), fixture recapture of `.slog` / `.golden.json`, MVP-tier categorical-only port (auto-delay is in-scope at initial release), new MCP tool for classification (extend `analyze_shot` only), skill output changes outside the three specified surfaces, `"power"` pump-mode vocabulary in `models/profile.py`, parity tolerance < 1e-3 globally, runtime profile-fetch retry logic, deep-link suppression when offline, skill-output rendering test, synthetic scale-lost-permanently fixture (coverage provided by Task 8a's unit tests instead), `cleanName` normalization in the Node harness.
