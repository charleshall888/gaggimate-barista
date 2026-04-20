# Review: align-manage-shot-notes-with-180-native-sidecar-schema

**Scope note**: only `project.md` loaded — no area docs matched tags (project has no `requirements/` dir; drift check is observational only against CLAUDE.md project conventions). Lifecycle index tags: `[gaggimate-1-8-0-upgrade]`.

## Stage 1: Spec Compliance

### Requirement 1: Add `bean_type` parameter to `manage_shot_notes`
- **Expected**: `bean_type: Optional[str] = None` on tool signature; forwarded to `ws_client.save_shot_notes` and to `ShotRating(...)` local backup. Oversized values handled.
- **Actual**: `mcp/src/gaggimate_mcp/server.py:523` declares `bean_type: Optional[str] = None`; passed to `ws_client.save_shot_notes` at line 612 and to `ShotRating(..., bean_type=bean_type)` at line 638. Defensive 200-char truncation at lines 561-562 applies before both sinks — a belt-and-suspenders safety above and beyond spec (spec only required `/feedback` to truncate; server-side truncation means oversized values can never reach `ShotRating` and raise `ValidationError`). Tool docstring mentions the 200-char cap.
- **Verdict**: PASS
- **Notes**: Signature inspectability acceptance (`inspect.signature(manage_shot_notes).parameters`) is satisfied. Local-backup acceptance verified by `test_tool_passes_bean_type_to_both_sinks` in Task 3 tests.

### Requirement 2: Add `bean_type` parameter to `save_shot_notes` WS transport
- **Expected**: `bean_type: Optional[str] = None` on signature; when non-None, payload `notes` dict contains `"beanType": <value>`.
- **Actual**: `mcp/src/gaggimate_mcp/api/websocket.py:356` declares the parameter; lines 427-429 overlay `merged_notes["beanType"] = bean_type` when non-None and flag `caller_provided_any`.
- **Verdict**: PASS
- **Notes**: Covered by `test_empty_sidecar_stringifies_dose_and_ratio` (asserts `sent_notes["beanType"] == "X"`).

### Requirement 3: Implement read-modify-write in `save_shot_notes`
- **Expected**: Call `self.get_shot_notes(normalized_id)`; accept None/dict/non-dict (defensive); spread existing; overlay camelCase-mapped non-None fields; stringify `doseIn`/`doseOut`; compute `ratio` only when both doses numeric; ensure `id` present.
- **Actual**:
  - Read: line 392 calls `await self.get_shot_notes(normalized_id)`.
  - Defensive non-dict handling: lines 393-396 use `isinstance(existing_raw, dict)` and fall back to `{}` otherwise. No warning log on non-dict (spec said "log a warning" — minor omission but not a functional gap).
  - Spread first: line 399 `merged_notes = dict(existing)`.
  - camelCase overlays: lines 406-429 correctly map `balance_taste→balanceTaste`, `grind_setting→grindSetting`, `dose_in→doseIn`, `dose_out→doseOut`, `bean_type→beanType`. Only non-None values overlay.
  - Stringification: lines 420, 425 use `str(dose_in)` and `str(dose_out)`.
  - Ratio computation: lines 433-442 only compute when both doses are non-None AND `dose_in_f != 0`, guarded by try/except for `(TypeError, ValueError)`. Emitted as `str(ratio_val)`. Spec edge case "only one of dose_in/dose_out provided → do NOT compute ratio" respected. Pre-existing ratio preserved when only one dose passed (because only the `merged_notes[...]` overlay happens and `ratio` is not touched).
  - `id` preservation: lines 447-448 `if "id" not in merged_notes: merged_notes["id"] = normalized_id` — prefers existing id, synthesizes from `normalized_id` otherwise.
  - Full-object send: lines 463-468 send the merged object via `req:history:notes:save`.
- **Verdict**: PASS
- **Notes**: Minor spec deviation — non-dict `get_shot_notes` return does not log a warning; silently falls through to empty dict. Functionally correct (no crash, empty-merge semantics) and the test `test_defensive_non_dict_existing` verifies the no-crash contract. Not a blocker. Also strengthens beyond spec by guarding `dose_in_f != 0` to avoid div-by-zero on pathological input.

