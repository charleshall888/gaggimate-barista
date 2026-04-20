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
