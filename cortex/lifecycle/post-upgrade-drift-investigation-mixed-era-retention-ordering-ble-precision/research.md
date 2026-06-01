# Research: Post-upgrade drift investigation (mixed-era, retention ordering, BLE precision)

Investigation-only spike (ticket 021, parent epic 013). Three empirical sub-questions to answer and append to `research/gaggimate-1-8-0-upgrade/verification-notes.md`:

- **(a)** Mixed-era `.slog` shot compatibility — pre- vs. post-upgrade transformed output diff.
- **(b)** Shot-history retention ordering + purge-order invariants — `/api/history/index.bin` observation + source reading.
- **(c)** BLE-precision round-trip float drift — raw parser output comparison across firmware versions.

Output verdict vocabulary for each sub-question: `drift detected` | `no drift` | `unable to test`. If `drift detected`, spawn a follow-up ticket (parser version-gating or fixture re-curation); this ticket is investigation-only.

## Codebase Analysis

### Files that will be touched

**Primary deliverable (append-only):**
- `research/gaggimate-1-8-0-upgrade/verification-notes.md` — three new dated sections, one per sub-question, following the 2026-04-18 / 2026-04-19 template.

**No checked-in scripts expected.** Any ad-hoc comparison code for (c) lives in the lifecycle scratch dir (`lifecycle/post-upgrade-drift-investigation-mixed-era-retention-ordering-ble-precision/`), not under `mcp/src/`. No precedent for committed one-shot analysis scripts.

**Possible new fixtures** if a pre-upgrade shot surfaces: `mcp/tests/fixtures/shots/<id>.slog` + `.golden.json` via `python -m gaggimate_mcp.tools.refresh_fixtures <id> --fetch`, mirrored to `{private-data-repo}/mcp-data/shot-archive/<id>.slog`. Out of scope for the spike itself (AC: investigation-only).

### Parser + transformer pipeline

- `mcp/src/gaggimate_mcp/parsers/shot.py` → `parse_binary_shot(data: bytes, shot_id: str) -> ShotData`.
- `mcp/src/gaggimate_mcp/transformers/shot.py` → `transform_shot_for_ai(shot: ShotData) -> TransformedShot`.
- **Raw parser sample fields** (BLE-precision candidates for (c)): `t`, `tt`, `ct`, `tp`, `cp`, `fl`, `tf`, `pf`, `vf`, `v`, `ev`, `pr`, `systemInfo` (bit-packed).
- **Scaling factors** (quantization floor; structurally bounds observable drift): `TEMP_SCALE=10`, `PRESSURE_SCALE=10`, `FLOW_SCALE=100`, `WEIGHT_SCALE=10`, `RESISTANCE_SCALE=100`. Any cross-era drift below `1/scale` is structurally impossible — parser divides int16/uint16 by scale.
- **Transformer output** pre-rounded to 1 dp (summary stats) / 2 dp (RMSE, resistance) per byte-stability contract. Sub-LSB drift at the raw parser level will not surface in transformed output.

### Index parser and HTTP client

- `mcp/src/gaggimate_mcp/parsers/index.py` → `parse_binary_index(data: bytes) -> IndexData`. Preserves on-wire order. `index_to_shot_list()` sorts newest-first by timestamp — use `IndexData.entries` directly for on-wire observation.
- Flag bits: `SHOT_FLAG_COMPLETED=0x01`, `SHOT_FLAG_DELETED=0x02`, `SHOT_FLAG_HAS_NOTES=0x04`. `header.next_id` — highest-ever shot id; `max(entry.id) < header.next_id` implies a purge has occurred.
- `mcp/src/gaggimate_mcp/api/http.py` → `GaggimateHTTPClient.fetch_shot_index(limit, offset)` (sorts newest-first) and `fetch_shot(shot_id)` (single shot pull; returns raw bytes). For raw on-wire order, bypass `index_to_shot_list()` and call `parse_binary_index(binary_data)` directly.

### Fixture harness (ticket 016 — done)

- `mcp/tests/shot_fixture_walker.py` → `compare(expected, actual, max_mismatches=10) -> list[Mismatch]`. Walker is directly reusable for **(a)** cross-fixture comparison (raise `max_mismatches`). **Wrong tool for (c)** — exact-equality walker doesn't compute per-field deltas; ad-hoc statistical comparison must be written.
- `mcp/tests/test_shot_regression.py` — invocation pattern: `parse_binary_shot(slog_path.read_bytes(), slog_path.stem.zfill(6))`.
- `mcp/tests/fixtures/shots/{246,247,249}.slog` + `.golden.json` — **all post-upgrade** (see 016 README: Shot 170 "was evicted by the 1.8.0 free-space purge before capture"). `{private_repo}/mcp-data/shot-archive/` mirrors the same three — no pre-upgrade fixtures in either location.
- `mcp/src/gaggimate_mcp/tools/refresh_fixtures.py` → `--fetch` mode pulls a `.slog` by id. **No read-only mode** — always overwrites `tests/fixtures/shots/<id>.{slog,golden.json}`. For one-shot candidate inspection use `GaggimateHTTPClient.fetch_shot()` directly.

