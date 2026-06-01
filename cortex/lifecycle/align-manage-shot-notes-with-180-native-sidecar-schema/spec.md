# Specification: Align `manage_shot_notes` with 1.8.0 native sidecar schema

Epic reference: [`research/gaggimate-1-8-0-upgrade/research.md`](../../research/gaggimate-1-8-0-upgrade/research.md) (DR-2).
Verification log: [`research/gaggimate-1-8-0-upgrade/verification-notes.md`](../../research/gaggimate-1-8-0-upgrade/verification-notes.md).

## Problem Statement

`/feedback` is invoked after every rated shot and calls `manage_shot_notes` to sync rating/notes to the device. On firmware 1.8.0, the WebSocket `req:history:notes:save` handler writes the entire sidecar file `/h/{id}.json` via truncate (replace, not merge). Our current `save_shot_notes` builds the payload from only the non-None fields the caller passed, which means any field not in the current call gets **silently wiped**. The same handler also updates `/h/index.bin` — but only when `doseOut` is sent as a JSON **String**; if sent as a number, the index's `volume` column silently zeros, corrupting the native shot list. Our current MCP sends `doseOut` as a Python float. The fix is to (a) implement read-modify-write in the WS transport, (b) coerce numeric dose/ratio fields to strings on the wire, (c) add the missing `bean_type` parameter, (d) update `/feedback` to pass it (auto-populated from the active coffee), and (e) include `id` inside the notes payload per schema.

## Requirements

All seven requirements below are **must-have** — the ticket cannot close without each of them. There are no should-haves or nice-to-haves in scope; anything that would be a should-have belongs in sibling tickets 015/016/017/018/021. See **Non-Requirements** for the won't-do list.

1. **Add `bean_type` parameter to `manage_shot_notes`** (must): `mcp/src/gaggimate_mcp/server.py:514` — add `bean_type: Optional[str] = None` to the tool signature; pass it to `ws_client.save_shot_notes` and to the `ShotRating(...)` constructor used for local backup.
   - Acceptance: call `manage_shot_notes(shot_id="999", bean_type="TEST-BEAN", sync_to_device=False)`; read `{data_repo}/mcp-data/ratings.json`; the entry for `"000999"` contains `"bean_type": "TEST-BEAN"`.
   - Acceptance: `python -c "from gaggimate_mcp.server import manage_shot_notes; import inspect; assert 'bean_type' in inspect.signature(manage_shot_notes).parameters"` exits 0.

2. **Add `bean_type` parameter to `save_shot_notes` WS transport** (must): `mcp/src/gaggimate_mcp/api/websocket.py` — add `bean_type: Optional[str] = None` to `save_shot_notes`; when non-None, the built payload's `notes` dict contains `"beanType": <value>`.
   - Acceptance: `python -c "from gaggimate_mcp.api.websocket import GaggimateWebSocketClient; import inspect; assert 'bean_type' in inspect.signature(GaggimateWebSocketClient.save_shot_notes).parameters"` exits 0.
   - Acceptance: covered by the unit test in Requirement 6 (empty-sidecar case includes `beanType` in the captured payload).