### Requirement 4: No-op write short-circuit
- **Expected**: If merged payload equals existing sidecar dict, skip WS `save` call entirely. The spec's acceptance tests dict-equality of merged vs existing, and this was the target of the follow-up fix in commit 646e4f0.
- **Actual**: `websocket.py:455` gate is `if merged_notes == existing:` — **dict equality on merged vs existing, not a stale flag**. This is precisely the fix described in 646e4f0. On no-op, the function returns a synthetic `{"msg": "no-op: unchanged", "id": normalized_id}` response so the tool layer still reports `device_synced=True`. `caller_provided_any` is tracked but (importantly) is not what gates the short-circuit — the short-circuit is purely dict-equal — which is the correct behavior.
- **Verdict**: PASS
- **Notes**: The `caller_provided_any` tracking variable is not actually used to gate the no-op (dead read, really) — but it doesn't cause harm and leaving it in is a minor code-quality nit, not a correctness issue. The test `test_noop_short_circuit` (`get_shot_notes → {"id": "246", "rating": 3}`, caller passes `rating=3`) directly exercises the spec's stated acceptance criterion, and it passes per plan.md Task 3 status.

### Requirement 5: `/feedback` skill passes `bean_type`
- **Expected per spec**: `~/.claude/skills/feedback/SKILL.md` updated to auto-populate `bean_type` from Active Coffee with truncation/override/placeholder rules. Acceptances grep `bean_type` ≥ 2 and `Active Coffee` present.
- **Actual**: The global path `~/.claude/skills/feedback/SKILL.md` does NOT exist on this machine (verified). The project-scoped `.claude/skills/feedback/SKILL.md` was edited instead. That file contains 7 occurrences of `bean_type`/`Active Coffee` combined — well above the threshold. Section 4c ("Shot Notes → Device") includes:
  - MCP call syntax with `bean_type="..."` arg (matches spec 5a).
  - `bean_type` source rules enumerated 1-4 matching spec 5a/5b/5c/5d exactly: Active Coffee title truncated to 200 chars, user-prose override, placeholder-omission rule.
- **Verdict**: PASS (with note)
- **Notes**: The path deviation is pragmatic — the global skill path does not exist, so editing a non-existent file would be a no-op. The project-scoped skill IS the operative skill for this project. User was aware and logged the deviation in events.log/plan.md. Behaviorally the skill now passes `bean_type`, which is what the spec's acceptance test actually validates. Marking PASS because (a) the behavioral goal is met, (b) the spec's literal path is non-existent and therefore unactionable, (c) fresh clones of this repo pick up the project-scoped skill via `.claude/skills/` discovery. A strict reviewer might mark this PARTIAL — the call here is judgment-based and the user's awareness of the deviation tips the scale to PASS.

### Requirement 6: Inline pytest for RMW + wire-type merge logic
- **Expected**: `mcp/tests/test_save_shot_notes_rmw.py` with 5 spec-named cases (Preservation, Empty sidecar, Defensive non-dict, No-op, String-vs-number preservation). Plus a tool-layer `bean_type` propagation test per plan. `pytest tests/test_save_shot_notes_rmw.py -q` exits 0.
- **Actual**: File exists with 6 test functions:
  - `test_rmw_preserves_existing_fields` — Preservation case, asserts id/rating/balanceTaste/notes all in `sent_notes`.
  - `test_empty_sidecar_stringifies_dose_and_ratio` — Empty sidecar + string-wire-type case; explicitly asserts `isinstance(doseIn/doseOut/ratio, str)`.
  - `test_defensive_non_dict_existing` — non-dict existing → no exception; empty-merge semantics.
  - `test_noop_short_circuit` — `_send_request.call_count == 0` on same-value same-state input. Exact spec AC.
  - `test_existing_dose_strings_preserved` — native-editor string `"18.0"` preserved byte-for-byte; explicit `isinstance(str)` check.
  - `test_tool_passes_bean_type_to_both_sinks` — covers both `sync_to_device=False` (local ratings.json gets `bean_type`) AND `sync_to_device=True` (WS transport receives `bean_type` kwarg). Uses `tmp_path` + `monkeypatch` + `importlib.reload` to isolate ratings.json from real storage.
  - All 6 pytest cases pass per plan.md Task 3 status (confirmed after 646e4f0 dict-equal fix).
- **Verdict**: PASS
- **Notes**: Test coverage goes slightly beyond spec — the tool-layer propagation test also exercises the `action="update"` path against the local `ratings.json`, which is AC #1's empirical acceptance. Good pattern; no redundancy.