### End-to-end invocation patterns

**(a) cross-era transform diff:**
```python
pre = transform_shot_for_ai(parse_binary_shot(pre_slog_path.read_bytes(), pre_slog_path.stem.zfill(6)))
post = transform_shot_for_ai(parse_binary_shot(post_slog_path.read_bytes(), post_slog_path.stem.zfill(6)))
mismatches = compare(pre, post, max_mismatches=1000)
```

**(b) index-order observation:**
```python
binary = await fetch_index_bin(base_url)   # copy http.py:55-77
index_data = parse_binary_index(binary)
for entry in index_data.entries:           # raw on-wire order
    ...
orphaned = [e.id for e in index_data.entries if not slog_exists(e.id)]
```

**(c) raw-parser precision diff (ad-hoc tooling required):**
- Iterate `ShotData.samples` across two aligned shots (by sample-index).
- Per-field subtract, aggregate to `(mean, max_abs, stddev, count_nonzero)`.
- No existing utility — ephemeral script in the lifecycle scratch dir.
- Noise-floor reference per field: `1/scale` (0.1 bar, 0.01 ml/s, 0.1 g, 0.01 ohm). Sub-quantum drift is structurally impossible.

### Verification-notes.md section template (observed from prior entries)

```markdown
## YYYY-MM-DD — <subject>

**Method**: <hybrid / live / source-code>, <retrieval specifics>

### Step N — <label>  (or **<Category>**)

<findings, with raw data in ```json``` fenced blocks>

**Conclusion** (or **Verdict**): <decision>

---
```

Ticket 021's AC layers on: per sub-question section, ending in one of `drift detected` / `no drift` / `unable to test`.

### Conventions to follow

1. `verification-notes.md` append-only; dated headers `## YYYY-MM-DD — <subject>`.
2. `**Method**:` line must be explicit — `hybrid`, `live`, or `source-code` — matching 2026-04-18 precedent.
3. Raw comparison data lives in fenced code blocks (not just summary prose).
4. Byte-stability contract on goldens — never hand-edit; regenerate via `refresh_fixtures`.
5. Shot-id padding: **padded (6-digit)** for device URLs + parsers; unpadded for WS `notes` endpoint.
6. `verification-notes.md` is in the main repo — auto-commit policy does NOT apply (that rule targets `{private-data-repo}`-symlinked paths only).
7. Shot-archive mirror: any new `.slog` captured must also land in `{private-data-repo}/mcp-data/shot-archive/`.
8. Walker exact-equality is load-bearing — no float tolerance introduced.

### Known gaps / ad-hoc tooling required

- **No per-field statistical comparison utility.** Sub-question (c) requires an ephemeral script for per-field delta aggregation across aligned sample lists.
- **No pre-upgrade `.slog` in repo or private archive.** Sub-questions (a) and (c) are likely `unable to test` unless an earlier-era shot can be sourced (device, Time Machine, private-repo git history — see Open Questions).
- **`refresh_fixtures` has no read-only mode.** Candidate-shot pulls require direct `GaggimateHTTPClient.fetch_shot()` invocation.

## Web Research

**Tools used**: `gh api` (v1.7.3 and v1.8.0 source blobs read directly), WebSearch, WebFetch (cppreference returned 403; inferred from WG21 P2587R1 and std-proposals discussion). All firmware citations are tag-pinned, not `main`-branch.

### Firmware source diff: v1.7.3 → v1.8.0

**`.slog` format (`src/display/models/shot_log_format.h`) — byte-identical across the two tags.** `diff` is empty. `SHOT_LOG_MAGIC = 0x544F4853`, `SHOT_LOG_VERSION = 5`, `SHOT_LOG_HEADER_SIZE = 512`, `SHOT_LOG_SAMPLE_SIZE = 26`, `SHOT_LOG_FIELDS_MASK_ALL = 0x1FFF`, phase-transition struct = 29 bytes × 12 — all bit-identical. (⚠️ This is the header + sample-layout level; does NOT rule out internal semantic shifts in the writer. See Adversarial §1.)

