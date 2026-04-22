# Plan: add-profile-select-action-to-manage-profile-mcp-tool

## Overview

Seven tasks: transport method (1) → server.py split into happy-path (2) and edge-path (3) for natural commit points → tests (4, 5) → skill (6) → live verification with failure semantics (7). The spec is dense and prescriptive, so each code task is a direct translation of a numbered spec requirement; each test task pins the acceptance criteria named in the spec. Task 2 and Task 3 partition the server.py edit to respect the plan's 5-15 min sizing rule.

## Tasks

### Task 1: Add `WebSocketClient.select_profile` method [x]
- **Files**: `mcp/src/gaggimate_mcp/api/websocket.py`
- **What**: Add a public method `select_profile(self, profile_id: str) -> dict` next to `save_profile` / `delete_profile`, and add `req:profiles:select` to the module docstring's list of request types. The method wraps `_send_request` with request type `"req:profiles:select"`, passing `id=profile_id`, and passes through its return dict unmodified.
- **Depends on**: none
- **Complexity**: simple
- **Context**:
  - Pattern to follow: the existing `delete_profile(self, profile_id: str)` method immediately above — same signature shape, same `_send_request` usage, same response-dict passthrough.
  - Signature: `def select_profile(self, profile_id: str) -> dict`.
  - Call: `self._send_request("req:profiles:select", request_id, id=profile_id)` where `request_id = generate_request_id()` matches the existing helpers' pattern.
  - Return: pass through the dict returned by `_send_request` (the parsed `res:profiles:select` body, carrying only `{tp, rid, error?}` per the AsyncAPI spec — no profile payload). This pass-through is load-bearing: Task 4 pins it explicitly.
  - Error propagation: `_send_request` raises `GaggimateError` with codes `WEBSOCKET_ERROR` / `TIMEOUT` / `PARSE_ERROR` / `API_ERROR` when transport or response conditions fail. `select_profile` does NOT catch, wrap, or log these — they propagate unchanged. A defensive `try/except GaggimateError: return None` would silently violate the contract.
  - Module docstring: append a line like `- Select profile: req:profiles:select` to the existing request-type list at the top of the module.
- **Verification**: `grep -c 'def select_profile' mcp/src/gaggimate_mcp/api/websocket.py` = 1 — pass if count = 1. `grep -c 'req:profiles:select' mcp/src/gaggimate_mcp/api/websocket.py` ≥ 2 — pass if ≥ 2 (one in docstring, one in the method call). Task 4's pass-through and error-propagation tests are the true correctness signal.
- **Status**: [ ] pending

