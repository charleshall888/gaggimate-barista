# Review: add-profile-select-action-to-manage-profile-mcp-tool

## Stage 1: Spec Compliance

### Requirement R1: New `select` action on `manage_profile`
- **Expected**: `grep -c '"select"' mcp/src/gaggimate_mcp/server.py` ≥ 3 (dispatch branch, "Use:" error message, docstring enumeration); `elif action == "select":` branch inside `manage_profile`.
- **Actual**: `grep -c '"select"'` returns 5. `elif action == "select":` present at line 449. Docstring enumerates `'select'` at line 123. "Use:" error message at line 586 contains `select`.
- **Verdict**: PASS

### Requirement R2: Accept either `profile_id` or `profile_name`
- **Expected**: Exactly one must be supplied. `profile_name` resolves via `req:profiles:list` label match (case-sensitive). Three unit tests: `resolves_profile_name_to_id`, `rejects_both_id_and_name`, `rejects_neither_id_nor_name`.
- **Actual**: Implementation at lines 464-495 treats empty strings as absent, enforces the mutex, performs case-sensitive label matching via `list_profiles()`, handles zero-match (`PROFILE_NOT_FOUND`) and multi-match (`INVALID_INPUT`) cases. All three required tests present and pass. `test_select_resolves_profile_name_to_id` uses `side_effect=[SAMPLE_PROFILES, updated_profiles]` to cover both the name-resolution list call and the post-select refresh, and asserts `mock_select.assert_called_once_with(TARGET_ID)`.
- **Verdict**: PASS

### Requirement R3: Pre-validate via `req:profiles:load` before select
- **Expected**: `load_profile` called before `select_profile`. `None` return raises `GaggimateError(PROFILE_NOT_FOUND)`. WS failure from `load_profile` surfaces without calling select. Two tests: `prevalidates_with_load`, `prevalidate_ws_failure_propagates`.
- **Actual**: Lines 499-504 call `load_profile(_pid)` and translate `None` into `GaggimateError(PROFILE_NOT_FOUND, ...)`. `load_profile`'s return semantics are not modified (confirmed — `load_profile` still returns `None` as before). Both required tests present, pass, and assert `mock_select.call_count == 0`.
- **Verdict**: PASS

### Requirement R4: WebSocket request shape `{tp: "req:profiles:select", rid, id}`
- **Expected**: New `WebSocketClient.select_profile(profile_id: str) -> dict` in `websocket.py` using `_send_request("req:profiles:select", request_id, id=profile_id)`. Module docstring updated to list `req:profiles:select`. Unit test `test_select_profile_sends_correct_request` exits 0.
- **Actual**: `select_profile` added at lines 235-257, mirrors `delete_profile` shape exactly. Module docstring at line 7 lists `- Select profile: req:profiles:select`. Test asserts `call_args[0][0] == "req:profiles:select"` and `call_args[1]["id"] == "abc-123"`. All 5 WS tests pass.
- **Verdict**: PASS

### Requirement R5: Return shape on happy path
- **Expected**: `{"success": true, "action": "select", "profiles": [...], "count": N}` where target id shows `selected: true` in returned list.
- **Actual**: Lines 571-576 return exactly this shape. `test_select_returns_full_updated_list` mocks the post-select list with target `selected:true`, asserts all four keys present and `count == len(profiles)`.
- **Verdict**: PASS

### Requirement R6: Partial-success when select lands but list refetch fails
- **Expected**: `{"success": true, "action": "select", "selected_profile_id": "<id>", "profiles_refetch_failed": true, "warning": "..."}` with `profiles` key **omitted**. Return `success: true` (not `false`) — the critical inversion point addressed by the /critical-review.
- **Actual**: Lines 514-532 catch `GaggimateError` from `list_profiles()` and return the exact partial-success shape with `success: True`. The `profiles` key is absent from this branch. `test_select_partial_success_list_fails` asserts `success: True`, `selected_profile_id == TARGET_ID`, `profiles_refetch_failed is True`, and `"profiles" not in result`. The semantic inversion from pre-critical-review (was `success: false`) is correctly applied — `success: true` throughout.
- **Verdict**: PASS

### Requirement R7: Post-condition divergence detection
- **Expected**: After successful list refetch, target id must show `selected: true`. If not, return `{"success": false, "error_code": "api_error", "error": "...<contains 'Selection divergence'>...", "profiles": [...]}`.
- **Actual**: Lines 539-569 inspect the refetched list for the target id. If absent or not `selected`, constructs `GaggimateError(API_ERROR, "Selection divergence: ...")` and returns the five-field shape plus `profiles`. `test_select_detects_selection_divergence` mocks the list with a different profile selected, asserts `success: False`, `error_code: "api_error"`, `"Selection divergence" in result["error"]`, and `"profiles" in result`. The literal substring "Selection divergence" is present in the error message at line 549.
- **Verdict**: PASS

### Requirement R8: Five-field error shape consistently on every failure path
- **Expected**: Every failure path emits `{success, action, error, error_code, suggestion}` — all five keys always. Inner `_select_error` helper used, not the bare `{success, error}` shape from `get`/`update`/`delete`. Parametrized test over all six error codes.
- **Actual**: Inner `_select_error` at lines 452-460 emits exactly five fields including `action`. The inner `try/except GaggimateError` at lines 578-581 routes all GaggimateErrors through `_select_error`. This is structurally isolated from the outer handler (lines 589-596) which emits four fields without `action` — but the outer handler cannot be reached by GaggimateErrors from inside the select branch since the inner except catches them first. Divergence response (lines 559-569) is a direct `return` that includes all five fields plus `profiles`. Partial-success path (lines 522-532) is `success: true` so R8's error shape doesn't apply to it. `test_select_error_shape_all_codes` parametrizes over all 6 codes (profile_not_found, websocket_error, timeout, parse_error, api_error, invalid_input), all 15 tests pass.
- **Verdict**: PASS