**Samples are scaled integers, not floats.** `ShotLogSample` is 13 × uint16/int16 fields scaled at ingest via `encodeUnsigned`/`encodeSigned` with `+0.5` half-up rounding. Quantization scales (0.1 bar, 0.01 ml/s, 0.1 g, 0.01 ohm) are far coarser than any ULP-level drift from `std::to_string`→`atof` (~1.2e-7 for binary32). **Cited**: `src/display/plugins/ShotHistoryPlugin.cpp:26-60` at v1.8.0. (⚠️ Line-number citations are tag-pinned but not SHA-pinned — see Adversarial §8.)

**Parser is version- and fieldsMask-driven** (not magic-cutoff-driven). `web/src/pages/ShotHistory/parseBinaryShot.js` branches on `version <= 4` vs `>= 5` and builds field layout dynamically from `fieldsMask`. Both 1.7.3 and 1.8.0 produce `version=5, mask=0x1FFF` files — fully interchangeable at the sample-payload level.

### BLE wire-format change — real but orthogonal to `.slog`

- **1.7.3**: `snprintf(str, sizeof(str), "%d,%d,%.1f,%.1f,%d,%.2f,%.2f", ...)` — fixed 1–2 decimal places per field. Cited: `lib/NimBLEComm/src/NimBLEClientController.cpp` at v1.7.3.
- **1.8.0**: `inline std::string float_to_string(float f) { return std::to_string(std::round(f * 1000.0f) / 1000.0f); }` at `lib/NimBLEComm/src/NimBLEComm.h`. Pre-rounds to 3 decimals, then `std::to_string` emits `%f` format (6 digits AFTER decimal, NOT 6 significant — per ISO C++ WG21 P2587R1). Net wire: `"7.500000"` instead of `"7.50"`.
- **Parse path still uses `String::toFloat()` (wraps `strtod`).** Round-trip of 3-decimal-rounded values gives bit-exact recovery for binary32-representable values at milli scale; may drift ~1.2e-7 ULP for non-exact values (e.g., 9.3).
- **This drift cannot propagate into `.slog`** because `encodeUnsigned(value * scale + 0.5)` quantizes at 0.1 bar / 0.01 ml/s — 5+ orders of magnitude coarser than 1.2e-7 ULP. (⚠️ Claim has gaps — see Adversarial §2 on scale-BLE path and §6 on quantum-boundary concentration.)

**PR #609 (buffer overread fix)**: 1.7.3 cast non-null-terminated `pData` directly to `char*` → passed to `atof`/`atoi`/`String()`, reading past buffer end (UB). 1.8.0 constructs `std::string rawData((char*)pData, length)` first. Produces **malformed parses** on truncated payloads, not precision drift. If pre-1.8.0 shots show sporadic spurious spikes in live-event-derived data that aren't in `.slog`, this is the likely culprit.

### Retention + purge (question b)

- **1.7.3**: count-based cap `MAX_HISTORY_ENTRIES = 100`. Sort filenames lexical ascending, remove `entries[0..size-MAX]`. **Only `.slog` removed — `.json` sidecar orphaned.**
- **1.8.0**: free-space floor `MIN_FREE_SPACE_BYTES = 500 * 1024` (500 KB). If `getFreeSpace() > MIN` return early; else collect `.slog` files, sort lexically ascending, loop: remove oldest `.slog`, call `markIndexDeleted(shotId)`, remove matching `.json`. Loop condition: `for (size_t i = 0; i < slogFiles.size() && getFreeSpace() <= MIN_FREE_SPACE_BYTES; i++)`.
- **Purge-order invariant: strict FIFO by shot id.** Filenames are `padId(id, 6)` → lexical sort ≡ numeric id sort ≡ creation order. Deterministic, filesystem-independent at the firmware level. (⚠️ SPIFFS GC timing and directory iteration stability caveats — see Adversarial §4.)
- **Storage backend: SPIFFS or SD_MMC, not LittleFS.** Chosen via `controller->isSDCard()`. Ticket's LittleFS framing is incorrect.
- **Index.bin write order**: append-at-EOF in id order (physical file order = append order). WebUI `parseBinaryIndex.js:130` display-sorts newest-first by timestamp. So `index.bin` on-wire order ≠ display order.

### Prior art for binary-format cross-version drift detection

- **Golden-output differential testing** — capture canonical input, run old vs new through both, byte-diff output. Tractable here because samples are integer-quantized.
- **Checksum/fingerprint overlap** — rolling hash over sample payload (skipping header non-deterministic fields like `startEpoch`).
- **Field-semantic assertions beyond version byte** — `parseBinaryShot.js:169-172` already validates `deviceSampleSize !== expectedSampleSize` at read time, catching field-count shifts even when `version` stays at 5.

