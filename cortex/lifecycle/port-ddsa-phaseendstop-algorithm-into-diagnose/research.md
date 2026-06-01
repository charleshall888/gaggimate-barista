# Research: Port DDSA / PhaseEndStop algorithm into /diagnose

Context anchor from Clarify: Port the Gaggimate v1.8.0 PhaseEndStop / DDSA algorithm from `AnalyzerService.js` into a Python diagnostics module so `/diagnose` autonomously classifies per-phase exit reasons (`weight | volumetric | pressure | flow | pumped | time`) and estimates auto-delay, with 1e-3-tolerance parity against reference-JS output captured via browser-side export (option a). Also add a deep-link to `/diagnose` output (supersedes 020) and a firmware-upgrade runbook section. Complexity: complex. Criticality: high.

## Codebase Analysis

### Files that will change / be created

**New:**
- DDSA Python module — target path TBD (see Open Questions §1). Ticket says `mcp/src/gaggimate_mcp/diagnostics/phase_end_stop.py`; collision forces either a package conversion or a rename.
- `mcp/tests/test_phase_end_stop_parity.py` — parity test (filename pinned by 013 epic AC).
- `mcp/tests/fixtures/shots/<shot_id>.reference-js.json` — reference-JS sidecars for 246/247/249 (and later 022's additions).
- `research/gaggimate-1-8-0-upgrade/runbook.md` OR `mcp/README.md` section OR module docstring — see Open Questions §5.
- Capture helper (checked-in JS source at `mcp/tests/fixtures/shots/capture_reference_js.js` recommended — see Open Questions §3).

**Modified:**
- `mcp/src/gaggimate_mcp/diagnostics.py` (existing 318-line connection-diagnostics file) — converted to package or renamed; cascades to 4 test files that `patch('gaggimate_mcp.diagnostics.ping_host')` and `test_diagnostics.py` naming.
- `mcp/src/gaggimate_mcp/server.py:21` (import of `diagnose_connection as run_diagnostics`); likely also `server.py:458-530` (`analyze_shot` tool — extend return shape to include `phase_exits`, `auto_delay`, `analyzer_url`).
- `.claude/skills/diagnose/SKILL.md` — §Phase Comparison (`:112-126`) + §Response Format template (`:217-244`): add per-phase exit-reason line, auto-delay line, trailing `Interactive chart:` deep-link line.

### Typing conventions

- **TypedDict** for transformer outputs (`TransformedSample`, `FlowSummary`, `ShotSummary`, `ComplianceMetrics`) — `transformers/shot.py`. `Optional[float]` where `None` means "degenerate/insufficient data."
- **`dataclass`** for parser types (`ShotData`, `PhaseTransition`).
- **Pydantic `BaseModel`** for configuration/validation surfaces only (`models/` — ShotRating, Profile).
- Recommendation: `PhaseExitReason` and `AutoDelayEstimate` should be `TypedDict` with `Literal["weight","volumetric","pressure","flow","pumped","time"]` for `exit_reason_type`. **Note**: JS internal type is `'duration'`, not `'time'` — see Open Questions §4.

### TransformedSample contract (`transformers/shot.py:68-77`, post-015)

```python
class TransformedSample(TypedDict):
    time_seconds: float         # 1 d.p.
    temperature_c: float        # 1 d.p.
    pressure_bar: float         # 1 d.p.
    flow_ml_s: float            # puck flow, 1 d.p.
    weight_flow_g_s: float      # 015, 1 d.p., no hygiene filter
    weight_g: float             # cup weight, 1 d.p.
    resistance: float           # 2 d.p.
```

Each `PhaseData` has `name`, `phase_number`, `start_time_seconds`, `duration_seconds`, `samples: list[TransformedSample]`.

**Critical gap (repeated across multiple agents):**
- `TransformedShot` does **NOT** surface per-phase `targets[]` / stop-condition arrays. The JS `calculateShotMetrics` reads `shot.profile.phases[].targets[]` to decide which target was hit.
- `TransformedShot.phases[].samples` is downsampled to `MAX_SAMPLES_PER_PHASE = 25` (`transformers/shot.py:11`); the JS algorithm operates on raw ~100 ms samples. The 4-second predictive window contains ~40 raw samples but only ~5–10 downsampled samples per phase — regression rates will not reproduce at any tolerance.
- `ComplianceMetrics` reads raw `tp`/`tf` target values directly from non-transformed `shot.samples` dicts — pattern exists but isn't surfaced through `TransformedSample`.

### `/diagnose` skill integration

- `.claude/skills/diagnose/SKILL.md:112-126` — Phase Comparison (prose, closest to current stop-target summary).
- `:127-137` — compliance-metrics bullet style (precedent for structured metrics).
- `:217-244` — `## Response Format` template block. Three new surfaces: per-phase exit-reason lines, auto-delay estimate line, trailing `Interactive chart:` line.
- Context-aware flagging rule (`:133`): post-bloom ramp undershoots are normal — exit-reason interpretation must respect this.
- No structured exit-reason vocabulary exists in the repo today; net-new terminology.

### `analyze_shot` MCP tool (`server.py:458-530`)

Returns `json.dumps({"success", "shot": transformed, "rating", "incomplete"})`. Boundary: MCP returns structured data, skill formats prose. For DDSA integration, extend `analyze_shot` with `"phase_exits": [...]`, `"auto_delay": {...}`, `"analyzer_url": str` (skill runs in Claude Code process, can't read MCP env vars — URL must be pre-built MCP-side).

### GAGGIMATE_HOST

- Read via `GaggimateConfig.gaggimate_host` / `config.host` (`config.py:7-17,42-45`). Default `"gaggimate.local"`.
- **Shot ID padded vs unpadded**: `TransformedShot.shot_id="000246"` (padded, `parsers/shot.py:247`); analyzer URL uses unpadded `/analyze/246` (`verification-notes.md:66`, `align-manage-shot-notes-with-180-native-sidecar-schema/spec.md:62`). `list_recent_shots` returns unpadded. Deep-link must strip leading zeros — prefer `shot_id.lstrip("0") or "0"` over `str(int(shot_id))` (latter raises on non-numeric IDs).

### Test patterns

- `test_shot_regression.py`: gold-standard — parametrize over `FIXTURE_DIR.glob("*.slog")`, `.stem` as id, `pytest.fail(...)` on missing sibling. Model for parity test.
- `test_shot_fixture_walker.py` + `shot_fixture_walker.py`: exact-equality walker, deep field-path mismatch messages. **Does not support tolerance** — either add `float_tol` param preserving default 0.0, or write sibling walker for parity test.
- `test_save_shot_notes_rmw.py`: async mocking style (`AsyncMock`, `monkeypatch`, `importlib.reload`).

### Fixture cohort

246 (Adaptive v2), 247 (Tropical Bloom truncated / BT-artifact candidate), 249 (Tropical Bloom healthy). Shot 170 evicted pre-capture. Ticket 022 (parent: 015) will add retained-negatives + non-null pathology-survivor fixtures.

## Web Research

### Source of truth: Gaggimate v1.8.0

- Repo: `github.com/jniebuhr/gaggimate`, tag `v1.8.0` (published 2026-04-01).
- `web/src/pages/ShotAnalyzer/services/AnalyzerService.js`: 1007 lines / 38,802 bytes.
- Downloaded reference copies: `/tmp/gaggimate-v1.8.0/AnalyzerService.js`, `/tmp/gaggimate-v1.8.0/PhaseEndStop_Algorithm_English.md`, `/tmp/gaggimate-v1.8.0/index.jsx`.

### Numerical constants (verified exact)

```js
const PREDICTIVE_WINDOW_MS = 4000;
const LAST_PHASE_UNDERSHOOT_MIN_G = 2;
const LAST_PHASE_UNDERSHOOT_MAX_G = 6;
const LAST_PHASE_OVERSHOOT_MAX_G = 4;
const LAST_PHASE_ESTIMATED_DELAY_MAX_MS = 4000;
```

### Function inventory

| Line | Exported | Name | Signature |
|---|---|---|---|
| 21  | — | `getMetricStats` | `(samples, key) -> {start,end,min,max,avg}` |
| 72  | — | `getPhaseAnchorIndexForWeightRate` | `(samples, isLastPhase) -> number` |
| 86  | — | `getRegressionWeightRate` | `(samples, endIndex, windowMs = PREDICTIVE_WINDOW_MS) -> number` (g/s) |
| 125 | — | `getPhaseWeightRate` | `(samples, isLastPhase) -> number` |
| 131 | — | `getSampleInstantWeightRate` | `(sample) -> number` (prefers `sample.vf` > 0.1, else `sample.fl` > 0.1, else 0) |
| 138 | — | `isDirectionallyValidLookAhead` | `(operator, currentValue, nextValue) -> bool` |
| 145 | — | `getLastNonExtendedIndex` | `(samples) -> number` (walks back past `systemInfo?.extendedRecording`) |
| 181 | **yes** | `formatStopReason` | `(type) -> string` |
| 208 | **yes** | `calculateShotMetrics` | `(shotData, profileData, settings) -> Object` |
| 993 | **yes** | `detectAutoDelay` | `(shotData, profileData, manualDelay) -> {delay, auto}` |

### Exit reason vocabulary

Raw internal `exitType` values: `'duration'`, `'pressure'`, `'flow'`, `'weight'`, `'volumetric'`, `'pumped'`. JS uses `'duration'` — the ticket's `'time'` label does not match the JS internal value.

`formatStopReason` collapses two distinct internals to the same UI label:
- `'duration'   → 'Time Stop'`
- `'pumped'     → 'Water Drawn Stop'`
- `'volumetric' → 'Weight Stop'`
- `'weight'     → 'Weight Stop'`
- `'pressure'   → 'Pressure Stop'`
- `'flow'       → 'Flow Stop'`

The Python port should preserve distinct `exit_reason_type` (six internal values), formatting separately.

### `detectAutoDelay` output shape

Returns **only** `{ delay: number, auto: boolean }`. No classification bucket enum. The scale/sensor split is internal to `calculateShotMetrics` (lines 261-264, 604-612). Averaging is `Math.round(sum / count / 50) * 50` (50 ms bucketing, lines 890-895). The ticket's "Exact match on auto-delay classification buckets" is slightly misworded — there are no buckets in the output, just a delay value (50ms-rounded) + boolean `auto`.

### Scale-lost-permanently flag

- `globalScaleLost` (line 242): reported only.
- `scaleConnectionBrokenPermanently` (line 268): sticky once set (line 316-318); gates weight/volumetric target evaluation at 4 check sites (lines 407, 447, 545, 624) + 2 fallback paths (lines 691-692, 804). Per-phase reported as `scalePermanentlyLost` (line 880).
- Easy to miss one site during port; structured audit needed.

### PhaseEndStop_Algorithm_English.md — what's covered vs not

Covered: 4-step auto-mode check (anchor, 1×/2×sampleInterval, predictive extrapolation), per-target prediction formulas, direction check, manual-mode adjustment, last-phase specifics (overshoot/undershoot fallback, Brew-by-Time, extended-recording filtering, `sampleInterval` fallback 250ms).

Not covered (silent gaps): exact numeric constants (2/4/6g, 50ms bucketing); independent high-delay warning loop at line 804; `setEstimatedScaleDelay` monotonic-max + `>2000 ms` `phaseHighScaleDelay` threshold (line 305-307); `delayReviewHint`/`delayReviewMs`/`delayReviewReason` rollup + "hide last phase" rule (lines 935-948); `detectAutoDelay` 50ms rounding + "scale delay as primary" legacy-compat return; `getSampleInstantWeightRate` `vf` > `fl` preference at 0.1 threshold.

### JS → Python numeric portability

- **Both IEEE-754 binary64.** Add/sub/mul/div/sqrt correctly rounded — identical results.
- **`Math.round` uses round-half-away-from-zero for positives; Python `round()` uses banker's rounding.** Divergence examples: `Math.round(2.5)=3` but `round(2.5)=2`; `Math.round(0.5)=1` but `round(0.5)=0`.
- `Math.round` is used at: `setEstimatedScaleDelay` (line 297), `setPhaseDelayReviewHint` (line 311), `matchStep = Math.round(match.delayMs / sInterval)` (line 617), 50ms bucketing (lines 890, 893).
- **Port MUST implement `js_round` and lint-ban `round()` in the DDSA module.**
  ```python
  def js_round(x: float) -> int:
      return math.floor(x + 0.5) if x >= 0 else -math.floor(-x + 0.5)
  ```
- `Math.floor/ceil/abs/min/max`: match Python built-ins on finite doubles.
- `Number.isFinite` ≈ `math.isfinite`; the global JS `isFinite` coerces strings but all inputs are already numeric in context.
- NaN/Infinity: match.
- Array iteration: `forEach/map/filter/find/findIndex/some` iterate insertion order; code does explicit `.sort((a,b) => a - b)` at line 231 — Python should mirror with `sorted(keys, key=int)`.
- Nullish `??` and optional chaining `?.`: replicate defensively.
- `numpy.round` is banker's — avoid. `decimal.Decimal` unnecessary (breaks parity).

### Parity test harness pattern

Golden fixtures (widely documented). Recommended:
1. Dict traversal comparator (dict/list/scalar recursive).
2. Leaf routing: `math.isclose(a, b, abs_tol=1e-3, rel_tol=0)` for floats; `a == b` for strings/booleans/ints; NaN-aware `(isnan(a) and isnan(b)) == equal`.
3. Separate structural-diff (missing keys) from numeric-diff (value mismatch).
4. Per-field tolerance override map — essential because integer-bucketed fields (`delayMs`, matchStep, estimatedScaleDelayMs) need exact equality, not 1e-3.

### Browser console export pattern

Standard idiom:
```js
(() => {
  const blob = new Blob([JSON.stringify(window.__capture, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: 'analyzer-fixture.json' });
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
})();
```

### Option (a) feasibility — serious complication

- `index.jsx:12` imports `calculateShotMetrics, detectAutoDelay` as named ES module exports; called at `index.jsx:238`.
- **In production Vite bundles served from the device, these names are minified and wrapped in a module IIFE — `calculateShotMetrics` is NOT callable from DevTools.**
- Options collapse to: (i) run a local dev build (`npm install + vite dev`) against a proxied device; (ii) patch firmware with `window.__analyzer = { calculateShotMetrics, detectAutoDelay }` (2-line change); (iii) extract state via React DevTools.
- **Per-fixture cost under (a) is not "manual capture per fixture" as ticket claims — it's 1–2 hours of dev-environment setup plus per-fixture replay.** See Open Questions §3.

### No external DDSA documentation

Search for "DDSA PhaseEndStop Gaggimate" returns only the repo's own MD file. Acronym is Gaggimate-internal. No forum/blog/third-party coverage. Sole source of truth is the JS + its partial English companion doc.

## Requirements & Constraints

### `requirements/` directory

Does **not** exist at project root. CLAUDE.md is effective governance.

### CLAUDE.md constraints (verbatim, relevant subset)

- **Repo-first device-second** (L106): profile writes go to repo file first, device second. Applies only tangentially to DDSA (read-only over telemetry).
- **Data architecture symlinks** (L41-47): `coffees/`, `grind-map.md`, `user-setup.md` symlinked into private data repo; `GAGGIMATE_STORAGE_PATH` in `mcp/.env`.
- **Firmware 1.8.0 semantic traps** (L121-124):
  - `evt:status.bt` semantic flip: "pre-1.8.0 this field reflected `settings.isVolumetricTarget()`; in 1.8.0 it reflects `profile.isVolumetric()`".
  - Shot history retention: 1.8.0 replaced `MAX_HISTORY_ENTRIES=100` with `MIN_FREE_SPACE_BYTES=500KB`; capacity purge also deletes `.json` sidecar → `shot_id` references can orphan silently.
- **Weight anomalies** (L116): BT scale artifacts common; estimate from last stable weight or `total_volume_ml × 0.82`; never ask user for weight. DDSA consumes weight signal heavily — hygiene filtering matters.
- **Core Rules** (L126-160): `/diagnose` output style and personality (Hoffmann dryness + Hedrick enthusiasm).

### DR-1 (research/gaggimate-1-8-0-upgrade/research.md)

User chose option (a) — full port — over deep-link-only alternative. Explicit willingness to pay effort + maintenance tax for agent autonomy. "L effort + recurring maintenance tax. Mitigation: check in fixture shots + golden outputs, cite firmware version, schedule re-sync on each upstream minor release."

### Upstream contract specs

**016 (shot-fixture-regression-harness):**
- Fixtures: `<shot_id>.slog` + `.golden.json` under `mcp/tests/fixtures/shots/`; stdlib-only deep-equality walker; **R4: exact equality, no float tolerance** ("transformer pre-rounds all numeric output fields") — 018's 1e-3 tolerance is a departure from this culture.
- R8: **"No JS-reference sidecars."** 018 owns its own JS-capture mechanism.
- Non-Requirement: no new dev dependencies; stdlib + pytest stack only.

**015 (surface-weight-flow-g-s-in-transformedsample-flowsummary):**
- `TransformedSample.weight_flow_g_s` surfaced (per-sample, 1 d.p., no hygiene filter).
- `FlowSummary` gained `peak_weight_flow_g_s`, `avg_weight_flow_g_s`, `time_to_first_nonzero_weight_flow_s`.
- L54: **"018 ports DDSA to produce per-phase `exit_reason_type` classifications. This is phase-boundary classification, NOT intra-phase divergence detection."**
- Unified Hygiene Rule: `valid(sample) ≡ ('vf' in sample) AND (abs(sample['vf']) < 20.0) AND (sample.get('pf', 0.0) > 0.0)`.

**017 (document-evtstatusbt-semantic-flip-and-retention-shift):**
- Pre/post framing: "pre-1.8.0 reflected X; in 1.8.0 reflects Y" — NOT "rather than" or "1.8.0+".
- Symbol names must match verbatim: `profile.isVolumetric()`, `settings.isVolumetricTarget()`, `MAX_HISTORY_ENTRIES`, `MIN_FREE_SPACE_BYTES`, `500 KB`.

### 013 epic AC pins filename

"`mcp/tests/test_phase_end_stop_parity.py` passes with DDSA port matching reference JS output within tolerance (018)."

### Related tickets

- **021 (open, high)**: BLE-precision drift investigation. If it finds LSB drift across 1.7.3/1.8.0 boundary, DDSA parity tolerances may need revisit. Not a hard block.
- **022 (open, low, parent 015)**: adds 2 fixtures (retained-negatives + non-null pathology-survivor). 018 parity test must be extended when 022 lands.

### MCP/Python conventions

- Python 3.13+ (`mcp/pyproject.toml`).
- Deps: aiohttp, mcp[cli], pydantic, pydantic-settings, structlog, websockets. Dev: pytest, pytest-asyncio, pytest-cov. No numpy/scipy/deepdiff.
- TypedDict over Pydantic for transformer-layer outputs.
- Module layout (`mcp/src/gaggimate_mcp/`): `api/`, `models/`, `parsers/`, `storage/`, `transformers/`, `tools/`, `utils/`. `diagnostics.py` exists as a flat file (connection diagnostics) — target path collision.
- No CI exists (`.github/workflows/` absent). Parity test is local-only.

### `/diagnose` skill (`SKILL.md`)

- "Always lead with telemetry analysis" (no taste-first).
- Tier-1 style fetches full profile via `manage_profile(action="get")`.
- Response Format (`:217-244`): `## Shot Analysis`, `### Identified Style`, `### Telemetry Summary`, `### Phase Comparison`, `### Diagnosis`, `### Recommendations`, `### What to Watch For`.
- Context-aware flagging rule (`:133`): post-bloom ramp undershoots are normal.
- "Standard diagnosis uses only the always-loaded files + skill references" — DDSA module must be callable without heavy reference files.
- Self-check protocol `<claims>` block: `SHOT_STYLE, GRIND_DIRECTION, PRESSURE_NARRATIVE, TASTE_SIGNAL, PRIMARY_DIAGNOSIS, PRIMARY_RECOMMENDATION`.

## Tradeoffs & Alternatives

### A. Link-only, defer classification (DR-1 option b)

Ship the 3-line deep-link; skip the port. **Adjudicated against by user (DR-1).** Worth keeping as graceful-degradation behavior if parity fails at runtime (see Adversarial).

### B. MVP categorical-only port (no auto-delay, no strict float parity)

Port only the 6-bucket classification; defer auto-delay estimation. Cuts from ~700 to ~250–350 lines.

- **Pro:** Halves the initial work; matches 90% of agent-autonomy value ("brew exited on volumetric" is the useful bit; ±1.2s delay is second-order).
- **Con:** Categorical classification entangles with `getRegressionWeightRate` and `getPhaseAnchorIndexForWeightRate` — likely not cleanly decomposable (see Adversarial §decomposability).
- **Adversarial challenge:** The "1–2 hour spike to check decomposability" is probably spec-phase theater — the entanglement is visible from the function inventory alone. Either commit to full port or commit to MVP + follow-up ticket; don't run a half-check.

### C. JS-as-subprocess (vendor AnalyzerService.js, embed JS runtime)

py-mini-racer / quickjs / Node subprocess. **Not recommended:** adds runtime dep (Node or C++ V8 binding brittle on arm64/alpine/Python 3.13); 50-150ms cold-start per `/diagnose`; cross-engine Number semantics differ (QuickJS BigInt); single-user local deploy doesn't justify the packaging tax. Keep as last resort if Python port hits decomposition wall.

### D. Automated transpilation (js2py, Transcrypt)

**Not recommended:** produces unreadable nested `PyJs*` wrappers; defeats the legibility goal of porting; debugging collapses. Transpilation preserves JS foreignness without idiom benefit.

### E. Module layout — flat vs package; path naming

- **Collision**: ticket's `mcp/src/gaggimate_mcp/diagnostics/phase_end_stop.py` conflicts with existing `diagnostics.py` (318-line connection-diagnostics file). Four test files `patch('gaggimate_mcp.diagnostics.ping_host')`; `test_diagnostics.py` naming becomes ambiguous.
- **Flat file precedent**: `transformers/shot.py` is 521 lines; `api/websocket.py` is 471; `server.py` is 801. A 700-line flat module fits repo culture.
- **Recommendation:** Relocate to `mcp/src/gaggimate_mcp/analysis/shot_analyzer.py` (new namespace, no collision, name descriptive rather than tied to JS-internal "PhaseEndStop"). Avoid forcing `diagnostics/` package conversion and the test-naming cascade.
- **Alternative**: rename existing `diagnostics.py` → `diagnostics/connection.py` + `diagnostics/__init__.py` re-exports. Cheaper than relocation for test mocks but couples shot-telemetry analysis under the "connection diagnostics" semantic space.

### F. Parity-test organization

- **F1 (spec'd):** separate `.reference-js.json` sidecars alongside `.slog` + `.golden.json`.
- **F2 (merged):** fold reference-JS into `.golden.json`.
- **F3 (CLI-integrated refresh):** extend `refresh_fixtures` with `--reference-js` flag.
- **Recommendation:** F1. 016 explicitly scopes JS sidecars out; merging risks 016's byte-stability contract (our serializer vs JS-native formatting drift). Document in `mcp/tests/fixtures/shots/README.md` that reference-JS sidecars are captured verbatim and do NOT follow 016's byte-stability invariant — prevents future "cleanup" from corrupting the parity baseline.

### G. 1e-3 float tolerance + per-field allowlist

1e-3 is aggressive enough to catch real bugs yet loose enough to absorb IEEE-754 accumulation noise across reduce-style summations.

- **Adversarial challenge:** 1e-3 is incoherent for integer-bucketed fields (`delayMs` rounded to 50ms; matchStep; phaseEstimatedScaleDelayMs). Either use `==` for those or the 1e-3 tolerance swallows 1-unit bucket errors.
- **Recommendation:** per-field tolerance override map; integer fields explicit-`==`, floats `abs_tol=1e-3, rel_tol=0`; initial empty "known-divergent" allowlist for per-field escape hatches when genuine accumulation-order divergence emerges.

### H. Runbook home

- **H1 (ticket):** `research/gaggimate-1-8-0-upgrade/runbook.md`. Wrong epic scope — runbook's lifetime is every-firmware-release, not tied to 1.8.0.
- **H3 (docs/runbooks/):** clean home for future runbooks; no precedent in repo.
- **H4 (module docstring + `mcp/README.md` section):** recommended. Re-sync instructions adjacent to the code they describe.
- **Additional enforcement recommendation:** pin `ANALYZER_JS_VERSION = "v1.8.0"` as a module constant; log a startup warning on device-firmware mismatch (mDNS TXT `version=<git-tag>` per research.md; makes drift observable rather than silent).

### Bottom line

Full port is the right direction, but three ticket amendments are load-bearing:
1. Module path (relocate to `analysis/shot_analyzer.py`, avoid `diagnostics/` collision + skip the decomposability-spike theater).
2. Signature change (take raw `ShotData` or `(TransformedShot, profile_snapshot)` — not downsampled `TransformedShot` alone — see Open Questions §2).
3. Runbook home (`mcp/README.md` + module docstring; ditch `research/gaggimate-1-8-0-upgrade/runbook.md`).

## Adversarial Review

### Failure modes and edge cases

1. **Profile-data gap is a spec-blocker, not a spec-detail.** `calculateShotMetrics` reads `shot.profile.phases[].targets[]` — pressure/flow/volumetric/pumped stop conditions with operators + values. None of this is in `.slog` bytes (`parsers/shot.py:29-86`). Neither `ShotData.phases` nor `TransformedShot.phases` carries targets. Consequences: (a) offline fixture-replay cannot run DDSA at all — parity test runs against `.slog`s with no device; targets are not in golden JSONs; (b) shots older than ~30 days may be orphaned via 500KB purge + profile deletion; (c) the fixtures currently bundle profile name but not target arrays. **Fix requires either bundling `<shot_id>.profile.json` next to each fixture AND extending the signature, OR having the transformer surface per-phase targets.** See Open Questions §2.

2. **`classify_phase_exits(transformed_shot)` is algorithmically wrong.** `TransformedShot.phases[].samples` is downsampled to 25/phase (`transformers/shot.py:11`). JS operates on raw ~100ms samples; the 4-second predictive window needs ~40 raw samples but has only ~5–10 after downsampling. Regression rates computed over downsampled data will not match reference at any tolerance. **Port must consume `ShotData` (raw), not `TransformedShot`**, OR `TransformedShot` must gain a raw-sample accessor.

3. **1e-3 tolerance contract muddled for integer-bucketed outputs.** `detectAutoDelay` returns delay rounded to 50ms; `phaseTotalDelayMs` is `Math.round(sum/50)*50`; matchStep is integer-valued. At bucket boundaries a banker's-vs-js_round divergence flips classifications by ±50ms — not absorbable by 1e-3 tolerance. Per-field policy: integer fields `==`; floats `1e-3`.

4. **Banker's rounding compounds at bucket boundaries.** Sample computed `delayMs = 24.5`: JS `Math.round(24.5/50)*50 = 50*round(0.49) = 0`; Python `int(round(24.5)) = 24`. Flips classification entirely. Port MUST replace every `round()` with `js_round` and audit.

5. **`evt:status.bt` semantic flip propagates into `volumetric` vs `weight` classification.** 017 documented that 1.8.0 `bt` reflects `profile.isVolumetric()`. DDSA distinguishes `volumetric` and `weight` internal types (UI collapses both to "Weight Stop"). If fixture `.slog`s were captured on 1.8.0 but reference-JS is generated on a future firmware where semantics flip again, parity test pins classifications to the JS at capture time — nothing pins firmware version of the `.slog`. Cross-era replay (021's open investigation) becomes a DDSA trust prerequisite.

6. **JSON float serialization round-trips are not bit-stable.** `JSON.stringify(0.1+0.2) = "0.30000000000000004"` in JS; `json.dumps(0.3) = "0.3"` in Python. Parity must `json.loads` both sides and compare numerically. Existing `shot_fixture_walker.py:82` uses `expected != actual` (exact comparison) — will fail spuriously. Tolerance-aware walker required.

7. **Option (a) fails against production Vite bundles.** The device serves a minified bundle; `calculateShotMetrics` is not window-exposed. Real option (a) cost: (i) check out Gaggimate repo, (ii) run `npm install + vite dev`, (iii) proxy to a live device, (iv) load each fixture shot ID in a browser tab, (v) run console script, (vi) save. 1–2 hours of dev-environment setup + per-fixture replay time. **Ticket's "manual capture per fixture" is materially misleading.** Option (b) Node harness may actually be lower total-cost because it's automatable.

8. **`target: "power"` is undocumented in Pydantic.** `models/profile.py:10` declares `Literal["pressure", "flow"]`, but `coffees/choco-coffee-hacienda-la-papaya-typica-anaerobic/bloom-slide.json:23` uses `"target": "power"`. Fixture 249 (Tropical Bloom) likely contains a power-target phase. DDSA exit-reason vocabulary (`weight|volumetric|pressure|flow|pumped|time`) does not include `power`. If a power-target phase has no stop condition and exits by time, is that `time`/`duration` or unclassified? Reveals hidden coverage gap.

9. **Fixture coverage is fixture-starved for the parity contract.** 246/247/249 exercise 2 profile families (Adaptive v2, Tropical Bloom). Missing: pure flow-target profile (Turbo); pure power/bloom-only; decaf/dark-roast low-pressure profile; cross-era shot; scale-lost-permanently mid-shot shot. "Passes on 3 fixtures" is a weak correctness signal.

10. **Scale-lost-permanently flag — no structured audit.** 4 check sites + 2 fallback paths. Easy to miss one during port. Recommend a synthetic or real fixture that triggers scale-lost mid-shot and asserts each phase inherits sticky flag. 022's non-null pathology-survivor may or may not cover this.

11. **Deep-link can 404 under retention shifts.** 500KB free-space purge evicts shots between fetch and click. Skill output may carry a dead link. Either gate host reachability or phrase the output honestly ("Interactive chart (may be evicted under low-storage conditions): ...").

12. **`GAGGIMATE_HOST` default = `gaggimate.local`** — dead link when MCP runs offline/fixture-replay. Skill's trailing line is wrong when diagnosis is on a fixture-replayed shot. Suppress or gate.

13. **`str(int(shot_id))` fragile.** Prefer `shot_id.lstrip("0") or "0"`.

14. **Module name `phase_end_stop` tied to JS-internal coinage.** Firmware may rename the class in 1.9.0. Prefer descriptive name (`shot_analyzer.py`, `exit_classifier.py`).

15. **Test file cascade on module rename.** `test_diagnostics.py` becomes ambiguous if `diagnostics.py` → `diagnostics/connection.py`. Four patch sites break. Agent 1's "safest restructure" undercounts scope.

### Security concerns

16. **Browser console scripts on user's production Gaggimate UI.** Console has full DOM + credential access; copy-paste-from-runbook each time is riskier than a committed, reviewed script. Recommend checking in the capture script as source (`mcp/tests/fixtures/shots/capture_reference_js.js`) — reviewed once.

17. **Reference-JS sidecars checked into repo (private data repo in our case).** Careless script dumps may leak profile metadata (bean origin, notes) not intended to be public. Scope the script to DDSA output only.

18. **Cross-site / DNS rebinding on untrusted networks.** Low likelihood; runbook should scope "run only when connected to a trusted network."

### Assumptions that may not hold

19. **"Reference-JS JSON stays valid across firmware updates."** No — silently degrades. No enforcement mechanism proposed. Port correctness drifts from live device UI without anyone noticing.

20. **"Parity contract is meaningful on 3 fixtures."** Only 2 profile families; critical archetypes missing. See §9.

21. **"High-criticality port is better than graceful degradation."** Debatable. A silently-wrong port (missing profile data for orphaned shots, drift from new firmware) conveys false authority. High-criticality + soft-fail-when-uncertain may be more defensible than high-criticality + enforce-parity-or-bust.

22. **"Module path collision is the hardest problem."** No — missing profile data is. Module collision is a 15-minute rename + re-export.

### Recommended mitigations

- **Resolve profile-data problem pre-spec.** Decide: (a) snapshot full `profile` JSON into each fixture (`<shot_id>.profile.json` sibling); (b) change port signature to `classify_phase_exits(raw_shot: ShotData, profile_snapshot: ProfileData)`; (c) for prod `/diagnose`, degrade gracefully when profile is orphaned (`"exit_reason": "unknown", "reason": "profile_evicted"`).
- **Take `ShotData` (raw), not `TransformedShot`, as input.**
- **Per-field tolerance in parity test:** integer fields `==`, floats `1e-3`, allowlist for genuinely-divergent fields.
- **Implement `js_round` and lint-ban `round()` in DDSA module.** Test with `.5` boundary cases.
- **Pin `ANALYZER_JS_VERSION = "v1.8.0"` in module; startup warning on firmware mismatch.**
- **Reconsider Option (a) vs (b).** Re-present with Vite-bundle complication spelled out; if user still picks (a), document the dev-build-proxy procedure explicitly.
- **Move runbook to module docstring + `mcp/README.md` section.** Delete `research/gaggimate-1-8-0-upgrade/runbook.md` from AC.
- **Require flow-target-only profile fixture before accepting parity contract as meaningful.** Potentially block 018 acceptance on 022 fixture expansion.
- **Reframe AC to `graceful degradation on orphaned shots`.** Emit `"exit_reason": "unknown"` + audit note rather than silently wrong parity.
- **Rename module `analysis/shot_analyzer.py`.** Decouple from JS internal names.
- **Commit capture script as `capture_reference_js.js`.** Reviewed once, not copy-pasted.

## Open Questions

All open questions are resolved below. Any marked **deferred** have explicit rationale and are safe to carry into Spec without blocking transition.

### 1. Module path — **RESOLVED**

Relocate from `mcp/src/gaggimate_mcp/diagnostics/phase_end_stop.py` (collides with existing 318-line `diagnostics.py`) to `mcp/src/gaggimate_mcp/analysis/shot_analyzer.py`. New namespace, flat file, descriptive name decoupled from JS-internal "PhaseEndStop" coinage.

Sub-item **deferred to Spec**: 013 epic AC pins test filename as `mcp/tests/test_phase_end_stop_parity.py`. Spec will either preserve the 013-pinned name (decoupled from module rename) or update 013's reference — minor bookkeeping choice, not a blocking decision.

### 2. Profile-data gap + input signature — **RESOLVED (user decision)**

User chose: **Fixture profile sidecar + signature change.**
- Add `<shot_id>.profile.json` sidecar alongside each fixture at capture time (owned by 018's Implementation Prerequisite).
- Port signature: `classify_phase_exits(raw_shot: ShotData, profile_snapshot: ProfileData) -> list[PhaseExitReason]`.
- `TransformedShot` stays unchanged (small/AI-friendly); fixture-layer additions are deterministic.
- Spec must codify: the sidecar schema, the Python type for `ProfileData` (likely a new TypedDict mirroring the device's profile JSON subset DDSA reads), and the runtime path in `/diagnose` that fetches the live profile via `manage_profile(action="get")` before calling the port.

### 3. JS capture approach — **RESOLVED (user decision, supersedes Clarify Q1)**

User chose: **Switch to (b) Node.js harness.** (Overrides the option (a) answer during Clarify, which was based on incomplete cost info about Vite bundle minification.)
- Extract `AnalyzerService.js` into a Node harness that ingests `.slog` data offline; no browser / dev-build proxy required.
- Fully automatable across fixture refreshes and 022's future additions.
- Spec must codify: harness location (proposed `mcp/tests/fixtures/shots/harness/` — pure vendored `AnalyzerService.js` + Node entry script + `package.json`), invocation pattern (probably a `refresh_fixtures --reference-js` mode or separate CLI), and the `.slog → {shot, profile, settings} → results` pipeline.

### 4. Exit-reason vocabulary — **RESOLVED (Research recommendation, Spec to codify)**

Preserve JS internal values verbatim in `exit_reason_type`: `Literal["weight", "volumetric", "pressure", "flow", "pumped", "duration"]` (ticket's `"time"` is a documentation slip — Spec will update ticket AC). Parity test matches reference-JS trivially; skill layer formats `"duration"` to user-facing "Time Stop" at render time.

Sub-item **deferred to Spec**: `power`-target phase handling. Fixture 249 likely contains a power-target phase; `models/profile.py:10` Pydantic `Literal["pressure", "flow"]` already doesn't cover the real vocabulary. Not a 018-blocker — likely exits as `duration` (no stop target, hits phase duration) — Spec phase will verify against reference-JS on fixture 249 and document what DDSA classifies it as.

### 5. Runbook home — **RESOLVED**

Move from ticket's `research/gaggimate-1-8-0-upgrade/runbook.md` to: (a) module docstring in `mcp/src/gaggimate_mcp/analysis/shot_analyzer.py` (operational re-sync steps), plus (b) a section in `mcp/README.md` titled "Re-syncing shot-analyzer on firmware upgrades." Drop the original runbook path from AC.

Pin `ANALYZER_JS_VERSION = "v1.8.0"` as a module constant with a startup warning comparing against device mDNS TXT `version=<git-tag>` — converts silent drift into observable drift.

### 6. Parity test tolerance policy — **RESOLVED (Spec to codify)**

- Integer-typed fields (`delayMs`, matchStep, `phaseEstimatedScaleDelayMs`, bucket indices): exact `==`.
- Float fields: `math.isclose(a, b, abs_tol=1e-3, rel_tol=0)`.
- NaN-aware equality.
- Per-field allowlist for genuinely-divergent fields (initial empty; additions require runbook note).
- Extend `shot_fixture_walker.py` with `float_tol: float = 0.0` + `per_field_tol: dict[str, float]` params (preserving 016's exact-equality default), or write a parity-specific sibling walker. Spec will pick one.

### 7. Fixture coverage sufficiency — **RESOLVED (user decision)**

User chose: **Ship on 246/247/249, document gap.**
- 018 parity test runs against the current 3-fixture cohort.
- Runbook section `Known coverage gaps` enumerates missing archetypes (flow-target-only Turbo, pure power-target, decaf/dark-roast low-pressure, cross-era, scale-lost-permanently mid-shot).
- When 022 lands (or any new fixture is captured), 018's parity test auto-extends. Spec should make the test parametrize over `glob("*.slog")` with no hard-coded fixture list so growth is automatic.
- The false-confidence risk of 3-fixture parity is mitigated by the Q8 soft-fail runtime posture — a classification that would be wrong on an uncovered archetype produces `exit_reason="unknown"` at runtime rather than a silent wrong answer.

### 8. Graceful degradation posture — **RESOLVED (user decision)**

User chose: **Hard parity + runtime soft-fail.**
- Parity test: strict match, no "close enough" escape hatch. The test runs against representative fixtures with their `.profile.json` sidecars; if parity fails, the port is broken and the test fails hard.
- Runtime `/diagnose`: when the port cannot produce reliable output, emit `exit_reason_type="unknown"` per affected phase with an `unavailable_reason` field (`"profile_evicted" | "firmware_version_mismatch" | "insufficient_samples"`), and the skill renders "Exit reasons unavailable: <reason>" adjacent to the deep-link. Deep-link always renders (independent of DDSA success) so the user can still open the native analyzer.
- Spec must codify the `PhaseExitReason` TypedDict to include `exit_reason_type: Literal[..., "unknown"]` + `Optional[unavailable_reason: str]`.

### 9. Deep-link retention + offline host handling — **deferred to Spec implementation**

Low-stakes copy + guard decision. Spec will pin: (a) default wording that acknowledges retention ("Interactive chart (may be evicted under low storage): ..."); (b) suppression logic when `config.host == "gaggimate.local"` and device is unreachable OR when the shot is fixture-replayed (detectable via shot origin metadata). Deferred because it doesn't block correctness — it's output-formatting polish that Spec's structured interview will nail down with real wording.

### 10. 021 cross-era dependency — **deferred as follow-up, non-blocking**

021 (open, high) investigates BLE precision drift across 1.7.3/1.8.0. 018 targets 1.8.0-only fixtures + 1.8.0 JS source, so pre-1.8.0 shots are out of scope by construction. If 021 later surfaces LSB drift, 018's per-field allowlist (Q6) absorbs it. No 018-blocking action required now; Spec should note this as a follow-up risk only.