### Task 2: Implement `select` action happy path + pre-validate in `manage_profile` [x]
- **Files**: `mcp/src/gaggimate_mcp/server.py`
- **What**: Add a new `elif action == "select":` branch to `manage_profile` covering: (a) input validation (both of id/name supplied → `INVALID_INPUT`; neither supplied → `INVALID_INPUT`; empty string for either → treated as missing for that slot); (b) name resolution via `ws_client.list_profiles()` with exact case-sensitive `label` match (zero matches → `PROFILE_NOT_FOUND`; multiple matches → `INVALID_INPUT`); (c) pre-validate via `load_profile` with `None` → raise `GaggimateError(PROFILE_NOT_FOUND)`; (d) the `select_profile` call; (e) the post-select `list_profiles()` refetch; (f) happy-path return `{"success": true, "action": "select", "profiles": [...], "count": N}`. All error returns on this task use the four-field shape `{success, action, error, error_code, suggestion}`. Error codes produced: `PROFILE_NOT_FOUND`, `INVALID_INPUT`, plus whatever `_send_request` raises and propagates to this handler (`WEBSOCKET_ERROR`, `TIMEOUT`, `PARSE_ERROR`, `API_ERROR`). Divergence detection, partial-success branch, docstring, and unknown-action string are Task 3.
- **Depends on**: [1]
- **Complexity**: complex
- **Context**:
  - Primary guide: spec §§R1–R8 (ignore R7 divergence details for this task — covered by Task 3).
  - File layout: `manage_profile` lives at `mcp/src/gaggimate_mcp/server.py` lines ~98–461. Action dispatch is an if/elif chain ending in an `else:` that raises "Unknown action". Insert the new `elif action == "select":` between the existing `delete` branch and the `else:`.
  - Error-shape template: server.py's `except GaggimateError` handler (around lines 449–453) emits the four-field shape via `_get_error_suggestion(e)`. Model the select branch's error returns on that exact shape for all error codes. **Do NOT model on `get`/`update`/`delete`'s validation branches** — those emit a bare two-field shape and the spec explicitly forbids matching them (see spec §R8 and Technical Constraints). The implementer must resist the nearest-neighbor pattern.
  - `load_profile` behavior: `mcp/src/gaggimate_mcp/api/websocket.py` lines 155–182 — returns `None` for missing profiles, does NOT raise. The select branch's pre-validate must check for `None` and explicitly `raise GaggimateError(ErrorCode.PROFILE_NOT_FOUND, f"Profile not found: {profile_id}")`. Do NOT modify `load_profile` itself.
  - Name resolution: when `profile_name` is given, call `ws_client.list_profiles()`, iterate profiles matching `label == profile_name` exactly (case-sensitive).
  - Happy-path return: after `select_profile` returns without error AND `list_profiles()` refetch succeeds, return `{"success": true, "action": "select", "profiles": [...], "count": N}`. For THIS task, do not add the divergence check — that is Task 3. Treat `list_profiles` refetch failure as propagating the underlying error for now (Task 3 will wire the partial-success branch).
  - Error-code constants: use `ErrorCode.PROFILE_NOT_FOUND`, `ErrorCode.INVALID_INPUT`, `ErrorCode.WEBSOCKET_ERROR`, `ErrorCode.TIMEOUT`, `ErrorCode.PARSE_ERROR`, `ErrorCode.API_ERROR` from `mcp/src/gaggimate_mcp/errors.py`. `PROFILE_NOT_FOUND` and `INVALID_INPUT` have zero raise sites in the codebase today — this task is their first raise site.
  - Partial commit safety: if this task lands complete but Task 3 is pending, the repo has a `select` action that works for happy paths and pre-validation errors but treats list-refetch-failure as propagating the transport error (vs. the spec's partial-success return). This is a deliberate transitional state — Task 3 completes it before Tasks 5/6 run.
- **Verification**: 
  - `grep -cE '^\s*elif action == "select"' mcp/src/gaggimate_mcp/server.py` = 1 — pass if exactly one.
  - `grep -c 'ErrorCode.PROFILE_NOT_FOUND' mcp/src/gaggimate_mcp/server.py` ≥ 1 — pass if ≥ 1 (first raise site).
  - `grep -c 'ErrorCode.INVALID_INPUT' mcp/src/gaggimate_mcp/server.py` ≥ 1 — pass if ≥ 1 (first raise site).
  - The subset of Task 5 tests exercising pre-validate + name resolution + happy path pass: `python -m pytest mcp/tests/test_manage_profile_select.py -k 'resolves_profile_name or rejects_both or rejects_neither or prevalidates_with_load or prevalidate_ws_failure or returns_full_updated_list' -v` — pass if exit 0.
- **Status**: [ ] pending

### Task 3: Add divergence detection, partial-success branch, docstring, unknown-action update [x]
- **Files**: `mcp/src/gaggimate_mcp/server.py`
- **What**: Extend the `select` branch from Task 2 with: (a) post-condition divergence check — after `list_profiles()` returns, inspect for the target id; if not marked `selected: true`, return `success: false` with `error_code: "api_error"` and the Selection-divergence error message from spec §R7 (include the full `profiles` list in the response); (b) partial-success branch — when `list_profiles()` raises after `select_profile` succeeded, catch the exception and return `{"success": true, "action": "select", "selected_profile_id": "<id>", "profiles_refetch_failed": true, "warning": "..."}` with no `profiles` key; (c) update the `manage_profile` tool docstring to enumerate `select` alongside the other actions; (d) update the "Unknown action" error message string from `"Use: list, get, create, update, delete"` to `"Use: list, get, create, update, delete, select"`.
- **Depends on**: [2]
- **Complexity**: complex
- **Context**:
  - Primary guide: spec §R6 (partial success), §R7 (divergence), §R8 (error shape remains four-field), §R10 (docstring + unknown-action string).
  - Divergence logic: after `list_profiles()` succeeds, walk the returned list; find the entry with `id == target_id`; if its `selected` field is not `true`, build the divergence error. Include in the error message: the target id, the id of whichever profile (if any) is actually `selected: true` in the returned list, and the "Selection divergence" literal substring (Task 5's test asserts it).
  - Partial-success structure: wrap the `list_profiles()` call in a try/except `GaggimateError`. On exception, the `select_profile` call already succeeded — build the success response WITHOUT a `profiles` key, WITH `selected_profile_id`, `profiles_refetch_failed: true`, and a `warning` string that includes the refetch error's message. Do NOT set `success: false`.
  - Docstring: find the `manage_profile` tool docstring (around server.py line 98). Add a one-line entry for `select` alongside the other five action descriptions. Keep the rest of the docstring unchanged.
  - Unknown-action message: literal string change. The result must match the exact string `"Use: list, get, create, update, delete, select"` (spec acceptance uses `grep -F` literal match).
- **Verification**:
  - `grep -F 'list, get, create, update, delete, select' mcp/src/gaggimate_mcp/server.py` exits 0 — pass if found.
  - `grep -c '"select"' mcp/src/gaggimate_mcp/server.py` ≥ 3 — pass if ≥ 3 (dispatch, unknown-action message, docstring).
  - `grep -c 'Selection divergence' mcp/src/gaggimate_mcp/server.py` ≥ 1 — pass if ≥ 1.
  - `grep -c 'profiles_refetch_failed' mcp/src/gaggimate_mcp/server.py` ≥ 1 — pass if ≥ 1.
  - The remaining Task 5 tests exercising divergence, partial success, full error shape, and unknown-action enumeration pass: `python -m pytest mcp/tests/test_manage_profile_select.py -k 'partial_success or detects_selection_divergence or error_shape_all_codes or unknown_action_lists_select' -v` — pass if exit 0.
- **Status**: [ ] pending

### Task 4: Unit tests for `select_profile` WS method (strengthened) [x]
- **Files**: `mcp/tests/test_api_websocket.py`
- **What**: Add five tests covering `WebSocketClient.select_profile`:
  - `test_select_profile_sends_correct_request` — mocks `_send_request`, calls `ws_client.select_profile("abc-123")`, asserts the mock was called with `request_type="req:profiles:select"` and `id="abc-123"`.
  - `test_select_profile_passes_through_response_dict` — mocks `_send_request` to return a fixed dict like `{"tp": "res:profiles:select", "rid": "r1"}`; asserts `select_profile` returns that exact dict unmodified.
  - `test_select_profile_propagates_websocket_error` — mocks `_send_request` to raise `GaggimateError(WEBSOCKET_ERROR, "conn refused")`; asserts `select_profile` propagates the same `GaggimateError` (use `pytest.raises`) with the same error code.
  - `test_select_profile_propagates_timeout` — mocks `_send_request` to raise `GaggimateError(TIMEOUT)`; asserts propagation.
  - `test_select_profile_propagates_api_error` — mocks `_send_request` to raise `GaggimateError(API_ERROR, "<firmware msg>")`; asserts propagation and that the error message is preserved.
- **Depends on**: [1]
- **Complexity**: simple
- **Context**:
  - Pattern to follow: existing `test_save_profile_success` and (for the raise tests) any existing test that uses `pytest.raises(GaggimateError)` in `mcp/tests/test_api_websocket.py`.
  - The raise tests pin the "does not catch or re-wrap" half of Task 1's contract. Without them a defensive try/except would silently pass.
  - PARSE_ERROR path is covered transitively by the shape of `_send_request`'s own raise behavior; if requested, add `test_select_profile_propagates_parse_error` following the same template — not strictly required because PARSE_ERROR propagates through the same catch-and-pass-through path as the others.
- **Verification**: `python -m pytest mcp/tests/test_api_websocket.py -k 'select_profile' -v` — pass if exit 0 AND stdout contains 5 "PASSED" lines.
- **Status**: [ ] pending

### Task 5: Unit tests for `manage_profile(action="select", ...)` [x]
- **Files**: `mcp/tests/test_manage_profile_select.py` (new file)
- **What**: Write 10 named tests:
  - `test_select_resolves_profile_name_to_id`
  - `test_select_rejects_both_id_and_name`
  - `test_select_rejects_neither_id_nor_name`
  - `test_select_prevalidates_with_load` (mocks `load_profile` → `None`, asserts `_send_request` NOT called with `req:profiles:select` and response carries `error_code: "profile_not_found"`)
  - `test_select_prevalidate_ws_failure_propagates` (mocks `load_profile` to raise `GaggimateError(WEBSOCKET_ERROR)`, asserts response carries `error_code: "websocket_error"`)
  - `test_select_returns_full_updated_list` (happy path — target id shows `selected: true` post-list)
  - `test_select_partial_success_list_fails` (mocks `_send_request` to succeed for `req:profiles:select` and raise for `list_profiles`; asserts `success: true`, `selected_profile_id` present, `profiles_refetch_failed: true`, no `profiles` key)
  - `test_select_detects_selection_divergence` (mocks list to return a list where a DIFFERENT profile is `selected: true`; asserts `success: false`, `error_code: "api_error"`, `error` contains "Selection divergence", `profiles` is present)
  - `test_select_error_shape_all_codes` (parametrized over `profile_not_found`, `websocket_error`, `timeout`, `parse_error`, `api_error`, `invalid_input`; asserts each response has all five keys `success`, `action`, `error`, `error_code`, `suggestion`)
  - `test_manage_profile_unknown_action_lists_select` (calls tool with action="bogus"; asserts returned error string contains `select`)
- **Depends on**: [3]
- **Complexity**: simple
- **Context**:
  - Pattern to follow: existing profile-related tests in `mcp/tests/` (whatever location currently tests `manage_profile` actions — likely `test_server.py` or a similar file). Match its fixture style (mock `WebSocketClient`, patch methods, pass the mocked client into `manage_profile`).
  - Mock strategy: mock at the `WebSocketClient` method level (`list_profiles`, `load_profile`, `select_profile`) for most tests. `test_select_prevalidate_ws_failure_propagates` mocks `load_profile` raising. `test_select_partial_success_list_fails` needs fine-grained control: mock `select_profile` to succeed, mock `list_profiles` to raise. For `test_select_error_shape_all_codes`, the parametrize can mock the appropriate method-layer raise for each error code.
- **Verification**: `python -m pytest mcp/tests/test_manage_profile_select.py -v` — pass if exit 0 AND stdout contains 10 "PASSED" lines with the 10 listed test names.
- **Status**: [ ] pending

### Task 6: Update `/new-coffee` skill to create+select [x]
- **Files**: `.claude/skills/new-coffee/SKILL.md`
- **What**: Edit the upload section of the skill so it (a) calls `manage_profile(action="create", ...)` as it does today, (b) captures the return into a variable named `created_profile`, (c) checks `created_profile["success"]` and short-circuits to the user with the error message if `False`, (d) on success extracts `created_profile["profile"]["id"]` and calls `manage_profile(action="select", profile_id=<that id>)`, (e) checks the select response and surfaces any `success: false` error rather than claiming activation.
- **Depends on**: [3]
- **Complexity**: simple
- **Context**:
  - Current upload-step location: `.claude/skills/new-coffee/SKILL.md` around lines 107–114 (per research — confirm during implement).
  - The skill is markdown with LLM-interpreted pseudocode. "Variable" capture means writing the pattern in prose/pseudocode the agent will follow at runtime.
  - Banned pattern: literal-string `profile_id="..."` anywhere in the file (acceptance grep explicitly rejects this).
  - Required prose: a sentence referencing `success": false` (or `success: false` or `create failed` or `If create returns`) in the same section as the create call, explaining what happens on failure.
- **Verification**:
  - `grep -c 'manage_profile(action="create"' .claude/skills/new-coffee/SKILL.md` ≥ 1 — pass if ≥ 1.
  - `grep -c 'manage_profile(action="select"' .claude/skills/new-coffee/SKILL.md` ≥ 1 — pass if ≥ 1.
  - `grep -cE 'profile_id="[^"{]*"' .claude/skills/new-coffee/SKILL.md` = 0 — pass if exactly 0 (no hardcoded string ids).
  - `grep -cE 'success": false|success: false|create failed|If create returns' .claude/skills/new-coffee/SKILL.md` ≥ 1 — pass if ≥ 1.
- **Status**: [ ] pending

### Task 7: End-to-end interactive verification on device (with failure semantics) [x]
- **Files**: none (verification-only task; no file changes)
- **What**: With the Gaggimate device powered on and reachable, run an end-to-end `/new-coffee` session with an already-researched coffee (user picks one). Confirm the skill uploads a new profile, the skill then calls select automatically, and `manage_profile(action="list")` immediately after shows the new profile with `selected: true` and every other profile in the list shows `selected: false`.
- **Depends on**: [3, 4, 5, 6]
- **Complexity**: simple
- **Context**:
  - Pre-flight: restart the MCP server after Task 3 lands so the new code is loaded (the MCP is a long-running process; code changes don't hot-reload).
  - Walk-through: user invokes `/new-coffee <bag info>`. The skill does its research/profile-design, proposes a profile, uploads on user approval. At upload time it now also selects.
  - Success criteria: (a) `/new-coffee` does not prompt the user to tap the profile on the device screen; (b) the next `manage_profile(action="list")` response shows exactly one profile with `selected: true` and that profile's `id` matches the just-created profile's `id`.
  - **Failure handling (explicit loop-back targets)**:
    - **If `/new-coffee` errors out because `create`'s response shape differs from what the skill expects** (id lives under a different key, or `success` is shaped differently): leave Task 7 pending, loop back to Task 6 (skill edit) to fix the extraction pattern; if the MCP `create` action itself is found to need a response-shape adjustment, loop back to Task 3 instead.
    - **If create succeeds but select fires before the device has indexed the new profile and the select fails (firmware race)**: leave Task 7 pending, do NOT modify Task 2 or Task 3 to add a retry — Scope Boundaries explicitly forbids retry loops in the MCP for this feature. File a new backlog ticket for the race with the observed symptoms, mark this feature's lifecycle as blocked on that ticket, and present the user with the choice to (i) land the current work with the race as a known follow-up or (ii) park the lifecycle until the race ticket is addressed.
    - **If the skill appears to claim activation when the MCP returned `success: false`**: leave Task 7 pending, loop back to Task 6 to fix the skill's response-checking prose. This is a skill-layer bug, not an MCP-layer bug.
  - **Completion criterion for Task 7**: the checkbox may be marked `[x]` ONLY when the success criteria above all hold AND no failure mode is known-unresolved. "Check the box and leave it to followup" is not a valid completion path for this task.
- **Verification**: Interactive/session-dependent: running `/new-coffee` end-to-end requires a physical Gaggimate device, a ready coffee bag, and user judgment on whether the flow completed without manual intervention. No headless script can substitute. Pass if both success criteria hold; fail and loop back per the Failure handling block otherwise.
- **Status**: [ ] pending

## Verification Strategy

Layered gates, each with a defined failure path:
- Tasks 4–5 prove the MCP surface behaves correctly under mocked transport. Task 4 pins the WS method's pass-through + error-propagation contract (closing the gap that prior single-test coverage left open); Task 5 pins every named acceptance criterion from spec §§R1–R10.
- Task 6's greps prove the skill contains both calls with the correct pattern shape and no hardcoded ids.
- Task 7 is the one gate that exercises the MCP↔firmware↔skill loop end-to-end. It is the only test that can catch mismatches between the mocked WS behavior and the real device (e.g., firmware races, id-shape drift between `create`'s response and `select`'s expectations). Task 7 is NOT droppable — failure loops back to the specific earlier task per the Failure handling block in Task 7's Context.

## Veto Surface

- **Task 4's expansion from 1 test to 5** — the original plan had 1 test at this layer; the expanded set pins pass-through and error propagation. If the user considers this over-testing for a 5-line method, they can reduce to 3 (args, pass-through, one representative raise propagation) with the trade-off that a defensive try/except regression would pass silently.
- **Task 5's test count (10)** — single file, all ten tests named by the spec acceptance blocks. If the user prefers splitting into two files (input-validation tests vs return-shape tests), that's a reasonable veto; it adds file fan-out without changing coverage.
- **Split of Task 2/3 vs a single server.py task** — the split was chosen to respect the 5-15 min sizing rule and give a natural commit point between happy path and edge paths. If the user prefers a single bundled task for review simplicity, that's a reasonable veto; the trade-off is that a partial-completion recovery path (half-landed branch) becomes more expensive.
- **R9's four static grep acceptance checks** — if any feel like over-specification of the skill's markdown shape (especially the `success": false` regex), they can be relaxed with user approval. The tradeoff is weaker static gating on a file that is LLM-interpreted and hard to test otherwise.

## Scope Boundaries

Matches spec's Non-Requirements section:
- No repo-side mirror of the active-profile pointer.
- No HTTP transport for profile operations.
- No firmware-side changes.
- No `req:profiles:save`-with-`selected:true` path.
- No paired deselect of the previously-active profile.
- No active-shot guard in the MCP.
- No change to the `selected` field on save payloads (`create_or_update_profile` continues to write `"selected": false`).
- No new MCP tool — `select` is an action on the existing `manage_profile`.
- No modification to `load_profile`'s return semantics.
- No retry loop in the MCP for selection divergence.
- No atomicity guarantee across the 4-round-trip sequence.
- **Firmware-race mitigation (e.g., wait-between-create-and-select)** is explicitly out of scope for this ticket — if Task 7 reveals a race, per Task 7's Failure handling the work halts and a new ticket is filed rather than adding retry/wait logic to Task 2 or Task 3.