### Filesystem reference (ESP32)

- **SPIFFS**: `unlink` is immediate at logical level; physical reclamation via GC during subsequent writes. No application-visible deterministic eviction order.
- **LittleFS** (not used by Gaggimate): compaction happens lazily; no documented deterministic eviction-by-creation-order contract.
- Firmware-controlled eviction dominates — FS quirks matter only during power-loss (see Adversarial §4).

### Key URLs

- https://github.com/jniebuhr/gaggimate/compare/v1.7.3...v1.8.0 (58 commits)
- https://github.com/jniebuhr/gaggimate/pull/604 (async rebuild)
- https://github.com/jniebuhr/gaggimate/pull/605 (capacity-based history + orphan cleanup)
- https://github.com/jniebuhr/gaggimate/pull/609 (BLE buffer overread fix)

## Requirements & Constraints

### No `requirements/` directory

The project encodes behavioral constraints in `CLAUDE.md`, `MEMORY.md`, and the parent epic's research artifacts. Relevant extracts:

### CLAUDE.md — firmware 1.8.0 semantic traps (already documented)

- **`evt:status.bt` semantic flip**: not this spike's scope.
- **Shot history retention shift** (`MAX_HISTORY_ENTRIES = 100` → `MIN_FREE_SPACE_BYTES = 500 KB`, companion `.json` also purged): **this is exactly the invariant (b) must test**. The spike's verification is *in addition to* the trap documentation; it doesn't replace it. Ticket 017 closed this doc surface; ticket 021 provides empirical confirmation.

### CLAUDE.md — Important Notes

- **Weight anomalies**: BT scale artifacts are common. Estimate dose out via `total_volume_ml × 0.82` or last stable sample. Relevant to interpreting any apparent cross-era weight deltas — could be scale artifact, not firmware drift.
- **Auto-commit policy**: `verification-notes.md` is in main repo, not private-repo-symlinked. Policy does NOT fire for this spike's write. Normal `/commit` skill applies.
- **Reading from `{private_repo}/mcp-data/shot-archive/`** is safe — one-way mirror populated by `refresh_fixtures`; no write-back concern.

### MEMORY.md lessons (drift-interpretation hazards)

- **End-of-shot samples are artifacts.** Pump-stopped pressure/temp readings are residual, not extraction data. Don't diagnose from last 1–2 samples. Relevant to (c): systematic near-end drift may be artifact, not firmware change.
- **Never ask the user for cup weight.** ±2 g BT scale estimate is fine.
- **Flow meter during bloom ≠ channeling.** `time_to_first_drip_s` is flow-meter-based; reports early. Use first cup-weight appearance instead.

### verification-notes.md template (from 2026-04-18 / 2026-04-19)

Same template documented under Codebase Analysis. Key convention: `**Method**:` line should declare `hybrid` / `live` / `source-code`. 2026-04-18 precedent for sub-question (c) was **hybrid** (source-code + live round-trip). Source-only reasoning for a "no drift" claim would break this precedent (see Adversarial §3).

### research.md + decomposed.md — Decomposition lineage

- research.md P3 items #8/#9/#10 → map to 021 (a)/(b)/(c). (Ticket body cites "#5/#6/#7" which is an off-by-numbering error relative to the current research.md layout; the three topics match.)
- decomposed.md: old ticket 022 merged into 021 question (c). Archived at `backlog/archive/022-ble-precision-round-trip-investigation.md`.
- decomposed.md AC hardening: "Flagged pre-upgrade fixture-availability challenge in 021 with explicit fallback (private data repo history, or honestly declaring the test unrunnable)."

### 016 fixture README (blocker satisfied, pre-upgrade gap confirmed)

- Shot 170 (the named pre-upgrade candidate) "was evicted by the 1.8.0 free-space purge before capture." Same mechanism (b) is testing.
- Decline-era shots from Chelchele "are long-gone."
- Archive at `{private-data-repo}/mcp-data/shot-archive/` mirrors `mcp/tests/fixtures/shots/` — contains only 246/247/249 (all post-upgrade). Confirmed via direct `ls`.
- 016 provides: parser/transformer methodology + golden-output regression mechanism + walker for cross-fixture diff. Does NOT provide pre-upgrade shot binaries.

### Ticket 021 AC constraints