3. **Implement read-modify-write in `save_shot_notes`** (must): before building the outgoing payload, call `self.get_shot_notes(normalized_id)` to fetch the existing sidecar. Accept both `None` and `{}` as "no existing state" (treat either as empty). If the returned value is not a dict (defensive check — it shouldn't happen but guards against firmware serialization bugs), log a warning and treat as empty.
   Build the outgoing payload by: (a) spreading existing state first; (b) overlaying the non-None caller-provided fields mapped to camelCase keys (`balance_taste` → `balanceTaste`, `grind_setting` → `grindSetting`, `dose_in` → `doseIn`, `dose_out` → `doseOut`, `bean_type` → `beanType`); (c) **emitting dose fields and `ratio` as strings** (`str(value)` for numbers) so the firmware's `updateIndexMetadata` at `ShotHistoryPlugin.cpp:465` accepts them; (d) when both `doseIn` and `doseOut` are numerically valid, computing and setting `ratio = str(round(float(doseOut) / float(doseIn), 3))`; (e) always ensuring `id` is present in the notes object — prefer the existing value if the sidecar already has one; else set it to `normalized_id` (the unpadded integer string, matching what the envelope already uses at `websocket.py:329` and what the native web UI sends from `/analyze/{id}` URLs).
   Send the full merged object via `req:history:notes:save`. Do not bypass to the old partial-payload path.
   - See Requirement 6 for unit-test acceptance. See Requirement 7 for live integration acceptance.

4. **No-op write short-circuit** (must): if, after building the merged payload, the result equals the existing sidecar dict (comparing by dict equality, ignoring key ordering) AND the caller did not explicitly change any field, skip the WS `save` call entirely. Local backup may still be written (to capture timestamp updates). The goal is avoiding flash wear when `/feedback` is invoked without new information.
   - Acceptance (unit test, part of `test_save_shot_notes_rmw.py`): given existing `{"id": "246", "rating": 3}` and caller passes only `rating=3` (same value), `_send_request` is not called for `req:history:notes:save`.

5. **`/feedback` skill passes `bean_type`** (must): `~/.claude/skills/feedback/SKILL.md` — the skill's `manage_shot_notes` call guidance must instruct: (a) read `user-setup.md` for the Active Coffee section; (b) if present and not the "No active coffee" placeholder, pass the coffee's display title as `bean_type`, truncated to 200 chars; (c) if the user explicitly provides a different bean designation in their feedback prose, prefer the user's value; (d) if Active Coffee is absent or placeholder, omit `bean_type` entirely — do not send the placeholder string.
   - Acceptance: `grep -c "bean_type" ~/.claude/skills/feedback/SKILL.md` ≥ 2 (at least one reference in the call-guidance and one describing the Active Coffee fallback).
   - Acceptance: `grep -q "Active Coffee" ~/.claude/skills/feedback/SKILL.md` succeeds.

6. **Inline pytest for RMW + wire-type merge logic** (must): create `mcp/tests/test_save_shot_notes_rmw.py`. If `mcp/tests/` does not exist, create it with `__init__.py`. Tests use `AsyncMock` for `GaggimateWebSocketClient._send_request` and patch `get_shot_notes` on the instance under test. No device dependency.
   Required test cases:
   - **Preservation**: `get_shot_notes` returns `{"id": "246", "rating": 3, "balanceTaste": "bitter"}`; caller passes only `notes="hi"`; captured `_send_request` for `req:history:notes:save` carries `notes={"id": "246", "rating": 3, "balanceTaste": "bitter", "notes": "hi"}`.
   - **Empty sidecar**: `get_shot_notes` returns `None`; caller passes `rating=5, dose_in=22.0, dose_out=55.0, bean_type="X"`; captured payload carries `notes={"id": "246", "rating": 5, "doseIn": "22.0", "doseOut": "55.0", "ratio": "2.5", "beanType": "X"}` (all dose/ratio values as strings).
   - **Defensive non-dict**: `get_shot_notes` returns `"oops"` (simulated firmware bug); caller passes `rating=3`; no exception raised; payload built as if empty sidecar.
   - **No-op**: `get_shot_notes` returns `{"id": "246", "rating": 3}`; caller passes `rating=3`; `_send_request` not called for `notes:save`.
   - **String vs number on dose fields**: when existing sidecar has `"doseIn": "18.0"` (string, from native editor), caller passes no dose fields, captured payload preserves `"doseIn": "18.0"` unchanged (neither float-coerced nor stripped).
   - Acceptance: `cd mcp && python -m pytest tests/test_save_shot_notes_rmw.py -q` exits 0.

7. **Live integration acceptance — clobber-prevention verification** (must): after all code changes, empirically verify the fix prevents MCP from clobbering native-editor-set fields (the real bug direction). Method:
   - (a) Via native editor on any recent shot (e.g., 246), set `beanType="INTEG-BEAN"`, `doseIn="18.0"`, `doseOut="36.0"`. Save.
   - (b) Call `manage_shot_notes(shot_id="246", action="update", rating=4)` — deliberately passing only `rating`, nothing else.
   - (c) Call `manage_shot_notes(shot_id="246", action="get")`; assert the returned notes dict contains all four fields: `rating=4`, `beanType="INTEG-BEAN"`, `doseIn="18.0"`, `doseOut="36.0"`. If ANY of the native-set fields is missing, the RMW fix is incomplete.
   - (d) Check the native shot list in the web UI: confirm shot 246's weight column shows "36.0g" (not "0g") — proves the index.bin update survived the string-coercion fix.
   - Recorded as a dated entry in `research/gaggimate-1-8-0-upgrade/verification-notes.md` with each bullet's pass/fail.
   - Acceptance: interactive/session-dependent. Cannot be asserted by a shell command — requires a live device, the native web UI, and a user's visual check of the shot list.

## Non-Requirements

- Writing to the sidecar file directly via any non-WebSocket mechanism. The WS handler is the authoritative path (it also updates `/h/index.bin`).
- Supporting firmware versions other than 1.8.0 (and incidentally 1.7.3, which has the same notes stack). No version gating or feature detection.
- Adding new fields beyond `schema/shot_notes.json`'s 10 fields (`id`, `rating`, `beanType`, `doseIn`, `doseOut`, `ratio`, `grindSetting`, `balanceTaste`, `notes`, `timestamp`). `additionalProperties: false` — no MCP-specific metadata in the sidecar. `timestamp` remains unpopulated (schema-declared but unused by the firmware and both native editors).
- Compare-and-swap / conflict detection on concurrent edits. Last-writer-wins is acceptable for single-user single-machine.
- Migrating existing local `ratings.json` entries to include `bean_type` retroactively. Only new saves get the field.
- Stripping or rewriting the `[Updated by AI]:` notes prefix across the repo.
- Changes to `list_recent_shots` or any other MCP tool beyond `manage_shot_notes`.
- A broader MCP test harness (that's ticket 016). Only a localized unit test for this ticket's RMW merge logic.
- Changing the response envelope of `manage_shot_notes` to surface the merged payload sent to device. The current response (`success`, `message`, `rating_data` from local backup) is preserved even though it doesn't show the merged sidecar — adding that is backlog-worthy but out of scope.
- Padding `id` to 6 digits on the wire. The firmware uses the id string as-is in path concatenation (`/h/{id}.json`); both MCP (`websocket.py:329` sends unpadded) and the native web UI (URLs like `/analyze/246` are unpadded) already use the unpadded form consistently. Empirically confirmed during research Phase 1: the native editor read back our unpadded-id write on shot 246.

## Edge Cases

- **Empty sidecar read (None)**: `get_shot_notes` returns `None` when firmware's `loadNotes` returns no notes. Merge treats as empty dict.
- **Empty sidecar read (empty dict)**: some firmware versions may serialize an empty JsonDocument as `{}` rather than `null`. Treat identically — empty input means we build the payload from caller fields + defaults.
- **Defensive: `get_shot_notes` returns non-dict**: firmware serialization bugs could theoretically return a list or string. Log a warning and treat as empty. Do not crash the /feedback loop over a transport anomaly.
- **Pre-existing sidecar with unknown fields**: merge preserves them by spreading existing first. Future-firmware-compatibility invariant.
- **Only one of `dose_in`/`dose_out` provided (or neither)**: do NOT compute `ratio`. Skip emission. Pre-existing `ratio` preserved as-is if in the sidecar.
- **Existing dose/ratio stored as strings (from native editor) vs. caller passing floats**: emit the wire payload as strings in all cases. Existing string values preserved byte-for-byte; caller-provided numbers stringified with `str(value)`.
- **`balance_taste` passed as invalid enum value**: existing path at `server.py:610-617` logs a warning and skips local enum assignment; WS payload sends the raw string. Firmware does not validate; native editor's dropdown won't render an unrecognized value. Behavior unchanged by this ticket.
- **Device unreachable — read fails**: `get_shot_notes` raises `GaggimateError` from the transport layer. The exception propagates out of `save_shot_notes` and is caught by the existing `except GaggimateError` at `server.py:606`. Result: `device_synced=False`, `device_error=<read error message>`, local backup saved. Local backup gets the caller-provided partial fields only — it does NOT recover pre-existing sidecar state (we didn't read it). Acceptable — the device is unreachable anyway; next successful call will re-merge.
- **Device reachable for read but not write**: RMW read succeeds, WS save raises. `device_synced=False`, `device_error=<write error message>`. Local backup still saves caller's partial fields. On next successful write, RMW reads the (still-intact) sidecar and merges correctly — no permanent corruption.
- **RMW read races a concurrent native-editor save**: the read returns the last-persisted state (native's in-progress edit not yet saved). Our write persists our merge of that pre-native state. When the user saves in the native UI, the UI's full-object write supersedes. Last-writer-wins with lost MCP intermediate. No silent corruption, but the user has no explicit signal MCP's write was overwritten. Accept — rare race, self-healing on next MCP call.
- **`bean_type` longer than 200 chars**: Pydantic `ShotRating.bean_type` has `max_length=200`. Oversized values raise `ValidationError` in local backup. `/feedback` must truncate before calling — see Requirement 5(b). On the WS wire, over-long beanType is also beyond firmware's schema `maxLength` (though firmware doesn't validate); truncating client-side is the contract.
- **Active Coffee section absent or placeholder**: `/feedback` must omit `bean_type` entirely — never send the "No active coffee" placeholder. RMW still preserves any existing `beanType` in the sidecar.
- **Payload size budget**: worst-case merged payload is `notes=2000ch + beanType=200ch + grindSetting=free + id/rating/ratio/balanceTaste/doseIn/doseOut ≈ 2.5KB`. ESP32 ArduinoJson `JsonDocument` capacity is upstream firmware's concern, but we must not deliberately send oversized data. Enforce at tool boundary: Pydantic `ShotRating.notes` already has `max_length=2000` (larger than firmware's schema of 200, but firmware doesn't validate — accept the asymmetry). Do not introduce new large fields.

## Changes to Existing Behavior

- **MODIFIED**: `save_shot_notes` payload construction — was "only non-None provided fields as a partial object", now "read existing → spread → overlay non-None fields → stringify dose/ratio → always include `id`". Partial-payload send path removed.
- **MODIFIED**: wire types for `doseIn`, `doseOut`, `ratio` — emit as strings on the WS payload to satisfy firmware's `is<String>()` check at `ShotHistoryPlugin.cpp:465`. Python-side parameters remain float/numeric; stringification is a transport-layer concern inside `save_shot_notes`.
- **ADDED**: `bean_type` / `beanType` traversal through the MCP stack (`ShotRating` model + `RatingStorage` already have the field; tool signature + WS transport get wired).
- **ADDED**: `get_shot_notes` is now called automatically on every `save_shot_notes` (read-before-write). One extra WS round trip per save.
- **MODIFIED**: `/feedback` behavior — auto-populates `bean_type` from `user-setup.md` Active Coffee on every rated-shot call (with explicit-override and placeholder-absence rules).
- **ADDED**: first unit test file under `mcp/tests/` (directory created if absent; `__init__.py` added).
- **ADDED**: no-op early-exit on identical RMW merge — avoids unnecessary flash writes.

## Technical Constraints

- Firmware 1.8.0 `req:history:notes:save` handler at [`ShotHistoryPlugin.cpp:483-491`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/src/display/plugins/ShotHistoryPlugin.cpp#L483-L491) opens `/h/{id}.json` with `FILE_WRITE` then `serializeJson(notes, file)` — replace semantics on write. Empirically confirmed during Phase 1 verification (shot 246 WS-write → native UI displays written values).
- Firmware's `updateIndexMetadata` at [`ShotHistoryPlugin.cpp:461-473`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/src/display/plugins/ShotHistoryPlugin.cpp#L461-L473) reads `notes["doseOut"]` with `.is<String>()` and only updates `index.bin`'s volume column when the value is a JSON String. Sending `doseOut` as a number silently zeros that column. This constrains wire types as described above.
- Sidecar schema is `additionalProperties: false` ([`schema/shot_notes.json`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/schema/shot_notes.json)). Firmware is lax (does not validate), but do not introduce MCP-specific extra keys.
- `balanceTaste` enum values exactly: `"bitter"`, `"balanced"`, `"sour"` (lowercase). MCP's `BalanceTaste` enum already matches.
- The `[Updated by AI]:` prefix (`config.ai_notes_prefix`) is still prepended in `server.py:583-590`. This spec does not change that.
- Data-repo auto-commit policy: MCP code lives in this repo, not the data repo. No `.data-repo-path` commit is triggered by this ticket's code changes. The `ratings.json` file IS in the data repo; new entries naturally include `bean_type` via `ShotRating` — this will be committed/pushed on the next auto-commit event from `/feedback` per CLAUDE.md.
- `id` on the wire: match what native editor + existing MCP envelope use — the unpadded integer string. Pad only if a future firmware mandates it; empirically, it does not.

## Open Decisions

None. Decisions resolved during Clarify/Specify interview and research:
- `bean_type` auto-populates from `user-setup.md` Active Coffee (with user-provided override) — answered in Specify interview.
- `ratio` is computed + sent by MCP when both doses are numeric — answered in Specify interview.
- All dose and `ratio` fields emit as **strings** on the wire — resolved by critical review (firmware's `is<String>()` check on `doseOut` for index updates).
- `id` emitted as unpadded integer string matching envelope/URL conventions — resolved by critical review (firmware concatenates without padding; native UI uses unpadded URLs).
- Integration test AC verifies clobber-prevention (native-write → MCP-partial-write → MCP-read) — resolved by critical review (prior direction tested the wrong thing).
