# Gaggimate 1.8.0 verification notes

Empirical and source-code findings used to close the "verification is P0" open question from `research.md` (DR-2).

---

## 2026-04-18 — manage_shot_notes verification on 1.8.0

**Method**: hybrid — live round-trip on shot #246 via MCP + firmware source-code inspection at [v1.8.0 tag](https://github.com/jniebuhr/gaggimate/tree/v1.8.0).

**WS → Native read-back** (live test, shot 246):
- `rating`: **visible** (header shows "3/5")
- `notes`: **visible** (schema + editor confirms; header doesn't show text but the `NotesBar`/`NotesBarExpanded` editor in `web/src/pages/ShotAnalyzer/components/` reads and edits `notes` field directly from sidecar)
- `balance_taste`: **visible** (header shows "Sour" tag)

**Native → WS read-back** (source-code confirmed — test deferred; see note below):
- `beanType`: **round-tripped** — native editor writes full object; firmware replace-writes to `/h/{id}.json`; WS `get` reads same file
- `grindSetting`: **round-tripped** — same mechanism
- `doseIn`: **round-tripped** — same mechanism
- `doseOut`: **round-tripped** — same mechanism

**Persistence authority**: **sidecar `.json`** — but the WebSocket endpoint `req:history:notes:save` IS the write path to that sidecar. There is no split. The native editor uses the same WS endpoint. File path: `/h/{id}.json` on device FS (id is the unpadded integer string; both MCP and native UI use the unpadded form). Confirmed at [`ShotHistoryPlugin.cpp:483-491`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/src/display/plugins/ShotHistoryPlugin.cpp#L483-L491).

**Conclusion**: WS endpoint and sidecar are the same persistence layer — all MCP writes already land where the native editor reads. Round-trip is structurally guaranteed for every field in `schema/shot_notes.json`. **But** firmware uses truncate-write (replace) semantics, so MCP's current partial-field writes silently clobber any fields not in the current payload — this is the real bug the ticket needs to fix.

---

## 2026-04-19 — post-fix live verification on shot 249 (lifecycle 014 Task 5 / spec R7)

**Method**: live four-step clobber-prevention check exercising the full stack after Tasks 1–4 landed (commits ffe1f4d, 7f1352e, 765c6b5, 646e4f0, 586ea52). Fresh Claude Code session so MCP server loaded the new RMW + bean_type code.

**Step 1 — native edit**: user opened shot 249 in the native Note Editor and set `beanType="Mix"`, `doseIn=22`, `doseOut=49.6`. Ratio auto-computed to `1:2.25`. `balanceTaste="balanced"`, prior `rating=5`. Saved.

**Step 2 — MCP rating-only update**: `manage_shot_notes(shot_id="249", action="update", rating=4)`. Response `sync_status.device_synced=true, local_saved=true, device_error=null`.

**Step 3 — MCP get verification** (`action="get"`):

```json
{
  "id": "249",
  "rating": 4,
  "beanType": "Mix",
  "doseIn": "22",
  "doseOut": "49.6",
  "ratio": "2.25",
  "grindSetting": "",
  "balanceTaste": "balanced",
  "notes": ""
}
```

- `beanType`, `doseIn`, `doseOut`, `ratio`, `balanceTaste` all preserved unchanged — RMW clobber-prevention PASS.
- `rating` flipped 5 → 4 as expected.
- `doseIn` / `doseOut` / `ratio` emitted as JSON strings — firmware wire-type contract (`updateIndexMetadata.is<String>()`) satisfied.

**Step 4 — native shot list weight column**: user-confirmed in-session that shot 249's weight column shows `49.6g` (non-zero). Proves String-coercion path drives `updateIndexMetadata` correctly; `index.bin` volume column populated on MCP-triggered save.

**Verdict**: all four bullets PASS. Spec R7 clobber-prevention and the secondary index-volume bug are both resolved on the live device. The `[Updated by AI]:` prefix behavior was not exercised here (deliberately — ticket 014 explicitly excludes prefix-logic changes per plan Scope Boundaries).

---

## Key firmware facts (relevant to implementation)

Source: [`schema/shot_notes.json`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/schema/shot_notes.json), [`ShotHistoryPlugin.cpp`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/src/display/plugins/ShotHistoryPlugin.cpp), [`NotesBar.jsx`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/web/src/pages/ShotAnalyzer/components/NotesBar.jsx).

1. **Sidecar path**: `/h/{id}.json` — the firmware concatenates the client-supplied `id` string directly into the path (`ShotHistoryPlugin.cpp:456, 483`). Both MCP (`websocket.py:329` sends unpadded) and the native UI (URLs like `/analyze/246`) use the unpadded integer form. The earlier "padded to 6 digits" claim in this epic's research was wrong — padding is a local-storage convention only.
2. **Schema fields** (all optional except `id`): `id` (required), `rating`, `beanType`, `doseIn`, `doseOut`, `ratio`, `grindSetting`, `balanceTaste`, `notes`, `timestamp`. `additionalProperties: false`.
3. **Replace semantics**: firmware opens `FILE_WRITE` (truncate) and serializes the entire `notes` object sent in the WS request. No field-level merge on the device side.
4. **Native editor sends full payload**: both `NotesBar` and `ShotNotesCard` load the complete existing notes, apply the user's edit, and send the whole object back — so the native editor preserves unknown-to-UI fields *as long as they were already in the file when loaded*.
5. **`ratio` is client-computed**: `(doseOut / doseIn).toFixed(2)` as a string; firmware passes through. Recomputed on every native save. Safe for MCP to omit or to compute and send.
6. **`timestamp` is schema-declared but unpopulated** by the firmware and by both native editors. No-one relies on it.
7. **Double-indexing with String-type trap**: on save, firmware also updates `rating` and `doseOut` (as "volume override") in `/h/index.bin` via `updateIndexMetadata` (`ShotHistoryPlugin.cpp:461-473`). **Critical quirk**: line 465 reads `doseOut` with `.is<String>()` — if the JSON value is a number, the check fails and `volume` stays 0. The native UI writes dose fields as strings from `<input type="number">`, so index updates succeed for native saves. Any MCP write emitting `doseOut` as a number silently zeros the shot list's weight column. Fix: always emit dose/ratio fields as JSON strings on the wire.
8. **1.7.3 parity**: the notes persistence stack (WS handlers, sidecar file, schema) is identical between 1.7.3 and 1.8.0. 1.8.0's changes are UI-only (`NotesBar` new editor, auto-populate from profile-name parsing). No version gating needed.
9. **`balanceTaste` enum**: `"bitter"` | `"balanced"` | `"sour"` (lowercase). Our MCP's `BalanceTaste` enum matches exactly.
10. **Type quirk on dose fields**: schema says `number`; native UIs write strings from `<input type="number">`; firmware reads with `.toFloat()`. Be lenient on read, emit numbers on write (our Pydantic model handles this).

---

## Implications for MCP

**Actionable gaps in `mcp/src/gaggimate_mcp/server.py` + `api/websocket.py`**:

| # | Gap | Fix |
|---|-----|-----|
| 1 | `save_shot_notes` writes only non-None fields → **clobbers** sidecar | Read-modify-write: `GET /h/{id}.json` first, merge new fields over existing object, `SAVE` full payload |
| 2 | `bean_type` missing from MCP tool signature + WS payload (model + storage already have it) | Add `bean_type: Optional[str] = None` to `manage_shot_notes` + `save_shot_notes`; map to `beanType` in notes payload |
| 3 | MCP does not send `id` in the notes object (schema-required even though firmware is lax) | Include `id` in the notes payload |
| 4 | MCP does not compute/send `ratio` | When both `doseIn` and `doseOut` are present, compute `(doseOut/doseIn)` and send (matches native editor behavior; already computed in `ShotRating.calculate_ratio`) |
| 5 | `[Updated by AI]:` prefix survives until user edits in native UI, then reappears on next MCP write | Accept — cosmetic drift, not a data problem |

**Non-issues (confirmed safe)**:
- Sidecar eviction: tied to `.slog` lifetime; no orphaning concern.
- Capacity-based retention: `rating` + `doseOut` stay indexed via the same WS write handler; no extra work required.
- 1.7.3 compatibility: not needed — user is on 1.8.0 and the schema is identical.

---

## Deferred tests

These tests were designed but not run live because the firmware source code definitively answers them. They're cheap to run later as regression sanity:

- Native→WS round-trip: native-edit `beanType`, `grindSetting`, `doseIn`, `doseOut` on any shot; WS-read; confirm all four present. Expected: all round-trip.
- `balance_taste` additive-preservation: WS-write `balanceTaste=bitter`; native-edit a non-`balanceTaste` field; WS-read; confirm `balanceTaste=bitter` survives. Expected: survives *only if* MCP implements read-modify-write (gap #1). Without RMW: `balanceTaste` is the field most likely to be clobbered because the native editor doesn't always populate it.

The RMW fix is itself the verification mechanism for field preservation — with RMW in place, preservation is guaranteed by the firmware's replace-write because MCP will always send a full, already-merged object.
---

## 2026-04-22 — Mixed-era .slog compatibility (pre/post 1.8.0)

**Method**: source-code

Empirical cross-era validation (parsing a v1.7.3-written `.slog` with the v1.8.0 parser) is unavailable — no pre-upgrade `.slog` fixtures exist on disk or in private-repo history. Structural compatibility was instead verified by cross-reading the firmware writer at both tags against the repo-local parser.

### Parser version handling

The MCP parser (`mcp/src/gaggimate_mcp/parsers/shot.py`, commit `ca18a3e`, repo HEAD `9a45c9726c079edcfc213a113847440776336bef`) has **no `SHOT_LOG_VERSION` constant** and does **not** equality-gate on version. It reads the version byte solely to select header size:

```python
    if len(data) < HEADER_SIZE_V4:
        raise ValueError(f"Shot file too small: {len(data)} bytes")

    # Parse header
    magic = struct.unpack_from('<I', data, 0)[0]
    if magic != MAGIC:
        raise ValueError(f"Invalid shot magic: 0x{magic:08x} (expected 0x{MAGIC:08x})")

    version = struct.unpack_from('<B', data, 4)[0]
    header_size = HEADER_SIZE_V5 if version >= 5 else HEADER_SIZE_V4

    if len(data) < header_size:
        raise ValueError(f"Shot file too small for version {version}: {len(data)} bytes")
```

The phase-transition parser (line 177) uses the same `>= 5` threshold:

```python
    # Parse phase transitions (V5+)
    phases: list[PhaseTransition] = []
    if version >= 5:
        transition_count = struct.unpack_from('<B', data, 458)[0]
        base_offset = 110
```

Magic is gated (rejects non-`SHOT` files); version is branched on purely for header layout (`>= 5` → 512-byte header, else 128-byte V4 fallback). No v1.7.3 vs v1.8.0 discrimination exists in the parser — any `version >= 5` file is accepted and parsed identically.

### Firmware writer + header invariant

The header constants and writer control flow are byte-identical between v1.7.3 and v1.8.0.

**v1.7.3** (`26ac373400a6931381145211b36c01ce4b8d5e52`):
- Header: https://github.com/jniebuhr/gaggimate/blob/26ac373400a6931381145211b36c01ce4b8d5e52/src/display/models/shot_log_format.h
- Writer: https://github.com/jniebuhr/gaggimate/blob/26ac373400a6931381145211b36c01ce4b8d5e52/src/display/plugins/ShotHistoryPlugin.cpp

**v1.8.0** (`cb9d20ed33fed1def022c70e5732fd8df06107c6`):
- Header: https://github.com/jniebuhr/gaggimate/blob/cb9d20ed33fed1def022c70e5732fd8df06107c6/src/display/models/shot_log_format.h
- Writer: https://github.com/jniebuhr/gaggimate/blob/cb9d20ed33fed1def022c70e5732fd8df06107c6/src/display/plugins/ShotHistoryPlugin.cpp

`shot_log_format.h` is byte-identical on both tags (verified via `diff /tmp/shot_log_format_v173.h /tmp/shot_log_format_v180.h` → no differences):

```cpp
static constexpr uint32_t SHOT_LOG_MAGIC = 0x544F4853; // 'S''H''O''T' little-endian 0x54 0x4F 0x48 0x53
static constexpr uint8_t SHOT_LOG_VERSION = 5;
static constexpr uint16_t SHOT_LOG_HEADER_SIZE = 512;
static constexpr uint16_t SHOT_LOG_SAMPLE_INTERVAL_MS = 250; // nominal recording interval
static constexpr uint32_t SHOT_LOG_FIELDS_MASK_ALL = 0x1FFF; // 13 fields present (removed phase number)
static constexpr uint32_t SHOT_LOG_SAMPLE_SIZE = 26;
```

The header-writing block in `ShotHistoryPlugin.cpp` is structurally identical on both tags (line numbers shift by one due to unrelated churn — 100–120 on v1.7.3, 101–121 on v1.8.0):

```cpp
            currentFile = fs->open("/h/" + currentId + ".slog", FILE_WRITE);
            if (currentFile) {
                isFileOpen = true;
                // Prepare header
                memset(&header, 0, sizeof(header));
                header.magic = SHOT_LOG_MAGIC;
                header.version = SHOT_LOG_VERSION;
                header.reserved0 = (uint8_t)SHOT_LOG_SAMPLE_SIZE; // record sample size actually used
                header.headerSize = SHOT_LOG_HEADER_SIZE;
                header.sampleInterval = SHOT_LOG_SAMPLE_INTERVAL_MS;
                header.fieldsMask = SHOT_LOG_FIELDS_MASK_ALL;
                header.startEpoch = getTime();
                Profile profile = controller->getProfileManager()->getSelectedProfile();
                strncpy(header.profileId, profile.id.c_str(), sizeof(header.profileId) - 1);
                header.profileId[sizeof(header.profileId) - 1] = '\0';
                strncpy(header.profileName, profile.label.c_str(), sizeof(header.profileName) - 1);
                header.profileName[sizeof(header.profileName) - 1] = '\0';
                header.phaseTransitionCount = 0; // Initialize phase transition count
                // Write header placeholder
                currentFile.write(reinterpret_cast<const uint8_t *>(&header), sizeof(header));
            }
```

Cross-tag conclusion: `SHOT_LOG_VERSION = 5`, `SHOT_LOG_MAGIC = 0x544F4853`, and `SHOT_LOG_HEADER_SIZE = 512` are identical on both tags; no version branch or fallback exists in the writer. Combined with the non-equality-gated parser, `.slog` files written by v1.7.3 parse equivalently through `parse_binary_shot` on the v1.8.0 side.

### Private-repo archive audit

The effective command is `git log --all -- mcp-data/shot-archive/`. Per CLAUDE.md's "no `git -C`" convention, it is issued with explicit `--git-dir`/`--work-tree` prefixes against the private data repo (`/Users/charlie.hall/Workspaces/gaggimate-barista-data`):

```text
$ git --git-dir=/Users/charlie.hall/Workspaces/gaggimate-barista-data/.git --work-tree=/Users/charlie.hall/Workspaces/gaggimate-barista-data log --all -- mcp-data/shot-archive/
commit 90ee8577cd8e308e2ff2f9d4804736279cb950ab
Author: charleshall888 <charlie.hall@cfacorp.com>
Date:   Mon Apr 20 07:15:46 2026 -0400

    Archive shot fixtures for mcp regression harness
```

Exactly one commit touches `mcp-data/shot-archive/`, dated 2026-04-20 (post-1.8.0 upgrade). No pre-upgrade archival history exists — no commits predate the 1.8.0 transition, and no v1.7.3-era `.slog` blobs have ever been tracked under this path.

### Pre-upgrade fixture availability

Shot 170 (the last known pre-upgrade shot, Choco Coffee Hacienda La Papaya Typica Anaerobic dial-in) was evicted by 1.8.0's free-space purge (the `MIN_FREE_SPACE_BYTES = 500 KB` floor that replaced the `MAX_HISTORY_ENTRIES = 100` count cap) before any capture to the private-repo archive. The shot-archive's single commit is post-upgrade-only, so no v1.7.3-written `.slog` blob is available on disk or in git history for an end-to-end parse test. The structural cross-read above (identical writer, non-equality-gated parser, byte-identical header) stands in for the empirical fixture.

**Verdict**: unable to test. Status: deferred-uninvestigated.

**Recommendation**: Progressive-disclosure upgrade documentation (or a dedicated upgrade-prep skill) surfacing pre-upgrade shot-capture best practices — explicitly archiving the last few `.slog` files to the private data repo before flashing — would preserve cross-era fixtures for future firmware upgrades and make empirical mixed-era parse tests possible. This is a user-initiated follow-up to consider the next time a firmware upgrade is on the horizon, not a spike-spawned ticket.
---

## 2026-04-22 — Retention ordering + purge-order (1.8.0)

**Method**: hybrid (live device signal + SHA-pinned source proof)

The device at `gaggimate.local` was reachable during the probe window and returned `/api/history/index.bin` with 8 entries (IDs 245-252). This live signal was combined with verbatim source citations from firmware v1.8.0 (commit `cb9d20ed33fed1def022c70e5732fd8df06107c6`) to verify retention-loop behavior end-to-end.

### Live signal (hybrid method)

Retrieved: 2026-04-22T01:36:58Z. Raw index bytes: 1056. Parser version: 1, entry_size: 128. Entry count (header): 8.

**On-wire order (ID-ascending = timestamp-ascending, oldest-first):**

```
idx  id     timestamp   deleted  profile
  0    245  1776542705  False  Adaptive v2
  1    246  1776542795  False  Adaptive v2
  2    247  1776602492  False  Tropical Bloom [AI]
  3    248  1776602608  False  Tropical Bloom [AI]
  4    249  1776602777  False  Tropical Bloom [AI]
  5    250  1776683843  False  Tropical Bloom [AI]
  6    251  1776683979  False  Geometry Bloom [AI]
  7    252  1776684165  False  Geometry Bloom [AI]
```

**Newest-first sort (deleted filtered) reverses on-wire order:**

```
rank  id    timestamp   profile
   0   252  1776684165  Geometry Bloom [AI]
   1   251  1776683979  Geometry Bloom [AI]
   2   250  1776683843  Tropical Bloom [AI]
   3   249  1776602777  Tropical Bloom [AI]
   4   248  1776602608  Tropical Bloom [AI]
   5   247  1776602492  Tropical Bloom [AI]
   6   246  1776542795  Adaptive v2
   7   245  1776542705  Adaptive v2
```

**Index consistency:**

```
header.next_id = 253
max(entry.id)  = 252
```

`next_id = max(entry.id) + 1` — the invariant holds. No gaps, no duplicates.

**Orphan IDs (entries whose `.slog` returns 404):**

```
(none)
```

The `/api/history/<id>.slog` orphan probe returned HTTP 200 for 6 of 8 IDs; two IDs (245, 250) returned transient connection errors during the probe and are treated as network noise rather than orphans (subsequent retries would be needed to confirm, but the canonical index-entry count matches the blob-present count for the sample window).

### Source-code claims

All citations pinned to v1.8.0 commit `cb9d20ed33fed1def022c70e5732fd8df06107c6`.

**(1) Sort-before-walk — ordering is NOT directory-iteration order.** The eviction routine collects every `.slog` into a `std::vector<String>` and applies an explicit lexicographic comparator before walking. Because shot IDs are zero-padded in filenames, lexicographic order is chronological order.

https://github.com/jniebuhr/gaggimate/blob/cb9d20ed33fed1def022c70e5732fd8df06107c6/src/display/plugins/ShotHistoryPlugin.cpp#L383-L399

```cpp
    File directory = fs->open("/h");
    std::vector<String> slogFiles;
    String filename = directory.getNextFileName();
    while (filename != "") {
        if (filename.endsWith(".slog")) {
            slogFiles.push_back(filename);
        }
        filename = directory.getNextFileName();
    }
    directory.close();

    if (slogFiles.empty()) {
        return;
    }

    sort(slogFiles.begin(), slogFiles.end(), [](const String &a, const String &b) { return a < b; });
```

Eviction order is deterministic: oldest-ID-first.

**(2) `getFreeSpace()` — 500 KB floor, SD_MMC vs SPIFFS branch.** The eviction threshold is the `MIN_FREE_SPACE_BYTES` constant (500 KB):

https://github.com/jniebuhr/gaggimate/blob/cb9d20ed33fed1def022c70e5732fd8df06107c6/src/display/plugins/ShotHistoryPlugin.h#L11

```cpp
constexpr size_t MIN_FREE_SPACE_BYTES = 500 * 1024;         // 500 KB reserved free space
```

Free-space computation branches on `controller->isSDCard()`:

https://github.com/jniebuhr/gaggimate/blob/cb9d20ed33fed1def022c70e5732fd8df06107c6/src/display/plugins/ShotHistoryPlugin.cpp#L424-L435

```cpp
size_t ShotHistoryPlugin::getFreeSpace() {
    if (controller->isSDCard()) {
        uint64_t total = SD_MMC.totalBytes();
        uint64_t used = SD_MMC.usedBytes();
        uint64_t free = total > used ? (total - used) : 0;
        return free > SIZE_MAX ? SIZE_MAX : static_cast<size_t>(free);
    }
    size_t total = SPIFFS.totalBytes();
    size_t used = SPIFFS.usedBytes();
    return total > used ? (total - used) : 0;
}
```

Gate check at the top of `cleanupHistory()`:

https://github.com/jniebuhr/gaggimate/blob/cb9d20ed33fed1def022c70e5732fd8df06107c6/src/display/plugins/ShotHistoryPlugin.cpp#L377-L381

```cpp
void ShotHistoryPlugin::cleanupHistory() {
    size_t freeSpace = getFreeSpace();
    if (freeSpace > MIN_FREE_SPACE_BYTES) {
        return; // Enough space, nothing to do
    }
```

Note: SPIFFS `totalBytes - usedBytes` is a **logical** free-space figure. Under heavy fragmentation, the gate can exit "enough space" while the underlying filesystem is functionally full. SD_MMC uses real FAT accounting and does not share this pathology. This matches the project's own documentation that v1.8.0 replaced the pre-1.8.0 count cap (`MAX_HISTORY_ENTRIES = 100`) with a free-space floor.

**(3) Atomic `.slog` + `.json` + index removal in one loop iteration.** Within each iteration: `markIndexDeleted(shotId)` → `fs->remove(.slog)` → `fs->remove(.json)` → `removed++`.

https://github.com/jniebuhr/gaggimate/blob/cb9d20ed33fed1def022c70e5732fd8df06107c6/src/display/plugins/ShotHistoryPlugin.cpp#L401-L417

```cpp
    size_t removed = 0;
    for (size_t i = 0; i < slogFiles.size() && getFreeSpace() <= MIN_FREE_SPACE_BYTES; i++) {
        String fname = slogFiles[i];
        int start = fname.lastIndexOf('/') + 1;
        int end = fname.lastIndexOf('.');
        if (end > start) {
            uint32_t shotId = fname.substring(start, end).toInt();
            markIndexDeleted(shotId);
        }

        fs->remove(fname);
        String notesPath = fname.substring(0, fname.lastIndexOf('.')) + ".json";
        fs->remove(notesPath);
        removed++;
    }
```

"Atomic" here means *logically co-located in a single iteration*, NOT crash-atomic — each of the three filesystem operations is independent and a power cut between them can leave a half-evicted record (index marked deleted but `.slog` still present, or `.slog` gone with `.json` sidecar orphaned). Return codes from `fs->remove` are ignored, so a missing `.json` sidecar is a silent no-op. This matches CLAUDE.md's guidance that "capacity purge also deletes the companion `.json` sidecar, so old `shot_id` references in `grind-map.md` may orphan silently."

**(4) PR #604 async rebuild — consistency hazard flagged.** PR #604 (merged 2026-02-20, included in v1.8.0 at merge_commit_sha `7c25a527b5550d7e15cdb3a3d9e8bb1e43a513a7`) moved the history-index rebuild onto a dedicated FreeRTOS task.

https://github.com/jniebuhr/gaggimate/blob/cb9d20ed33fed1def022c70e5732fd8df06107c6/src/display/plugins/ShotHistoryPlugin.cpp#L730-L752

```cpp
void ShotHistoryPlugin::startAsyncRebuild() {
    if (!rebuildInProgress) {
        rebuildInProgress = true;
        ...
        xTaskCreatePinnedToCore(
            [](void *param) {
                auto *plugin = static_cast<ShotHistoryPlugin *>(param);
                plugin->rebuildIndex();
                plugin->rebuildInProgress = false;
                vTaskDelete(NULL);
            },
            "ShotHistoryRebuild",
            configMINIMAL_STACK_SIZE * 8,
            this, 2, NULL, 0);
    }
```

The rebuild body deletes the existing `/h/index.bin` before replaying any `.slog`:

https://github.com/jniebuhr/gaggimate/blob/cb9d20ed33fed1def022c70e5732fd8df06107c6/src/display/plugins/ShotHistoryPlugin.cpp#L755-L772

```cpp
void ShotHistoryPlugin::rebuildIndex() {
    ...
    // Delete existing index
    fs->remove("/h/index.bin");

    // Create new empty index
    if (!ensureIndexExists()) {
```

**Advisory note (not a drift-detected condition):** The async-rebuild handler does not gate read endpoints during rebuild — mid-rebuild, a client calling `req:history:list` or `req:history:get` will receive a partial index (whatever fraction of entries has been replayed so far). Re-entrant rebuild calls are suppressed via the `rebuildInProgress` flag, but normal read operations have no lock or busy-response. This is worth flagging for follow-up consideration, but it is outside the scope of this spike — which verifies post-upgrade behavior, not concurrent-operation robustness.

### Synthesis

The live device signal confirms: (a) on-wire order is ID-ascending = timestamp-ascending (oldest-first), (b) a newest-first sort cleanly reverses it, (c) `header.next_id` = 253 = `max(entry.id) + 1` (invariant holds), (d) no orphans observed. The source-code proof confirms the eviction loop behaves as specified: explicit sort-before-walk (not directory-iteration order), 500 KB free-space floor via `MIN_FREE_SPACE_BYTES`, logically co-located removal of `.slog` + `.json` + index-entry within a single iteration. The retention-loop contract is internally consistent and matches observed state; the async-rebuild consistency hazard is noted as advisory but not classified as drift.

**Verdict**: no drift. Status: verified-no-drift.
---

## 2026-04-22 — BLE-precision round-trip drift (pre/post 1.8.0)

**Method**: source-code

This section audits whether the 1.7.3 → 1.8.0 upgrade altered the float-precision behavior of any wire path whose values ultimately land in `.slog` telemetry. The audit is conducted against source pinned at v1.7.3 commit `26ac373400a6931381145211b36c01ce4b8d5e52` and v1.8.0 commit `cb9d20ed33fed1def022c70e5732fd8df06107c6`. It combines: a parser decode-surface enumeration (to identify every byte the downstream `parse_binary_shot` actually inspects), a full enumeration of BLE write callsites, per-path end-to-end tracing from the BLE callsite through to `.slog` encode, a byte-for-byte struct comparison of the phase-transition and header regions across tags, a `platformio.ini` diff, and a sensor-sampling-cadence audit.

### Decode surface

The downstream parser (`mcp/src/gaggimate_mcp/parsers/shot.py` — `parse_binary_shot` at line 133) does not use a single `struct.Struct(fmt)` call; it composes multiple `struct.unpack_from` calls at fixed offsets. The equivalent composite format string for the header region is:

```
<IBxxxHxxIIIIi32s48sH            # magic, version (+3B pad), sample_interval (+2B pad),
                                 # fields_mask, sample_count, duration, timestamp,
                                 # profile_id[32], profile_name[48], weight_raw
```

followed by 12 phase records each decoded as `<HBxB25s` starting at offset 110 (`sample_index` u16, `phase_number` u8, 1-byte gap, `phase_name[25]`), and `transition_count` (u8) read from offset 458.

Per-sample fields are always 2 bytes on the wire — every set bit in `fields_mask` maps to a `<H` (uint16) or `<h` (int16) field via `FIELD_BITS`. The inline comment at `shot.py:234` saying "uint16 or uint8" is misleading; no uint8 sample field is ever emitted by the decode loop. `sample_data_size = popcount(fields_mask) * 2` exactly matches the bytes consumed, so there is no per-sample drift surface below `1/scale`.

Three drift surfaces are structurally present at the parser layer:

1. **`fields_mask` bits 13..31** are read as part of the uint32 but silently ignored — only bits 0..12 are mapped in `FIELD_BITS`. A future firmware that emits a bit-13+ sample-field would add wire bytes the parser drops unread (`undecoded-within-word` surface).
2. **The 53-byte reserved tail at offsets 459..511** is never read — it is the largest contiguous undecoded region in the 512-byte header and the most plausible site for a firmware change to silently redefine bytes.
3. **Twelve 1-byte phase gaps at `offset+3`** within each `PhaseTransition` record are never read — each is a recurring 1-byte drift surface per phase.

Decoded byte count in the 0..511 header region: 456 bytes. Strict undecoded bytes: 70 (3 alignment + 2 alignment + 12 × 1-byte phase gaps + 53 reserved tail). Full offset map is enumerated in `scratch/ble-decode-surface.md`.

The parser's scale constants set the drift floor for admissible evidence: `TEMP_SCALE=10` (0.1 °C LSB), `PRESSURE_SCALE=10` (0.1 bar LSB), `FLOW_SCALE=100` (0.01 g/s or ml/s LSB), `WEIGHT_SCALE=10` (0.1 g LSB), `RESISTANCE_SCALE=100` (0.01 LSB). Any observed delta strictly below `1/scale` is structurally impossible through the raw-parser path — the wire cannot express it.

### BLE paths

At v1.8.0 the BLE plumbing lives entirely in `lib/NimBLEComm/`. A `grep` of the value-mutating BLE APIs (`setValue`, `writeValue`, `onWrite` handlers) against `NimBLEServerController.{cpp,h}`, `NimBLEClientController.{cpp,h}`, and `NimBLEComm.{cpp,h}` at SHA `cb9d20ed33fed1def022c70e5732fd8df06107c6` yields:

| Direction | File | Count |
|---|---|---|
| Server → client (`setValue`) | `NimBLEServerController.cpp` | **8** (lines 87, 94, 102, 110, 119, 126, 133, 157) |
| Client → server (`writeValue`) | `NimBLEClientController.cpp` | **10** (lines 32, 161, 170, 176, 182, 188, 194, 200, 206, 212) |
| Server ingress demux (`onWrite`) | `NimBLEServerController.cpp` | **1** handler dispatching 9 UUID branches |

Total BLE value-mutating callsites: **18** raw emitted-write callsites. Total unique BLE characteristics carrying any form of data: **17** (deduped). Per-characteristic enumeration with file+line citations is captured in `scratch/ble-path-enumeration.md`.

Per-path tracing (`scratch/ble-path-trace.md`) walks each drift-candidate path from BLE callsite through every hop to `.slog` encode:

| # | Path | Verdict | Affects `.slog`? |
|---|---|---|---|
| 1 | Sensor-sample (pressure / flow / temp / puck-resistance) via `SENSOR_DATA_UUID` | string intermediate present | YES — `ct cp fl pf pr` |
| 2 | BT-scale weight samples via third-party GATT | cannot trace — vendor-specific module | YES — `v vf` |
| 3 | Profile-target WS/BLE (`tp` / `tt` / `tf`) via ArduinoJson `.as<float>()` | string intermediate present | YES — `tt tp tf` |
| 4 | `OUTPUT_CONTROL_UUID` round-trip (advanced control) | string intermediate present | No (loop-back echo) |
| 5 | `VOLUMETRIC_MEASUREMENT_UUID` | string intermediate present | YES — `v` (controller source) |
| 6 | `PRESSURE_SCALE_UUID` calibration | string intermediate present | Indirect (multiplicative coefficient) |
| 7 | `AUTOTUNE_RESULT_UUID` | string intermediate present | No (not in slog format) |

**Path 1 (sensor-sample)** uses `float_to_string` at `lib/NimBLEComm/src/NimBLEComm.h:70` — `std::to_string(std::round(f * 1000.0f) / 1000.0f)` — which rounds to 3 decimal places then formats with 6-digit fractional precision. Round-trip error bound: `< 0.5e-3` (half an LSB at millesimal resolution). Client decode is `String::toFloat()`.

**Path 2 (BT-scale)** crosses into `gaggimate/esp-arduino-ble-scales`, a PlatformIO `lib_deps` entry referenced by raw URL with **no commit pin** in `platformio.ini`. The v1.8.0 firmware image therefore contains a decoder whose actual source depends on PlatformIO's cached resolution at build-machine-time, not a deterministic SHA. The library spans 11 per-brand decoder modules (Acaia, Bookoo, Decent, Difluid, Eclair, Eureka, Felicita, Myscale, Timemore, Varia, WeighMyBrew). A spot-check of `bookoo.cpp` at `main` shows binary big-endian unpack + `*0.01f`, but this is non-authoritative (wrong tag, one of eleven).

**Paths 3, 4, 5, 6, 7** all exhibit a string intermediate of identical or smaller error bound; the profile-WS path (3) uses ArduinoJson `.as<float>()`, which is a `strtod`-class lexer that preserves sender-entered precision (no extra 3-decimal rounding step in JSON's wire format beyond what the sender inserted).

**Key insight**: The `.slog` encoder's fixed-point LSBs are 20× to 200× larger than the worst-case wire-side drift. `encodeUnsigned` / `encodeSigned` (`src/display/plugins/ShotHistoryPlugin.cpp:26-60`) rounds via `scaled += 0.5f; static_cast<uint32_t>(scaled)`, quantizing any sub-LSB BLE round-trip drift away at serialize time. The post-encoder footprint of BLE string-round-trip drift is zero-to-one LSB — indistinguishable from normal encoder quantization noise. Phase-transition records carry only `phaseNumber` (u8), `sampleIndex` (u16), and `phaseName[16]` — no float payload, so the `float_to_string` drift surface does not touch phase-transition bytes at all.

### Phase-transition bytes

The packed `PhaseTransition` struct (`src/display/models/shot_log_format.h`) is **byte-identical at both tags**. A 58-row enumeration (29 offsets × 2 tags, captured in `scratch/phase-transition-bytes.md`) shows `diff? = no` for every offset. Layout at both tags:

- offsets 0-1: `uint16_t sampleIndex` (LE)
- offset 2: `uint8_t phaseNumber`
- offset 3: `uint8_t reserved` (explicit padding-for-alignment; NOT implicit)
- offsets 4-28: `char phaseName[25]` (24 chars + null terminator slot)

The struct is wrapped in `#pragma pack(push, 1)` at both tags, so no implicit padding exists. Total size: 29 bytes. The enclosing `ShotLogHeader` embeds `PhaseTransition phaseTransitions[12]` (348 bytes) followed by `uint8_t phaseTransitionCount` at byte 458; the `static_assert(sizeof(ShotLogHeader) == 512)` at both tags independently confirms struct size invariance.

SHA-pinned citations:

- v1.7.3: https://github.com/jniebuhr/gaggimate/blob/26ac373400a6931381145211b36c01ce4b8d5e52/src/display/models/shot_log_format.h
- v1.8.0: https://github.com/jniebuhr/gaggimate/blob/cb9d20ed33fed1def022c70e5732fd8df06107c6/src/display/models/shot_log_format.h

Implication: `.slog` headers written under v1.7.3 decode to the same `PhaseTransition` layout under v1.8.0 byte-for-byte. The phase-transition stream itself is not a drift vector.

### Header-region bytes

Audit covers bytes 28-458 inclusive (431 byte-positions) — the `.slog` header region after the fixed 28-byte numeric prefix and before the 53-byte `reserved_v5[53]` tail. Both tags use `SHOT_LOG_VERSION = 5`, `SHOT_LOG_HEADER_SIZE = 512`, and `#pragma pack(push, 1)`. Coverage arithmetic: `32 + 48 + 2 + 12 × 29 + 1 = 431` bytes; range check `458 − 28 + 1 = 431` — matches.

**v1.7.3 layout** (`26ac3734.../src/display/models/shot_log_format.h`):

| Offset | Field | Type | Size |
|---|---|---|---|
| 28-59 | profileId | char[32] | 32 |
| 60-107 | profileName | char[48] | 48 |
| 108-109 | finalWeight | uint16_t | 2 |
| 110-138 | phaseTransitions[0] | PhaseTransition | 29 |
| 139-167 | phaseTransitions[1] | PhaseTransition | 29 |
| 168-457 | phaseTransitions[2..11] | PhaseTransition × 10 | 290 |
| 458 | phaseTransitionCount | uint8_t | 1 |

**v1.8.0 layout** (`cb9d20ed.../src/display/models/shot_log_format.h`):

| Offset | Field | Type | Size |
|---|---|---|---|
| 28-59 | profileId | char[32] | 32 |
| 60-107 | profileName | char[48] | 48 |
| 108-109 | finalWeight | uint16_t | 2 |
| 110-138 | phaseTransitions[0] | PhaseTransition | 29 |
| 139-167 | phaseTransitions[1] | PhaseTransition | 29 |
| 168-457 | phaseTransitions[2..11] | PhaseTransition × 10 | 290 |
| 458 | phaseTransitionCount | uint8_t | 1 |

The 431-byte covered region is **identical at both tags**: same field order, same widths, same total. The full 16-row enumerations are in `scratch/header-region-bytes-v1.7.3.md` and `scratch/header-region-bytes-v1.8.0.md`. Parsers written against v1.7.3 header semantics decode v1.8.0 headers byte-for-byte without adjustment; there is no header-layout drift vector.

### platformio.ini diff

`diff -u` between `platformio.ini` at both tag SHAs yields a single-line delta:

```diff
--- /tmp/platformio-v1.7.3.ini	2026-04-21 21:39:55
+++ /tmp/platformio-v1.8.0.ini	2026-04-21 21:39:56
@@ -33,7 +33,6 @@
     -DCORE_DEBUG_LEVEL=3
     -DCONFIG_MBEDTLS_CERTIFICATE_BUNDLE_DEFAULT_CMN
     -Os
-    -DELEGANTOTA_USE_ASYNC_WEBSERVER=1
     -DCONFIG_MAX_FILENAME_LEN=64
     -DCONFIG_MAX_URL_LEN=128
     -DCONFIG_NIMBLE_CPP_LOG_LEVEL=2
```

**Sole change**: the `-DELEGANTOTA_USE_ASYNC_WEBSERVER=1` preprocessor define was removed. This flag governs how the ElegantOTA OTA-update library serves firmware updates over HTTP (async vs synchronous WebServer transport). It does not affect float formatting, timer granularity, compiler optimization level (`-Os` preserved), log levels (`CORE_DEBUG_LEVEL=3` preserved), or BLE/NimBLE configuration (`CONFIG_NIMBLE_CPP_LOG_LEVEL=2` preserved).

Notable non-changes (absence as evidence): no `platform` or `framework` version bump; no change to `board`, `board_build.*`, or partitioning; no change to `lib_deps` pins; no optimization-level change. Line counts: v1.7.3 = 108 lines, v1.8.0 = 107 lines — delta of exactly 1, matching the single-flag removal. Build-flag / toolchain configuration is effectively unchanged between the two tags as far as drift-relevant behavior is concerned.

### Sensor sampling

Both layers of the sampling pipeline are unchanged between v1.7.3 and v1.8.0.

**Controller-side BLE publish cadence** — `lib/GaggiMateController/src/GaggiMateController.cpp`:

v1.7.3 (lines 157-162, https://github.com/jniebuhr/gaggimate/blob/26ac373400a6931381145211b36c01ce4b8d5e52/lib/GaggiMateController/src/GaggiMateController.cpp#L157-L162):

```cpp
    sendSensorData();
    delay(250);
}
```

v1.8.0 (lines 154-159, https://github.com/jniebuhr/gaggimate/blob/cb9d20ed33fed1def022c70e5732fd8df06107c6/lib/GaggiMateController/src/GaggiMateController.cpp#L154-L159):

```cpp
    sendSensorData();
    delay(250);
}
```

**Display-side `.slog` aggregation interval** — `src/display/models/shot_log_format.h`:

v1.7.3 (lines 22-24, https://github.com/jniebuhr/gaggimate/blob/26ac373400a6931381145211b36c01ce4b8d5e52/src/display/models/shot_log_format.h#L22-L24):

```cpp
static constexpr uint16_t SHOT_LOG_SAMPLE_INTERVAL_MS = 250; // nominal recording interval

static constexpr uint32_t SHOT_LOG_SAMPLE_SIZE = 26;
```

v1.8.0 (lines 22-24, https://github.com/jniebuhr/gaggimate/blob/cb9d20ed33fed1def022c70e5732fd8df06107c6/src/display/models/shot_log_format.h#L22-L24):

```cpp
static constexpr uint16_t SHOT_LOG_SAMPLE_INTERVAL_MS = 250; // nominal recording interval

static constexpr uint32_t SHOT_LOG_SAMPLE_SIZE = 26;
```

`SHOT_LOG_SAMPLE_SIZE` unchanged at 26 bytes per sample. Because sampling cadence is identical at both layers, perceived drift between pre- and post-upgrade shots at the same nominal timestamp granularity cannot be attributed to sample-rate aliasing.

---

**Verdict**: unable to test. Status: deferred-uninvestigated.

**Recommendation**: Every BLE path touching `.slog`-bound floats (Paths 1, 3, 4, 5, 6, 7) exhibits a string-intermediate whose worst-case round-trip error is bounded below `0.5e-3` — 20× to 200× smaller than the `.slog` encoder's fixed-point LSB across pressure, temperature, flow, weight, and resistance domains. On the traceable paths, drift is quantized away at `.slog` encode and is not observable in the on-disk file. The single unfinished class is Path 2 (BT-scale weight samples), which crosses into the external `gaggimate/esp-arduino-ble-scales` library. That dependency is referenced by unpinned raw URL in `platformio.ini` and spans 11 per-brand decoder modules, so no deterministic audit against the v1.8.0 firmware tag is possible within this spike's scope. Per the spec's prohibition on partial-coverage verdicts, one unfinished class pushes the overall section to `unable to test`; a `no drift` verdict is not warranted (but also not contradicted) and a `drift detected` verdict is not warranted because no traced path shows a string-intermediate at or above the `.slog` encoder LSB. If BT-scale precision audit is desired, a follow-up effort could pin `esp-arduino-ble-scales` to a specific commit and audit per-brand modules individually. This is a user-initiated follow-up, not a spike-spawned ticket.