- Investigation-only: no code changes, no version-gating, no fixture recapture.
- Single deliverable: three dated sections in `verification-notes.md`.
- Each sub-question: question restated, method, raw data/observation, verdict ∈ {`drift detected`, `no drift`, `unable to test`}.
- "Unable to test" is a legitimate terminal state for (a)/(c) when no pre-upgrade fixture is obtainable, and for (b) when no eviction occurs in the observation window.
- `drift detected` verdict triggers follow-up ticket spawn (parser version-gating or fixture re-curation); out of scope for 021.
- No requirement to simulate space pressure for (b) ("Do not require artificial space-pressure simulation").

### Exact-equality contract (016)

Transformer pre-rounds at 1 dp / 2 dp, so any drift below the rounding threshold cannot surface in transformed output. Sub-question (c) must diff **raw parser output**, not transformed output, to see ULP-level drift.

## Tradeoffs & Alternatives

Five alternatives considered for how to execute the spike. The ticket's prescribed approach (empirical pre/post diff) is one option; others surfaced because confirmed fixture unavailability changes the cost/value calculus.

### Alternative A — Empirical pre/post diff (ticket's prescribed approach)

Pull pre-upgrade and post-upgrade `.slog`, run both through parser+transformer, diff field-by-field. Separate raw-parser diff (c) from transformed diff (a).

**Prerequisites**: at least one pre-upgrade `.slog`. Confirmed unavailable in repo and private archive.

**Pros**: answers all three questions end-to-end if a fixture appears. Catches runtime-only effects that source reading misses (compiler rounding, accumulated state, platform float semantics). Produces durable golden pair.

**Cons**: collapses to "unable to test" on (a)/(c) under confirmed fixture unavailability. N=1 cannot separate cross-era drift from normal shot-to-shot variance. Statistical methodology for (c) unspecified; parser noise floor unestablished.

**Failure modes**: false-positive drift claim from N=1; silent miss on profile patterns absent from the single fixture.

### Alternative B — Firmware-source-code reasoning (fixture-independent)

Diff v1.7.3 vs v1.8.0 source directly. Answer each sub-question from source:
- (a) Grep the shot-log writer for semantic shifts; confirm sample encoding byte-identical.
- (b) Read retention + index-write paths; ordering provable from source.
- (c) Trace whether `.slog` values pass through any BLE-serialized string intermediate (`atof`/`parseFloat`). If no such path exists, drift is provably zero.

**Prerequisites**: read-level C++ competence; access to both tags on GitHub (public).

**Pros**: fixture-independent. Answers in hours. Produces durable citations. Separates "no drift path exists" from "drift path exists but bounded" — stronger than single-fixture diff.

**Cons**: may miss subtle runtime-only effects (int-to-float-to-int via helper functions, compiler intrinsics, accumulated-state drift). Breaks the 2026-04-18 `verification-notes.md` hybrid-evidence precedent if used source-only. Does not produce regression fixtures.

**Failure modes**: missed code path (e.g., rarely-traversed BLE-receive branch feeding sensor-fusion state); surface-level confidence that runtime falsifies. Line-number citations may rot if not SHA-pinned.

### Alternative C — Hybrid (source-code primary + minimal empirical corroboration)

Source analysis as the answer mechanism; empirical signals added only where cheap and independent.

**Minimum empirical adds:**
1. **(b) live observation**: one `/api/history/index.bin` fetch on the user's device; record on-wire ordering, compare `max(entry.id)` vs `header.next_id`, check for orphaned entries (entries whose `.slog` 404s). Directly observable; corroborates or falsifies source prediction.
2. **(a)/(c) same-firmware baseline**: run 246/247/249 through the pipeline pairwise; document same-era variance as parser-noise-floor frame of reference for any future pre-upgrade fixture. Caveat: 247 is truncated BT-artifact candidate — confounded.
3. **Skip single-shot cross-era diff** even if a fixture surfaces — N=1 adds negligible evidence beyond source analysis.

**Pros**: highest information-per-hour. Matches 2026-04-18 hybrid precedent. Source answers structural questions; live device call closes (b) definitively.

**Cons**: requires judgment about what to check empirically; easy to over-scope.

### Alternative D — Noise-floor baseline from same-firmware back-to-back shots

Use 246 vs. 247 (both post-upgrade, nominally similar) to characterize parser's own variance floor. Produces a bar that any future cross-era claim must exceed.

**Pros**: fills known-unknown #3 (noise floor) even with zero pre-upgrade fixtures. Establishes methodology for (c)'s unspecified threshold.

**Cons**: doesn't test drift — characterizes variance. Only useful if pre-upgrade fixture eventually appears. 246/247 structurally dissimilar (different durations, profile-phase counts) so the baseline mixes parser variance with extraction variance.