### Requirement R9: `/new-coffee` skill calls select after create with create-failure short-circuit
- **Expected**: SKILL.md has `manage_profile(action="create")` call, captures result, checks `success: false` → stops, then calls `manage_profile(action="select", profile_id=<extracted>)`, checks select success. No hardcoded `profile_id="..."` string literal.
- **Actual**:
  - `grep -c 'manage_profile(action="create"'` = 1 (Step 6 of SKILL.md)
  - `grep -c 'manage_profile(action="select"'` = 1 (Step 6, after create)
  - `grep -cE 'profile_id="[^"{]*"'` = 0 (no hardcoded string literal)
  - Create-failure prose: "If create returns `success: false`, surface the error message to the user and stop — do not proceed to save or select."
  - Select-failure prose: "If `select_response["success"]` is false, report the error..."
  - Id extraction: `manage_profile(action="select", profile_id=created_profile["profile"]["id"])` — uses the variable reference, not a hardcoded string.
  - Interactive verification (Task 7): confirmed live via `manage_profile(action="list")` showing exactly one `selected: true` matching the just-created profile.
- **Verdict**: PASS

### Requirement R10: Action list and tool docstring updated
- **Expected**: Unknown-action error message ends with `, select` (exact literal `"Use: list, get, create, update, delete, select"`). Docstring enumerates `select`.
- **Actual**: `grep -F 'list, get, create, update, delete, select' mcp/src/gaggimate_mcp/server.py` exits 0 and matches line 586. Docstring at lines 123-126 describes `select` with a one-line summary plus a note about active-shot forwarding. `test_manage_profile_unknown_action_lists_select` asserts `"select" in result["error"]` — passes.
- **Verdict**: PASS

### Scope Boundaries / Non-Requirements Check
- No repo-side mirror: `select` branch writes nothing to `user-setup.md`, `coffees/`, or `.data-repo-path`. Confirmed — no file-write calls anywhere in the select branch.
- No HTTP transport: `api/http.py` not touched by any of the six commits.
- No firmware changes: not applicable.
- No `req:profiles:save` fallback: only `req:profiles:select` used.
- No paired deselect: no explicit deselect call.
- No active-shot guard: forwarded to firmware as documented.
- No `selected: true` on save: `create_or_update_profile` still writes `"selected": False` (pre-existing behavior).
- No new standalone tool: `select` is an action on existing `manage_profile`.
- No modification to `load_profile` return semantics: `load_profile` still returns `None` for missing profiles; `select` translates `None` internally.
- No retry loop: divergence returns error to caller, no re-attempt.
- **Verdict**: All scope boundaries respected.

---

## Requirements Drift

**State**: none
**Findings**:
- None
**Update needed**: None

---

## Stage 2: Code Quality

- **Naming conventions**: Consistent with project patterns. `select_profile` mirrors `save_profile` / `delete_profile`. `_select_error` follows the local helper convention. `_pid` / `_pname` are clear local temporaries. Log keys (`selecting_profile_via_action`, `select_profile_list_refetch_failed`, `manage_profile_select_divergence`, `manage_profile_select_error`) match the existing `snake_case_event_name` structured logging style.

- **Error handling**: The nested `try/except GaggimateError` inside the `select` branch is the correct architectural choice. It ensures all GaggimateErrors from the select path (input validation, name resolution, load_profile, select_profile) are caught locally and routed through `_select_error` (five-field shape with `action`), preventing them from leaking to the outer handler (four-field shape, no `action`). The split-brain catch at lines 514-516 is a narrowly-scoped inner-inner try that handles only the list refetch, returning partial success without treating refetch failure as a fatal error. This layering is well-structured and matches the spec's intent.

- **Test coverage**: 15 tests in `test_manage_profile_select.py` (9 named + 6 parametrized rows) and 5 tests in `test_api_websocket.py::TestWebSocketClientSelectProfile`. All 20 pass. Coverage includes: name resolution, both id/name rejection paths, pre-validate abort (load returns None), pre-validate WS failure, happy path, partial-success split-brain, divergence detection, all six error codes with five-field shape assertion, and unknown-action error message. The parametrized `test_select_error_shape_all_codes` exercises both the "raise from load_profile" path and the "raise from select_profile" path for `api_error`. Edge case for `invalid_input` correctly uses bad-input triggering rather than mocking, which is more robust.

- **Pattern consistency**: `select_profile` in `websocket.py` is a direct structural copy of `delete_profile` (same request/response pattern, same logging calls, same return). The server-side `select` branch follows the existing `elif action == "..."` dispatch pattern. The `_select_error` inner helper avoids repetition across the multiple error return sites in the select branch. One minor note: `from gaggimate_mcp.errors import ErrorCode` is imported inside the `elif action == "select":` block (line 450) rather than at the module level. This is a late import — the module already imports `GaggimateError` at the top but not `ErrorCode`. The late import is functional and avoids a small refactor to the top-level imports; it's not a bug, but a future cleanup candidate if `ErrorCode` gets other callers.

---

## Verdict

```json
{"verdict": "APPROVED", "cycle": 1, "issues": [], "requirements_drift": "none"}
```
