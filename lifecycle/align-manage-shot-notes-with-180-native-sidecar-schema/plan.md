# Plan: Align `manage_shot_notes` with 1.8.0 native sidecar schema

## Overview

Rewrite `save_shot_notes` in `websocket.py` to implement read-modify-write with firmware-wire-compatible types (string dose/ratio), then propagate `bean_type` through the tool boundary (`server.py`), write focused pytest coverage for the merge logic, and update `/feedback` to auto-populate `bean_type` from Active Coffee. Live integration verification closes the loop.

**Note on protocol deviation**: Criticality is `critical`, which normally dispatches 2 competing plan agents. Deviating to single-plan flow in main context — the spec is prescriptively designed and the architectural decisions (RMW, string wire types, id handling) were already resolved in spec + critical review. Decomposition strategy has narrow room for meaningful variance. Logged in `events.log` as `plan_protocol_deviation`.

## Tasks

### Task 1: Rewrite `save_shot_notes` with RMW + wire-type fixes
- **Files**: `mcp/src/gaggimate_mcp/api/websocket.py`
- **What**: Replace the existing partial-payload `save_shot_notes` with a read-modify-write implementation that (a) calls `self.get_shot_notes(normalized_id)` first, (b) accepts `None`/`{}`/non-dict returns as "empty", (c) spreads existing state, (d) overlays non-None caller fields mapped to camelCase, (e) stringifies `doseIn`/`doseOut`/`ratio` on the wire, (f) includes `id` (preserving existing if present, else unpadded `normalized_id`), (g) computes `ratio` when both doses numeric, (h) short-circuits the save if merged payload equals existing and no field changed.
- **Depends on**: none
- **Complexity**: complex
- **Context**:
  - Current function lives at `mcp/src/gaggimate_mcp/api/websocket.py:347-402`. Signature: `async def save_shot_notes(self, shot_id: str, rating: Optional[int] = None, notes: Optional[str] = None, balance_taste: Optional[str] = None, grind_setting: Optional[str] = None, dose_in: Optional[float] = None, dose_out: Optional[float] = None) -> dict`.
  - Add new parameter: `bean_type: Optional[str] = None`.
  - Reuse existing `get_shot_notes` at `:316-345`. It returns `Optional[dict]` — check `isinstance(result, dict)` before spreading; if not dict or falsy, start from `{}`.
  - Field mapping (Python → JSON): `rating` → `"rating"` (int), `notes` → `"notes"` (str), `balance_taste` → `"balanceTaste"` (str), `grind_setting` → `"grindSetting"` (str), `dose_in` → `"doseIn"` (str — stringify floats), `dose_out` → `"doseOut"` (str — stringify floats), `bean_type` → `"beanType"` (str), `ratio` → `"ratio"` (str — computed).
  - `id` handling: merged_notes must have `"id"` key. If existing dict has one, preserve. Else set to `str(int(shot_id))` (the `normalized_id` already computed at top of function).
  - Ratio: when caller provides both `dose_in` AND `dose_out` as truthy numerics, compute `round(float(dose_out) / float(dose_in), 3)` and stringify. If only one provided, do NOT touch `ratio` (preserved from existing if present). Handle `float("0.0")` / division by zero — skip if `dose_in == 0`.
  - No-op short-circuit: after merge, if `merged == existing` (dict equality) AND caller passed no non-None field values, skip the `_send_request` call and return a synthetic success response `{"msg": "no-op: unchanged", "id": normalized_id}` so `manage_shot_notes`'s `device_synced` branch still sets `True`.
  - Logging: keep `logger.info("saving_shot_notes", ...)` before the write; add `logger.debug("rmw_merge_skipped_noop", ...)` when short-circuit fires.
  - **Call-site contract for the save**: the WS save invocation MUST remain `await self._send_request("req:history:notes:save", request_id, id=normalized_id, notes=merged_notes)` — keep `notes` as a keyword argument (Task 3 tests access `call_args.kwargs["notes"]` and depend on this shape).