### Alternative E — Artificial fixture construction (synthetic pre-upgrade `.slog`)

Re-encode a post-upgrade sample stream using 1.7.3's BLE formatting assumption, round-tripped through `atof`, then re-encode to `.slog`.

**Cons**: tests the transformer, not the firmware. Requires writing a `.slog` encoder (non-trivial; must be verified byte-identical to firmware output). Answers only (c), not (a) or (b). Dominated by Alternative B.

### Alternative F — Explicit deferral with trigger

Close (a)/(c) now as "unable to test — no pre-upgrade fixture verified unavailable." Complete (b) in full. Add a trigger mechanism for pre-upgrade capture before next firmware upgrade.

**Pros**: honest given confirmed fixture unavailability. Preserves (b) value. Closes recurring hazard (same problem would bite next upgrade).

**Cons**: leaves (a)/(c) open. Doesn't exploit source-reading avenue. Partial-F is dominated by combining with B/C.

**Failure mode**: trigger mechanism not enforced → deferral becomes permanent. Backlog-ticket or CLAUDE.md reminder both have known drift-to-forget failure modes (see Adversarial §7 for a continuous-snapshot alternative).

### Recommended approach

**Hybrid source-code + minimal empirical + partial-F trigger**, specifically:

1. **(a) mixed-era**: source-first via v1.7.3↔v1.8.0 diff of `shot_log_format.h` + shot-log writer. Cite SHA-pinned permalinks (not tag names — tags can be re-pointed). Plus: audit the 430 bytes of header + 348 bytes of phase-transition struct that the Python parser *doesn't* decode, to ensure no float bit-patterns lurk in unexamined regions.
2. **(b) retention**: source reading of eviction + index writer + **live `/api/history/index.bin` fetch** during investigation. Record on-wire order, orphan count, `max(entry.id)` vs `header.next_id` delta. Also record same-era variance across all currently-available on-device shots (likely 20–50 shots exist post-upgrade, not just the 3 fixtures — see Adversarial §5).
3. **(c) BLE precision**: structural reasoning via source (no `.slog` float bytes → no round-trip drift possible), explicitly extended to the **BT-scale BLE deserialization path** (Adversarial §2). This is the stronger question — display-BLE is one wire; scale-BLE feeds `v`/`vf` and was not analyzed by Agents 1–4.
4. **Pre-upgrade fixture trigger**: recommend (in the spike, not file) a continuous-archive mechanism — a periodic `bin/pre-upgrade-snapshot.sh` or launchd job mirroring device shots into `mcp-data/shot-archive/`. Backlog-ticket-as-reminder is known to drift; continuous capture is robust.

**Rationale**: empirical pre/post diff (Alt A) collapses on confirmed fixture unavailability. Source-code analysis (Alt B) gives stronger answers but breaks the hybrid precedent if used alone. The hybrid (Alt C) matches 2026-04-18 methodology and costs ~1 afternoon, not days. Question (b) is answerable today with one HTTP call. Questions (a) and (c) are answerable from source if the adversarial review's gaps (phase-transition struct, BT-scale BLE path, SHA-pinning) are closed.

## Adversarial Review

Agents 1–4 converged on "hybrid source-code + minimal empirical" with confidence. The adversarial pass surfaced eight failure modes.

### 1. Phase-transition struct + header regions are partially unread

- Python parser decodes only `sample_index`, `phase_number`, and 25-byte name from each 29-byte transition struct (`parsers/shot.py:181-192`). Remaining bytes are untouched.
- Header bytes 28–108 and 108–458 are also partially unread. ~350 bytes of header unexamined.
- If v1.8.0 repurposed a reserved region for a BLE-derived float target (exit-pressure target, phase-transition timestamp, stop-condition value), current fixtures would not detect it — parser skips the bytes, so golden outputs are silently unchanged.
- **"Byte-identical format header"** (from Web research) is the sample-layout level, not the full `.slog` content.
- **Mitigation**: audit every byte of the header + phase-transition struct at both tags before concluding "no drift."

### 2. BT-scale BLE deserialization path was NOT analyzed

- The user has a BT-scale-enabled Gaggimate Pro. Weight samples travel scale BLE → firmware → `encodeUnsigned` → `.slog` `v`/`vf` fields.
- Web research traced display-BLE (controller→display) but not scale-BLE (scale→controller).
- PR #609 (`atof`→`std::string` fix) touches a BLE read path. Whether that path also covers scale-BLE is unverified.
- Profile-target values (`tp`, `tt`, `tf`) originate from the active profile object. If profile-target-set via WS/BLE writes a float first (then `encodeUnsigned` quantizes), the float itself carries 1.8.0's new BLE rounding.
- Quantum-boundary values are exactly where discretization bias concentrates — "below scaling quanta" is correct at the mean but can flip sign at boundaries.
- **Mitigation**: extend (c) to explicitly cover scale-BLE + profile-target BLE paths.