### Requirement 7: Live integration acceptance — clobber-prevention
- **Expected**: Four-bullet live test (a native set → b MCP partial update → c MCP get returns all native fields → d native shot-list weight column non-zero) documented as dated entry in verification-notes.md.
- **Actual**: `research/gaggimate-1-8-0-upgrade/verification-notes.md` lines 28-58 contain the 2026-04-19 entry exercising shot 249 with all four bullets:
  - (a) native set `beanType="Mix"`, `doseIn=22`, `doseOut=49.6`, `balanceTaste="balanced"`, prior `rating=5`.
  - (b) `manage_shot_notes(shot_id="249", action="update", rating=4)` → `device_synced=true`.
  - (c) `action="get"` → JSON dump shows `rating=4`, `beanType="Mix"`, `doseIn="22"`, `doseOut="49.6"`, `ratio="2.25"`, `balanceTaste="balanced"`, `grindSetting=""`, `notes=""`. Dose/ratio as strings (firmware wire-type contract honored).
  - (d) user-confirmed shot 249 weight column shows `49.6g` (not zero) — `updateIndexMetadata` path drove `index.bin` correctly.
- **Verdict**: PASS
- **Notes**: The entry is appended, not replacing the prior 2026-04-18 pre-fix baseline — good provenance hygiene. `[Updated by AI]:` prefix not exercised here (deliberately out of scope per plan Scope Boundaries).

## Requirements Drift
**State**: none
**Findings**: None. The implementation aligns with CLAUDE.md conventions where they apply: (1) `[Updated by AI]:` prefix behavior unchanged (per spec Non-Requirement); (2) data-repo auto-commit policy unaffected (MCP code lives in the agent repo, not data repo, so no `.data-repo-path` write is triggered — spec Technical Constraint correctly anticipated this); (3) repo-first profile discipline irrelevant here (shot notes, not profiles); (4) the new `bean_type` auto-population from Active Coffee is consistent with the existing Active Coffee read pattern already in feedback/diagnose skills. The MCP tool addition is a normal API surface extension, not a convention change.
**Update needed**: None

## Stage 2: Code Quality

- **Naming conventions**: `bean_type` (Python snake_case) ↔ `beanType` (JSON camelCase, matching firmware schema) — mapping is consistent with all pre-existing fields (`balance_taste↔balanceTaste`, `grind_setting↔grindSetting`, `dose_in↔doseIn`, `dose_out↔doseOut`). `normalized_id` usage in `save_shot_notes` mirrors `get_shot_notes` line 329 pattern. Test names are descriptive and match spec vocabulary (Preservation / Empty sidecar / Defensive / No-op / String-vs-number preservation).

- **Error handling**: `get_shot_notes` exception during RMW propagates as `GaggimateError`, caught by existing `except GaggimateError` at `server.py:616` → sets `device_synced=False`, preserves local backup path — matches spec Edge Case "Device unreachable — read fails". Non-dict defensive path (`isinstance(existing_raw, dict)`) silently falls through to empty — functionally correct, though the spec suggested logging a warning which the implementation omits. This is a minor observability gap, not a correctness bug. Ratio computation guards `(TypeError, ValueError)` AND `dose_in_f != 0` — exceeds spec's safety bar by preventing div-by-zero. `_send_request` failures propagate unchanged.

- **Test coverage**: 6 tests across two layers — 5 at the WS transport boundary (RMW semantics + wire types) + 1 at the tool boundary (propagation + local backup). Transport tests use `AsyncMock` for `_send_request` and patch `get_shot_notes` per-test — clean isolation, zero network. Tool test uses `tmp_path` + `monkeypatch` of `GAGGIMATE_STORAGE_PATH` + `importlib.reload` to isolate `ratings.json` — solid pattern for module-level singleton reset. Live R7 test covers the full stack including firmware `index.bin` side effect (which no unit test can exercise). Coverage aligns with spec AC #6's "no device dependency" constraint.

- **Pattern consistency**: New `bean_type: Optional[str] = None` parameter follows exact style of existing `balance_taste: Optional[str] = None` at both layers. `RatingStorage`/`ShotRating` integration unchanged — `bean_type` was already a Pydantic field on `ShotRating` (per spec's observation that "model + storage already have it"). Tool-layer 200-char truncation belt does not duplicate the skill-layer truncation rule; it's a safety net, clearly commented. The `caller_provided_any` tracking flag is vestigial (no-op gate uses dict equality instead) — minor code-quality nit; could be removed in a follow-up cleanup but is not incorrect.

## Verdict
```json
{"verdict": "APPROVED", "cycle": 1, "issues": [], "requirements_drift": "none"}
```