- **Verification**:
  - `python -c "from gaggimate_mcp.api.websocket import GaggimateWebSocketClient; import inspect; p = inspect.signature(GaggimateWebSocketClient.save_shot_notes).parameters; assert 'bean_type' in p; print('OK')"` prints `OK`.
  - `grep -c 'self.get_shot_notes(normalized_id' mcp/src/gaggimate_mcp/api/websocket.py` ≥ 1 — pass if count ≥ 1 (the RMW read-before-write call, not the definition). Distinct from the `async def get_shot_notes` line which does not match this pattern.
  - Remaining behavioral verification covered by Task 3's pytest run.
- **Status**: [x] completed

### Task 2: Wire `bean_type` through `manage_shot_notes` tool + defense-in-depth truncation
- **Files**: `mcp/src/gaggimate_mcp/server.py`
- **What**: Add `bean_type: Optional[str] = None` to the `manage_shot_notes` tool signature and docstring (Args section). Before passing to downstream, apply defensive truncation: if `bean_type is not None`, set `bean_type = bean_type[:200]` (server-side belt for `/feedback`'s suspenders, per spec Edge Case on oversized `bean_type`). Pass the truncated value to BOTH `ws_client.save_shot_notes(...)` and `ShotRating(...)`.
- **Depends on**: [1]
- **Complexity**: simple
- **Context**:
  - Tool signature currently at `mcp/src/gaggimate_mcp/server.py:514-523`. Pattern to follow: exact same Optional[str] style used for `grind_setting`.
  - `ShotRating` at `mcp/src/gaggimate_mcp/models/rating.py:48` already has the `bean_type` field with `max_length=200` — no model change needed.
  - `RatingStorage.save_rating` at `mcp/src/gaggimate_mcp/storage/ratings.py:78` already writes `bean_type` to the local `ratings.json`.
  - Docstring update: follow the existing field description style in the docstring at `:525-543`. New line: `bean_type: Coffee bean / origin description (optional, max 200 chars — truncated if longer)`.
  - Truncation placement: right after the `shot_id` normalization block (around line 555, just before the try/except). Keeps it above both the device sync and the local backup paths so both receive the same truncated value — prevents device/local divergence when input exceeds 200 chars.
  - At the `save_shot_notes(...)` call site in server.py (`:594-603`), append `bean_type=bean_type,` as a new keyword argument (matches style of existing `dose_out=dose_out,`).
  - At the `ShotRating(...)` ctor site (`:620-628`), append `bean_type=bean_type,` as a new keyword argument.
- **Verification**:
  - `python -c "from gaggimate_mcp.server import manage_shot_notes; import inspect; p = inspect.signature(manage_shot_notes).parameters; assert 'bean_type' in p; print('OK')"` prints `OK`.
  - Semantic coverage of both call sites is provided by Task 3's `test_tool_passes_bean_type_to_both_sinks` test (asserts bean_type reaches both the WS transport AND the local `ShotRating` ctor via `sync_to_device=False` + `sync_to_device=True` paths). Grep counts are structural; behavioral verification is via pytest.
- **Status**: [x] completed

### Task 3: Create pytest for `save_shot_notes` merge logic + tool-layer propagation
- **Files**: `mcp/tests/__init__.py` (new), `mcp/tests/test_save_shot_notes_rmw.py` (new)
- **What**: Create the `mcp/tests/` directory with an empty `__init__.py` and a test file containing six pytest async test cases that validate the RMW + wire-type behavior from Task 1 and the `bean_type` propagation from Task 2. Use `pytest-asyncio`'s `@pytest.mark.asyncio` decorator and `unittest.mock.AsyncMock`.
- **Depends on**: [1, 2]
- **Complexity**: simple
- **Context**:
  - Confirm `pytest-asyncio` is in `mcp/pyproject.toml` before writing the file. If not present, add it to the dev dependencies there.
  - Test fixture pattern: instantiate `GaggimateWebSocketClient(mock_config)` with a minimal mock config (just enough attrs to satisfy `__init__`). Replace `instance.get_shot_notes` and `instance._send_request` with `AsyncMock`s on a per-test basis.
  - Required test cases (names are suggestions; match spec Requirement 6 + Requirement 1 local-backup coverage):
    - `test_rmw_preserves_existing_fields` — existing has `balanceTaste="bitter"`, caller passes only `notes="hi"`; assert captured `_send_request` call received merged dict with both.
    - `test_empty_sidecar_stringifies_dose_and_ratio` — existing is `None`, caller passes `dose_in=22.0, dose_out=55.0`; assert captured payload has `"doseIn": "22.0"`, `"doseOut": "55.0"`, `"ratio": "2.5"` (all strings).
    - `test_defensive_non_dict_existing` — `get_shot_notes` returns `"oops"`; caller passes `rating=3`; no exception; payload built as empty-merge.
    - `test_noop_short_circuit` — existing `{"id": "246", "rating": 3}`, caller passes `rating=3`; assert `mock_send_request.call_count == 0` (the `get_shot_notes` call is mocked separately and doesn't go through `_send_request`, so 0 is exact).
    - `test_existing_dose_strings_preserved` — existing has `"doseIn": "18.0"` (string); caller passes no dose fields; assert payload's `doseIn` is still `"18.0"` exactly (not `18.0` float, not stripped).
    - `test_tool_passes_bean_type_to_both_sinks` — calls `manage_shot_notes(shot_id="999", bean_type="TEST-BEAN", sync_to_device=False)` with a temp `GAGGIMATE_STORAGE_PATH`; assert: (a) the ratings.json file at `{temp_path}/ratings.json` has the `"000999"` entry with `"bean_type": "TEST-BEAN"`. (b) separately, with `sync_to_device=True` and a mocked `ws_client.save_shot_notes`, assert `ws_client.save_shot_notes` was called with `bean_type="TEST-BEAN"` in its kwargs. Covers Spec Requirement 1's local-backup AC and Requirement 2's transport AC in one test.
  - Pattern reference for async mocking in Python: `AsyncMock` used as `instance.method = AsyncMock(return_value=X)` then `await instance.method(...)`.
  - Use `shot_id="246"` throughout RMW tests (so `normalized_id` is `"246"`). For the tool-layer test, use `shot_id="999"` to avoid collision with any live ratings.
  - Captured payload accessed via `mock_send_request.call_args.kwargs["notes"]` — this matches the call-site contract locked in by Task 1's Context.
  - Tool-layer test setup: use `monkeypatch.setenv("GAGGIMATE_STORAGE_PATH", str(tmp_path))` to redirect RatingStorage to a temp dir. Re-import `gaggimate_mcp.server` after setting env so the module-level `rating_storage` picks it up — or pass the config explicitly. If that's awkward, instantiate `RatingStorage(GaggimateConfig(storage_path=str(tmp_path)))` and patch `server.rating_storage` for the test.
- **Verification**:
  - `cd mcp && python -m pytest tests/test_save_shot_notes_rmw.py -q` — pass if exit 0 and all 6 tests pass.
  - `ls mcp/tests/__init__.py` and `ls mcp/tests/test_save_shot_notes_rmw.py` both succeed — pass if both files exist.
- **Status**: [x] completed (6/6 pass after Task 1 follow-up gate fix in 646e4f0)

### Task 4: Update `/feedback` skill to pass `bean_type`
- **Files**: `~/.claude/skills/feedback/SKILL.md`
- **What**: Add guidance in the skill's `manage_shot_notes` call section instructing: (a) read `user-setup.md` → Active Coffee section; (b) if present and not the placeholder `No active coffee`, pass the coffee's display title as `bean_type` (truncated to 200 chars); (c) if the user's feedback prose explicitly names a different bean, prefer the user's; (d) if Active Coffee is absent/placeholder, omit `bean_type` entirely.
- **Depends on**: [2]
- **Complexity**: simple
- **Context**:
  - Skill file at `~/.claude/skills/feedback/SKILL.md`. Find the section that describes the `manage_shot_notes` MCP call — likely a code block or a bulleted list of parameters. Add `bean_type` as a parameter with the source-rule bullets above.
  - The Active Coffee section in `user-setup.md` is a markdown table with columns including the coffee title. Parse the title from the first row. If the file contents contain `No active coffee`, treat as absent.
  - Do NOT hardcode a specific coffee title; the skill reads `user-setup.md` at runtime.
  - Truncation rule: `bean_type[:200]` — no mid-word boundary fanciness needed.
- **Verification**:
  - `grep -c "bean_type" ~/.claude/skills/feedback/SKILL.md` ≥ 2 — pass if count ≥ 2.
  - `grep -q "Active Coffee" ~/.claude/skills/feedback/SKILL.md` — pass if grep succeeds (exit 0).
  - `grep -qE "(200|truncat)" ~/.claude/skills/feedback/SKILL.md` — pass if either "200" or "truncat" (truncate/truncation) appears, confirming truncation rule is documented.
- **Status**: [x] completed (edited project-scoped `.claude/skills/feedback/SKILL.md`; ~/.claude path in spec did not exist on this machine)

### Task 5: Live integration verification
- **Files**: `research/gaggimate-1-8-0-upgrade/verification-notes.md` (append-only)
- **What**: Execute the four-step clobber-prevention live check from spec Requirement 7: (a) native-edit shot with `beanType`, `doseIn`, `doseOut`; (b) MCP `manage_shot_notes(rating=4)` only; (c) MCP `action=get` confirm all four fields survived; (d) native shot list shows non-zero weight. Record pass/fail per bullet in a dated entry.
- **Depends on**: [1, 2, 3, 4]
- **Complexity**: simple
- **Context**:
  - Verification template exists in `research/gaggimate-1-8-0-upgrade/verification-notes.md`. Append a new dated section; do not overwrite the existing 2026-04-18 entry.
  - User must perform the native-editor edits in the browser — the agent cannot do that via MCP.
  - After user confirms native edit is saved, agent runs the MCP `update` (rating only) and `get` calls, then shows the returned notes dict for side-by-side verification with the user.
  - User must also eyeball the native shot list to confirm the weight column for the target shot.
- **Verification**: Interactive/session-dependent: requires a live device, the user's native-editor interaction, and a visual check of the shot list — cannot be asserted by a shell command. Pass criterion: user confirms in-session that (a) the MCP `action=get` response contains all four native-set fields unchanged, AND (b) the native shot list shows the correct weight (non-zero). The `verification-notes.md` entry is documentation of this confirmation, not the evidence itself.
- **Status**: [x] completed (2026-04-19 live test on shot 249: beanType/doseIn/doseOut/ratio/balanceTaste all preserved after MCP rating-only update; native shot list weight column shows 49.6g; entry appended to `research/gaggimate-1-8-0-upgrade/verification-notes.md`)

## Verification Strategy

End-to-end: run Task 3's pytest (validates RMW + wire types at unit level) → confirm Task 1 and 2's signature-presence checks → confirm Task 4's skill grep — all shell-assertable. The definitive correctness proof is Task 5's live integration test, which exercises the full stack (MCP tool → WS transport → firmware → sidecar → firmware read → tool) and confirms the clobber bug is fixed AND the secondary index-volume bug is fixed.

After Task 5 completes, close backlog 014 with `update-item status=complete lifecycle_phase=complete`.

## Veto Surface

- **Task 1 is a single complex task** — combining RMW, string coercion, id handling, ratio, no-op, defensive parsing, and the new `bean_type` param into one function rewrite. Alternative: split into "mechanical additions" (bean_type + string coercion + id) and "structural change" (RMW + no-op). The combined approach is defensible because all these changes share the same function context — splitting would force context reloading. Open to split if preferred.
- **No-op short-circuit reuses `_send_request` synthetic response** — the shape `{"msg": "no-op: unchanged"}` is invented by us; if downstream consumers expect specific keys we'd break them. Current callers only log the msg field, so this is safe, but worth calling out.
- **Task 4 path is absolute** (`~/.claude/skills/feedback/SKILL.md`). If the user has the skill elsewhere or the project should use a local skill copy, the path differs. Verified: skill is at the absolute path.
- **`pytest-asyncio` assumed available** — if it isn't in `mcp/pyproject.toml`, Task 3 adds it. This is a dev-dep change that extends scope slightly; if disallowed, fall back to `asyncio.run(...)` inside sync tests (uglier but works).

## Scope Boundaries

Maps to spec Non-Requirements. Explicit exclusions:
- No direct sidecar file writes outside WebSocket path.
- No support for firmware <1.8.0 or version gating.
- No new sidecar fields beyond the 10-field schema.
- No CAS/conflict detection.
- No retroactive migration of existing `ratings.json`.
- No changes to `[Updated by AI]:` prefix logic.
- No changes to `list_recent_shots` or other MCP tools.
- No broader MCP test harness (that's ticket 016).
- No changes to `manage_shot_notes` response envelope.
- No `id` padding — unpadded integer string only.