### 3. Source-only reasoning breaks the hybrid evidence precedent

- 2026-04-18 `verification-notes.md` entry used **hybrid** (source + live round-trip). Going source-only on (c) weakens the evidence class below the established floor.
- **Mitigation**: require SHA-pinned source citation + at least one live signal per sub-question. Source alone should not be admissible for "no drift" claims.
- Live signal for (b) is cheap (one HTTP call). Same-firmware variance across available post-upgrade shots is cheap (~20 min). No reason to defer these.

### 4. SPIFFS GC + power-loss + directory-iteration failure modes

- SPIFFS `unlink` is immediate logically; physical reclamation via GC. If `getFreeSpace()` polls physical free space, the eviction loop may terminate early (enough free) even though the unlinks haven't reclaimed — or loop further than needed. Unknown whether firmware queries logical or physical free space.
- SD_MMC timing: contention with next shot write during eviction can leave FS in intermediate state.
- Power loss during eviction: `.slog` deleted but `.json` sidecar not yet deleted (or vice versa); or index entry updated but files not deleted. 1.8.0's async rebuild (PR #604, `evt:history-rebuild-progress`) may be the recovery path, but its mid-rebuild consistency is not described.
- Directory iteration order on SPIFFS is not guaranteed stable. The firmware's "lexical sort" depends on the *reader* sorting — confirm the eviction loop explicitly sorts, not iterates in FS-returned order.
- **Mitigation**: source-level confirmation of (1) `getFreeSpace()` semantics, (2) explicit sort in eviction loop, (3) rebuild consistency contract.

### 5. "Only 246/247/249" survey was too narrow

- Fresh on-device shots accumulated since 2026-04-01 upgrade (~19 days of normal use → likely 20–50 shots). Same-era variance pool larger than N=3 is available today.
- `/api/history/index.bin` entries whose `.slog` 404s are "silently orphaned" references — CLAUDE.md's trap note warns about these. Their timestamps would confirm/deny whether any pre-upgrade shots crossed the 1.8.0 boundary.
- Unexplored archive sources: Time Machine, iCloud Drive backup of `~/Workspaces/gaggimate-barista-data/`, `git log --all -- shot-archive/` in the private data repo (earlier commits may have referenced now-deleted shots), device's own flash backup if one was taken before firmware flash.
- **Mitigation**: pull current `/api/history/index.bin`; compute same-era variance across all available post-upgrade shots; run `git log --all -- shot-archive/` in the private repo.

### 6. Structural drift surfaces beyond format headers

- **Compiler / PlatformIO toolchain**: IEEE-754 arithmetic is deterministic per expression, but compiler flags (FMA fusion, `-ffast-math`-like) can shift behavior. Check `platformio.ini` diff v1.7.3↔v1.8.0.
- **Sensor sampling / aggregation rate**: if 1.8.0 changed upstream pressure/temp sampling rate or averaging window, values fed into `encodeUnsigned` differ even with identical format. Real possibility from "stability / internal fixes" bucket.
- **Rounding mode**: firmware uses half-up (`+0.5`); Python transformer uses banker's rounding. Same-era fixtures stable because boundary values don't change — if 1.8.0 BLE wire introduced a new quantum boundary at the firmware-rounding boundary for ½-unit values, parser output could differ at boundary values.
- **Mitigation**: include `platformio.ini` + sampling-path audit in source review.

### 7. Pre-upgrade-capture trigger has no enforcement mechanism

- Backlog-ticket reminder ages out silently.
- CLAUDE.md checklist entry relies on user narrating upgrades.
- Robust option: `bin/pre-upgrade-snapshot.sh` + cron/launchd periodic archive (not upgrade-gated). Makes the problem structurally impossible, not reminder-dependent.
- **Mitigation**: if spike recommends a capture trigger, recommend the continuous-archive mechanism, not a ticket.

### 8. Agent line-number citations are tag-pinned, not SHA-pinned

- Web research cited specific line numbers at v1.7.3 / v1.8.0 tag URLs. Tags can be re-pointed. If a tag moves (rare but possible), citations rot.
- `gh api` returns a specific blob SHA for each file request; include that SHA in the verification artifact.
- Existing 2026-04-18 entry cites blob URLs without SHAs — pre-existing pattern issue.
- **Mitigation**: pin citations to commit SHAs (single provenance line per entry: "v1.8.0 tag = commit `<sha>` retrieved 2026-04-20").

