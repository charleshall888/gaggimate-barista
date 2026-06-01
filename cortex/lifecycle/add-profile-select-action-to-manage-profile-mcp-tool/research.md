# Research: Add `select` action to `manage_profile` MCP tool

**Lifecycle slug**: `add-profile-select-action-to-manage-profile-mcp-tool`
**Backlog**: `backlog/023-add-profile-select-action-to-manage-profile-mcp-tool.md`
**Tier / Criticality**: complex / medium

## Headline

The ticket frames profile-selection mechanism as unknown and prescribes browser-devtools discovery. Research short-circuits that: the GaggiMate firmware is open-source at [`jniebuhr/gaggimate`](https://github.com/jniebuhr/gaggimate), the protocol is documented in an AsyncAPI spec, and a reference MCP implementation ([`julianleopold/gaggimate-mcp`](https://github.com/julianleopold/gaggimate-mcp)) already wraps it.

**Confirmed mechanism**: WebSocket `req:profiles:select` with payload `{tp, rid, id}`. Firmware calls `ProfileManager::selectProfile(uuid)` which invokes `_settings.setSelectedProfile(uuid)` — a **single-value setter**. No paired un-selection required; firmware enforces single-select.

The other two hypotheses are rejected:
- **HTTP `POST /api/profiles/{id}/select`** — not in the AsyncAPI spec. Device's HTTP surface is history/data only (`/api/history/*`); profiles are WebSocket-only.
- **`req:profiles:save` with `selected: true`** — the `selected` flag on save payloads does not drive activation; `setSelectedProfile(uuid)` does, reached only via `req:profiles:select`. (Current MCP `create_or_update_profile` already always writes `"selected": false` on save, which confirms save ≠ activation in this codebase too.)

## Codebase Analysis

### Files that will change

| Path | Nature of change |
|---|---|
| `mcp/src/gaggimate_mcp/api/websocket.py` | Add `select_profile(profile_id: str) -> dict` method next to `save_profile` / `delete_profile`. Add `req:profiles:select` to module docstring list. |
| `mcp/src/gaggimate_mcp/server.py` | Add `elif action == "select":` branch in `manage_profile` (around current line 440, between `delete` and `else`). Update error message on line 443 from `"Use: list, get, create, update, delete"` to include `select`. Update tool docstring. |
| `mcp/tests/test_manage_profile_select.py` (new) or extension of existing profile test | Fixture test for the new action — follow `test_api_websocket.py` + `test_models_profile.py` style (mock `_send_request`, assert request shape, assert returned JSON). |
| `mcp/README.md` (if action table exists there — confirm during implementation; the current `mcp/README.md` is about shot-analyzer maintenance and does not enumerate `manage_profile` actions) | Update any action enumeration to include `select`. |

No changes needed to `mcp/src/gaggimate_mcp/api/http.py`, the profile Pydantic model, the storage layer, or `user-setup.md`.

### Existing patterns to follow

**Action dispatch (`server.py`)** — if/elif chain:
```python
if action == "list": ...
elif action == "get": ...
elif action == "create": ...
elif action == "update": ...
elif action == "delete": ...
else: # error
```
Add `select` before `else`.

**WebSocket request (`websocket.py`)** — every profile op uses `_send_request`:
1. `request_id = generate_request_id()`
2. `_send_request("req:profiles:select", request_id, id=profile_id)` opens WS, sends `{tp, rid, id}`, waits for `res:profiles:select`, checks `error`, returns dict.

**Response shape** — all `manage_profile` actions return:
```json
{"success": true|false, "action": "<name>", "profile"|"profiles": ..., "error": ..., "error_code": ..., "suggestion": ...}
```

**Error handling** — `GaggimateError` caught at line 447-454, generic Exception at 455-460, both returned as JSON with `_get_error_suggestion()` populating the `suggestion` field.

### Integration points

- **`/new-coffee` skill** (`.claude/skills/new-coffee/SKILL.md`, around lines 107-114): currently calls `manage_profile(action="create", ...)` and stops. After `select` lands, the skill extends to `create` → capture returned `id` → `select`. The skill update is the acceptance criterion for the ticket but is a skill-layer change, not an MCP-tool change; it can be a same-PR follow-through task or a separate ticket.
- **Profile model** (`models/profile.py`, lines 116-170): already has `selected: bool = False` on line 145. No model change.
- **Storage layer** (`storage/profiles.py`): no change — selection is device-only state.
- **User-facing active-profile pointer in `user-setup.md`**: already tracked as human-readable prose under "Active Coffee". Out of scope for the MCP action; the `/new-coffee` skill may update it as part of its workflow but this ticket need not.

## Web Research

### Ground-truth sources (all from `jniebuhr/gaggimate` master)

| Source | URL | What it proves |
|---|---|---|
| AsyncAPI spec | `docs/websocket-api.yaml` | `ProfilesSelectRequest`: `tp: 'req:profiles:select'`, `id: string`, response `tp: 'res:profiles:select'` with optional `error` field |
| Firmware handler | `src/display/plugins/WebUIPlugin.cpp` | `else if (type == "req:profiles:select") { auto id = request["id"].as<String>(); profileManager->selectProfile(id); }` |
| Firmware implementation | `src/display/core/ProfileManager.cpp` | `ProfileManager::selectProfile` writes `_settings.setSelectedProfile(uuid)` — single-value setter |
| Web UI call-site | `web/src/pages/ProfileList/index.jsx` | `await apiService.request({ tp: 'req:profiles:select', id })` — the actual JS the tap-handler runs |

### Reference implementation

`julianleopold/gaggimate-mcp` already ships `manage_profile(action="select")`. Conventions worth adopting from that project:

- Accept **either** `profile_id` or `profile_name` — if name, resolve via `list_profiles` + label match, then call select.
- **Pre-validate** existence by calling `req:profiles:load` before `req:profiles:select`. Rationale: firmware's `selectProfile` does not guard against non-existent UUIDs — it calls `setSelectedProfile(uuid)` unconditionally, then `loadSelectedProfile` fails silently. Pre-validation produces a clean "not found" error instead of a silent device-side failure.
- Include `rid` on every request for response correlation (matches existing MCP pattern).

### Response body

`res:profiles:select` per the AsyncAPI spec carries **only** `{tp, rid, error}` — no profile payload. To verify the selection landed, the MCP must either re-`list` or re-`load` after the select call. This shapes the return-shape decision (E below).

### Unverified caveats

- **Behavior when selecting during an active shot**: not documented. Safe default: allow, document caveat. Live testing would clarify but isn't blocking for v1.
- **Firmware version floor**: handler is present on master. Stable tag v1.7.3 likely has it; project is on 1.8.0 per CLAUDE.md, well clear. No version gate needed.

## Requirements & Constraints

No `requirements/` directory exists. Constraints come from `CLAUDE.md`, the MCP's own code contract, and prior backlog/lifecycle conventions.

### CLAUDE.md rules that apply

- **"Repo first, device second"** (`CLAUDE.md`, under *MCP Tools Available*): "The JSON file in `coffees/{coffee}/` is the source of truth. Any profile create or update must: (1) write the JSON to the repo file, (2) then upload to device via MCP." This rule governs **create/update** (profile content). `select` is an ephemeral device-state mutation, not a content write — the rule does not apply and does not conflict. The spirit of the rule (repo authority over device) is preserved: the repo continues to own profile bytes; the device owns "which of your uploaded profiles is currently active."
- **Auto-commit policy** (same section): triggers after data-writing skill steps. `select` performs no repo writes, so the policy does not fire. If `/new-coffee` later mirrors the active-profile pointer into `user-setup.md`, that skill-step does trigger auto-commit — handled in the skill layer, not the MCP tool.

### MCP action-taxonomy conventions

- All existing actions return `{"success": bool, "action": "<name>", ...payload..., "error"?, "error_code"?, "suggestion"?}`. `select` must follow.
- One verb per action (`list`, `get`, `create`, `update`, `delete`). `select` is consistent — dedicated action rather than overloading `update`. Overloading `update` is actively unsafe because today's `create_or_update_profile` unconditionally writes `"selected": false`, so `update(selected=True)` would need a special-case branch that risks the LLM mis-calling `update` and rewriting phases.

### Out of scope for this ticket

- Mirroring active-profile state into `user-setup.md` or `coffees/{slug}/` (defer to follow-up).
- Changing the "Repo first, device second" architecture.
- Firmware-side UI changes.
- Updating `/new-coffee` to upload + select in one run — acceptance criterion but a skill-layer change; handle in a separate task or follow-through within this ticket's implement phase, not in the MCP surface itself.

## Tradeoffs & Alternatives

Research resolved most axes definitively (A, C, F); the remaining design decisions (B, E, and pre-validation) are spec-level calls.

| Axis | Options | Decision |
|---|---|---|
| **A — Transport** | WebSocket only vs. add HTTP vs. WS-first-with-HTTP-fallback | **WebSocket only.** Firmware exposes no HTTP profile endpoints. No transport split needed. |
| **B — Action granularity** | Dedicated `action="select"` vs. fold into `update(selected=True)` | **Dedicated action.** Overloading `update` collides with existing `create_or_update_profile` unconditionally writing `selected: false`. Named action matches one-verb-per-action pattern, and the LLM picks correctly by verb. |
| **C — Atomicity** | Firmware enforces single-select vs. MCP performs paired ops | **Firmware enforces.** `setSelectedProfile(uuid)` is a single-value setter — one call flips. No paired un-selection required. |
| **D — Repo-side pointer** | No mirror (v1) vs. `user-setup.md` mirror vs. per-coffee pairing | **No mirror in v1.** Device is authority via `list`. Revisit as follow-up ticket if agent UX shows a need. |
| **E — Return shape** | Return selected profile only (E1) vs. return full updated list (E2) vs. return `{selected, previous_id}` (E3) | **Likely E2 (full list)**, pending spec. Rationale: the firmware's `res:profiles:select` carries no profile payload, so the MCP must already re-fetch to produce a useful return. Since a `list` is the natural re-fetch (and matches the backlog verification criterion "`list` shows `selected: true` on that profile and `false` on others"), E2 gives callers the flipped state in one tool call without a follow-up. Defer final call to spec — E1 is defensible if payload size is a concern. |
| **F — Response wait semantics** | Wait for ack vs. send-and-forget vs. fire-and-check | **Wait for ack (match existing `_send_request` pattern).** All existing profile ops wait for correlated `res:*` with 5 s timeout. No reason to diverge. |
| **Pre-validation** | Resolve-first via `load` before `select` vs. call `select` directly | **Defer to spec.** Reference MCP pre-validates because firmware does not guard against missing UUIDs; trade-off is an extra round-trip. Lean yes (better error messages), but not blocking. |
| **Identifier input** | `profile_id` only vs. accept `profile_name` too | **Defer to spec.** Reference MCP accepts both. For this project, `/new-coffee`'s happy path already has the id from the create response, so `profile_id` alone covers acceptance. `profile_name` is a convenience add. |

### Failure-mode ranking (if C had required paired ops)

Kept here as documentation of what was considered and why it doesn't apply:

1. Worst — **no selection at all** (deselect old succeeds, select new fails) → user's next shot runs on fallback profile; silent surprise.
2. Medium — **both selected** (select new succeeds, deselect old fails) → cosmetic UI drift; new profile works; next list corrects.
3. Best — **firmware enforces single-select** (this case).

Applied recommendation had C2 ever been needed: perform new-first-old-second so worst case is cosmetic, not functional, and treat the deselect as best-effort with a logged warning.

## Open Questions

All research questions are resolved or explicitly scoped to the spec phase. No investigation-level gaps remain.

- **Pre-validation via `load` before `select`** — resolved to: *defer to spec*. Research-level evidence is complete (firmware doesn't validate; reference MCP does pre-validate); the tradeoff (extra round-trip vs. cleaner errors) is a spec design call, not a research gap.
- **Return shape E1 vs. E2** — resolved to: *defer to spec*. Research-level evidence is complete (firmware returns no profile body in `res:profiles:select`; `list` is cheap); the choice of whether the tool re-fetches via `list` or `load` is a spec design call.
- **Accept `profile_name` as well as `profile_id`** — resolved to: *defer to spec*. Reference MCP supports both; project's primary caller (`/new-coffee`) has the id from create response, so name-support is convenience.
- **Behavior when selecting during an active shot** — resolved to: *document caveat in spec; no guard in v1*. Firmware behavior is undocumented; live testing is the only way to characterize fully, and isn't blocking.
- **Follow-through on `/new-coffee` skill update** — resolved to: *in scope for this ticket's implement phase as a task, not for the MCP surface design*. Acceptance criterion "/new-coffee can upload + select a profile in one skill run" is a skill-layer change separate from the MCP tool addition.