## Open Questions

These are the answerable-by-investigation gaps surfaced by the adversarial review. Each is **deferred** to the Spec phase or to the spike execution itself, with rationale below. Research passes the exit gate with no questions blocking the Research → Spec transition.

1. **Phase-transition struct audit** — do the 29-byte transition structs at v1.7.3 and v1.8.0 contain any float bit-patterns in regions the Python parser doesn't decode? [Adversarial §1]
   **Deferred**: this is a source-inspection task the spike will execute as part of (a)'s methodology; Spec should bake it into the acceptance criteria but the answer itself requires reading firmware source, not a user decision.
2. **Header-region audit** — do header bytes 28–458 at both tags contain any BLE-derived float bit-patterns? [Adversarial §1]
   **Deferred**: same class as Q1 — spike-execution task; Spec encodes the requirement.
3. **BT-scale BLE path** — does the scale-to-controller BLE deserialization in 1.8.0 introduce any `atof`/`std::to_string` round-trip that affects `.slog` `v`/`vf` values? [Adversarial §2]
   **Deferred**: spike-execution task for (c); Spec encodes the requirement to explicitly cover scale-BLE alongside display-BLE.
4. **Profile-target BLE path** — when a profile target value is set via WS/BLE, does it pass through the new `float_to_string`/`toFloat` round-trip before landing in `.slog` phase-transition or sample fields? [Adversarial §2]
   **Deferred**: same class as Q3.
5. **Evidence-class floor** — does the verification-notes.md hybrid precedent require at least one live signal per sub-question, or is source-only acceptable for (c)? [Adversarial §3]
   **Deferred to Spec**: this is a methodology constraint best resolved with the user during the Spec structured interview — it changes AC wording.
6. **SPIFFS/SD_MMC failure modes** — what does `getFreeSpace()` poll (logical vs physical)? Does the eviction loop explicitly sort? What is the mid-rebuild consistency contract? [Adversarial §4]
   **Deferred**: spike-execution task under (b); Spec encodes the requirement.
7. **Fresh on-device shots** — how many post-upgrade shots currently live on the device, and what is the same-era parser variance across that pool? [Adversarial §5]
   **Deferred**: spike-execution task; answerable only when the spike runs against the live device.
8. **Orphan index entries** — does the current `/api/history/index.bin` contain entries whose `.slog` 404s? [Adversarial §5]
   **Deferred**: spike-execution task under (b).
9. **Private-repo git history** — does `git log --all -- shot-archive/` reference any `.slog` that was added and later removed, possibly pre-upgrade? [Adversarial §5]
   **Deferred**: spike-execution task; mechanical one-command check during the spike.
10. **Toolchain drift** — does `platformio.ini` diff between v1.7.3 and v1.8.0 show any compiler-flag or framework-version change that could shift float arithmetic? [Adversarial §6]
    **Deferred**: spike-execution task; answerable from source diff.
11. **Sensor-path audit** — is the upstream sensor sampling / aggregation rate identical between versions? [Adversarial §6]
    **Deferred**: spike-execution task; source-diff answerable.
12. **Pre-upgrade-capture trigger** — if (a)/(c) land on "unable to test," what mechanism prevents the next upgrade from reproducing the same gap — backlog ticket, CLAUDE.md checklist, or continuous-snapshot script? [Adversarial §7]
    **Deferred to Spec**: this is a scope decision about what the spike *recommends* in its verdict section (implementation of the mechanism is out of scope per 021's AC). User input needed on recommendation form.
13. **SHA-pinned citations** — require commit-SHA pins in verification-notes.md, and retroactively pin the 2026-04-18 entry? [Adversarial §8]
    **Deferred to Spec**: a convention decision the user should weigh in on; affects both this spike's output and a retroactive edit.
14. **Statistical methodology for (c)** — when pre/post empirical comparison is possible, what aggregation is the "systematic magnitude" signal — mean delta per field, max |delta|, stddev, paired-sample test, distribution divergence?
    **Deferred to Spec**: methodology commitment the user should approve so the spike doesn't redecide at execution time. Lower urgency since fixture unavailability means this pathway is unlikely to trigger — but still worth encoding if it does.
15. **"Unable to test" escalation** — does an `unable to test` verdict trigger a follow-up ticket (mirroring the `drift detected` spawn rule), or is it a terminal state?
    **Deferred to Spec**: scope decision affecting what the spike closes vs. leaves open.
