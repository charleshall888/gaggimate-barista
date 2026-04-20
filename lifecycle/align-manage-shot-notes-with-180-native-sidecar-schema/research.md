# Research: Align `manage_shot_notes` with 1.8.0 native sidecar schema

## Epic Reference

Background: [`research/gaggimate-1-8-0-upgrade/research.md`](../../research/gaggimate-1-8-0-upgrade/research.md) (DR-2, revised). Epic covers the full 1.8.0 audit; this ticket addresses the single P0 verification + alignment concern that blocks `/feedback` correctness.

Verification log: [`research/gaggimate-1-8-0-upgrade/verification-notes.md`](../../research/gaggimate-1-8-0-upgrade/verification-notes.md) — findings from live + source-code verification done during this research phase.

---

## Codebase Analysis

### Files that will change

| File | Change |
|------|--------|
| `mcp/src/gaggimate_mcp/server.py` | `manage_shot_notes` — add `bean_type` param; pass to `ws_client.save_shot_notes` and `ShotRating` ctor |
| `mcp/src/gaggimate_mcp/api/websocket.py` | `save_shot_notes` — add `bean_type` param; implement read-modify-write: call `get_shot_notes` before build-and-send, merge, always include `id` + compute `ratio` when both doses present |
| `~/.claude/skills/feedback/SKILL.md` | `/feedback` — pass `bean_type` when the user provides it (and when active-coffee context is available, auto-populate from `user-setup.md`) |

### Relevant existing patterns (file:line)

- `mcp/src/gaggimate_mcp/server.py:514` — `manage_shot_notes` tool entry. Already supports `action="get"` (line 558) and a "local backup always saved" invariant (line 619-630).
- `mcp/src/gaggimate_mcp/server.py:583-590` — AI-prefix logic: prepends `config.ai_notes_prefix` to notes if not already present. Only the prefixed version is synced to device.
- `mcp/src/gaggimate_mcp/api/websocket.py:316-345` — `get_shot_notes` → sends `req:history:notes:get`, returns `response["notes"]` dict (or None if empty). This is the read half of RMW.
- `mcp/src/gaggimate_mcp/api/websocket.py:347-402` — `save_shot_notes` → sends `req:history:notes:save`. **Currently builds `notes_data` from only non-None fields** (lines 380-392). This is the bug: partial builds become destructive writes under firmware's replace semantics.
- `mcp/src/gaggimate_mcp/models/rating.py:16-64` — `ShotRating` Pydantic model. Already has `bean_type` (line 48) and auto-computes `ratio` in `calculate_ratio` validator (line 59-64). Ratio formula: `round(dose_out / dose_in, 3)`.
- `mcp/src/gaggimate_mcp/storage/ratings.py:70-80` — local backup payload already includes `bean_type` (line 78). File: `{storage_path}/ratings.json`, keyed by `shot_id` (6-digit-padded). Every save is a full-object write (line 82), so the local backup is effectively already RMW-correct.

### Integration points and dependencies

- `/feedback` skill calls `manage_shot_notes` via the MCP tool interface. Currently passes `rating`, `notes`, `balance_taste`, `grind_setting`, `dose_in`, `dose_out`. Needs `bean_type` added.
- `user-setup.md` → Active Coffee section identifies the current bean. `/feedback` can derive `bean_type` from there automatically.
- `RatingStorage` (local backup) is a second source of truth. With RMW wired through MCP, the local backup and the device should converge on every save — but they can still diverge across native edits (native saves bypass MCP and don't touch local storage). This is fine: the device is stated to be the source of truth (`server.py:527`); local backup is a fallback for offline writes.

### Conventions to follow

- **Repo first, device second**: does not apply to shot notes. Shot notes are device-first; `CLAUDE.md` states "The device is the source of truth for all shot notes." The repo-first rule applies to profiles only.
- **Partial updates**: `manage_profile` supports them (per `CLAUDE.md`). `manage_shot_notes` also accepts only the fields you want to change. The shift with 1.8.0 sidecar: "accepts only the fields you want to change at the tool boundary" is fine; "writes only those fields to the device" is not. The tool-boundary behavior stays; the transport layer must be upgraded to RMW.
- **AI prefix**: notes get `[Updated by AI]: ` prepended via `config.ai_notes_prefix`. Already implemented; no change.

### Read-back path availability

`get_shot_notes` returns the full sidecar JSON as a dict. This is sufficient for RMW: read → spread → overwrite keys → write.

### `balance_taste` handling

- Set: in `manage_shot_notes` (tool layer) → `save_shot_notes` (WS layer) → `balanceTaste` key in sidecar JSON.
- Read: by the native editor's `NotesBar`/`ShotNotesCard` (per firmware research) — yes, the native UI exposes `balance_taste` via its own UI control mapped to `balanceTaste`.
- Agent-specific?: No. The native UI supports the same field with the same enum values. Our agent's role in `balance_taste` is choosing/collecting the value, not owning the schema.

### Test infrastructure maturity

No MCP tests exist today. `mcp/tests/` is absent. Backlog ticket **016** (shot-fixture regression harness) is the canonical ticket for adding fixtures — it blocks 015, 018, 021. For 014 specifically, a minimal inline pytest against `save_shot_notes`'s RMW merge logic (no device needed; mock `get_shot_notes` + `_send_request`) is a reasonable addition without waiting for 016.

---

## Web Research

Source: [upstream Gaggimate repo at v1.8.0](https://github.com/jniebuhr/gaggimate/tree/v1.8.0).

### WebSocket save handler: `req:history:notes:save`

- Dispatch in the WS handler; `saveNotes()` implementation at [`ShotHistoryPlugin.cpp:483-491`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/src/display/plugins/ShotHistoryPlugin.cpp#L483-L491).
- Opens `/h/{id}.json` in `FILE_WRITE` (truncate), `serializeJson` of the incoming `request["notes"]` object, closes. The `id` is the client-supplied string concatenated directly — no padding performed by firmware.
- **Replace, not merge.** Whatever the client sends is what ends up on disk.
- Also calls `updateIndexMetadata(id, rating, volume)` at `:461-473` — reads `notes["rating"]` unconditionally and `notes["doseOut"]` **only if `.is<String>()`** (line 465). Sending `doseOut` as a JSON number silently zeros the `/h/index.bin` volume column.

### WebSocket get handler: `req:history:notes:get`

- `loadNotes()` at [`ShotHistoryPlugin.cpp:493-500`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/src/display/plugins/ShotHistoryPlugin.cpp#L493-L500).
- Reads `/h/{id}.json` with `readString()` + `deserializeJson`; returns dict as `response["notes"]`. Empty/no-file returns empty JsonDocument — either `{}` or `null` in the JSON payload depending on ArduinoJson version; handle both.

### Sidecar schema

File path: `/h/{id}.json` — the firmware concatenates the client-supplied `id` directly (`ShotHistoryPlugin.cpp:456, 483`). Both MCP and the native UI use the unpadded integer form (e.g. `/h/246.json` for shot 246).

From [`schema/shot_notes.json`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/schema/shot_notes.json):

| Field | Type | Constraint |
|---|---|---|
| `id` | string | required, 6-digit padded |
| `rating` | number | 0-5 |
| `beanType` | string | free-form |
| `doseIn` | number | ≥ 0 |
| `doseOut` | number | ≥ 0 |
| `ratio` | number | ≥ 0 (client-computed) |
| `grindSetting` | string | free-form |
| `balanceTaste` | string | enum: `bitter` / `balanced` / `sour` |
| `notes` | string | maxLength 200 |
| `timestamp` | integer | declared but not populated by anyone |

`additionalProperties: false` — strict schema, though firmware does not enforce.

### Native editors

Two coexist in 1.8.0 ([PR #602](https://github.com/jniebuhr/gaggimate/pull/602) added the second):
- [`web/src/pages/ShotHistory/ShotNotesCard.jsx`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/web/src/pages/ShotHistory/ShotNotesCard.jsx) — classic card in ShotHistory list.
- [`web/src/pages/ShotAnalyzer/components/NotesBar.jsx`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/web/src/pages/ShotAnalyzer/components/NotesBar.jsx) + `NotesBarExpanded.jsx` — new in 1.8.0, inline in Shot Analyzer.

Both edit the same 8 fields: `rating`, `beanType`, `doseIn`, `doseOut`, `ratio` (read-only auto-calc), `grindSetting`, `balanceTaste`, `notes`. Both load full existing object before edit, both send full object on save.

### `ratio` computation

`(parseFloat(doseOut) / parseFloat(doseIn)).toFixed(2)` → string. Recomputed on every render; always fresh after any native save. Our Pydantic model uses `round(dose_out / dose_in, 3)` → float — minor precision difference, no correctness impact.

### 1.7.3 ↔ 1.8.0 parity

The notes persistence stack (handlers, sidecar file, schema) is **identical between 1.7.3 and 1.8.0**. Verified by direct fetch of the 1.7.3 tag. 1.8.0's changes in this area are UI-only (`NotesBar` added; auto-populate from profile-name parsing; auto-save-on-profile-change).

### Documentation

- [`docs/shot-notes-api.md`](https://github.com/jniebuhr/gaggimate/blob/v1.8.0/docs/shot-notes-api.md) — WebSocket API doc.
- [v1.8.0 release notes](https://github.com/jniebuhr/gaggimate/releases/tag/v1.8.0).

---

## Requirements & Constraints

No `requirements/` directory exists; constraints sourced from `CLAUDE.md`, epic research, and project conventions.

### Applicable constraints

- **Device is source of truth for shot notes** (from `server.py` docstring line 527 and `CLAUDE.md` implicit, since shot data lives on device). Local `RatingStorage` is a best-effort backup for offline/device-error conditions.
- **Every rated shot passes through `/feedback`** (CLAUDE.md §4). Any regression in `manage_shot_notes` is a high-blast-radius defect.
- **`balance_taste` is critical to grind-map and tasting-notes loop** (CLAUDE.md §4 and `/feedback` skill). Losing it silently is the "silent corruption" concern that motivates this ticket's CRITICAL tier.
- **No multi-user concerns**: the project is single-user (one machine, one agent). No concurrent-write scenarios beyond user-in-UI + agent-in-MCP, which is rare but possible and handled by RMW + last-writer-wins.
- **No backwards-compat concerns**: 1.8.0 is the minimum firmware target (the user's machine). The sidecar stack is identical on 1.7.3 anyway.

### Scope boundaries

- **In**: `manage_shot_notes` signature + `save_shot_notes` transport + `/feedback` skill call site.
- **Out**: deep-link to native analyzer (→ 018); surfacing `weight_flow_g_s` (→ 015); fixture harness (→ 016); docs pass (→ 017).

### Sequencing

- **This ticket** (014) — blocking nothing else in the epic but blocks claiming `/feedback` is safe on 1.8.0.
- **016** (fixture harness) — unrelated to this ticket; helpful for testing RMW merge logic but not a prerequisite (MCP-side unit test can stand alone with mocks).

### Test coverage expectation

Inline pytest for the RMW merge logic: mock `get_shot_notes` + `_send_request`, assert the `notes_data` built by `save_shot_notes` is the full merged object (not the partial input). No need to wait for 016 since this test needs no fixtures.

---

## Tradeoffs & Alternatives

The firmware research collapsed the WS-vs-sidecar dichotomy — they're the same persistence. So the alternatives reduce to:

### (A) Extend WS payload only (status quo + `bean_type`), keep partial-field send

- Pros: smallest diff.
- Cons: **still broken.** `balance_taste` still silently clobbered when `/feedback` runs after a native edit. The ticket's own AC ("`balance_taste` preserved additively — never clobbered") is not met. This is not actually an option.

### (B) Read-modify-write (recommended)

- On every `save_shot_notes`: call `get_shot_notes(id)` → build merged dict by spreading existing over new fields → send full payload including `id`.
- Pros: correct under firmware's replace semantics; preserves all fields including any unknowns (future-firmware-compatibility); matches what both native editors already do.
- Cons: one extra WS round-trip per save (minor); minor race window between read and write where a concurrent native save would be lost-updated. The race window is acceptable for single-user single-machine.

### (C) RMW + field-level conflict detection

- RMW plus compare-and-swap: track `timestamp` or content hash; abort save if the sidecar changed between read and write.
- Pros: rigorous.
- Cons: (1) firmware doesn't populate `timestamp`; (2) the single-user scenario has no real concurrent-write threat; (3) the failure mode of a simple RMW — losing a simultaneous native edit — is both rare and self-correcting on the next native save. CAS is overkill.

### (D) Agent-local `balance_taste` (don't write it to device)

- Keep `balance_taste` in `RatingStorage` only; write only native-schema fields to the device.
- Pros: decouples agent from firmware schema; no risk of device-side clobbering of our agent-specific field.
- Cons: breaks the round-trip narrative (`balance_taste` would be invisible in the native editor); the native editor already has a `balanceTaste` field with matching enum values, so coupling is fine; data lives in two places instead of one.

### (E) Always-send-all-fields (no read)

- Always include every schema field, filling in nulls for unset ones.
- Pros: no extra read round-trip.
- Cons: we don't *know* existing values without reading — we'd clobber anything set by the native editor that wasn't also in our current call. Strictly worse than B.

### Recommended approach: **(B) Read-modify-write**

Rationale:
1. Firmware's replace semantics means any write that isn't a full object is a clobber. There is no correct partial-write strategy.
2. Native editors already do RMW at the UI layer; MCP matching that pattern is consistent.
3. Single-user concurrency makes a plain RMW sufficient — no CAS needed.
4. Local `RatingStorage` already effectively RMWs (always writes full object); bringing the WS transport to the same invariant collapses two different behaviors into one.

---

## Adversarial Review

Looking for ways the recommended RMW approach can still fail:

1. **Empty-sidecar read**: `get_shot_notes` returns `None` when the file doesn't exist. Merge logic must treat `None` as "empty dict", not explode. Trivial but easy to miss in tests.

2. **`id` field contamination**: if a future firmware version ever enforces `additionalProperties: false`, our MCP-written sidecars must NOT contain extra fields. Current risk: we might be tempted to add `timestamp` or a custom `source: "mcp"` marker. Don't. Stick to the schema.

3. **Stale-read race** (single-user, rare but possible): user opens native editor, edits `beanType` → /feedback runs RMW and reads sidecar before user hits save → MCP writes merged object without user's new `beanType` → user hits save → native UI overwrites with its version. Net effect: one of the two writes wins, no silent corruption. Acceptable.

4. **`[Updated by AI]:` prefix loop**: MCP writes `notes="[Updated by AI]: foo"`. User edits in native → sees the prefix → may strip it. On next MCP write, prefix is re-added. User perceives it as ever-growing annotation noise. Mitigation: MCP should not double-prefix; current code already handles this (line 587: `if not notes.startswith(agent_prefix)`). But if the user strips it and replaces with fresh notes, we'll re-prefix on next call, which is fine. Document in `/feedback` skill: prefix is informational, not identity.

5. **Ratio drift**: MCP sends `round(x, 3)` = `2.023`; native editor sends `x.toFixed(2)` = `"2.02"`. Alternating saves will cause `ratio` to flip-flop between the two precisions. Harmless — `ratio` is derived and displayed at 2 decimals in the UI anyway. Accept.

6. **`balanceTaste` enum mismatch**: if we ever loosen the `BalanceTaste` enum or the firmware adds new values in a future release, writes could be rejected by a future schema validator. Current code is aligned; leave as-is.

7. **Local backup divergence**: `RatingStorage` saves a copy with its own `timestamp`. If device write fails (network error), local still saves. Later, device reconnects, `/feedback` doesn't auto-sync the backlog. Acceptable: the user can re-run the rating if they care, and the device-synced bool in the response tells them what happened.

8. **Schema drift on future firmware**: if a later firmware adds new fields to the sidecar that neither the native editor nor MCP knows about, RMW will preserve them (we spread existing → overwrite our known keys), which is the right behavior. ✓

9. **Tool signature expansion breaking callers**: adding `bean_type` as an optional param is additive; no existing callers break. ✓

10. **`/feedback` skill coupling**: we need to also update `/feedback` to pass `bean_type`. If we don't, the MCP-side fix is inert for the most common code path. Spec must include the skill update or flag it explicitly.

---

## Open Questions

All five Clarify-phase open questions resolved during research:

1. ~~Does `req:shot:notes:set` persist somewhere the native Note Editor reads?~~ **Resolved**: yes — same sidecar file. WS endpoint name is `req:history:notes:save` (not `:set`, minor rename from epic research). Confirmed empirically and by source.
2. ~~Where does the sidecar live on the device?~~ **Resolved**: `/h/{paddedId}.json`.
3. ~~Does the native editor clobber or merge?~~ **Resolved**: it re-sends the full object, so it preserves fields already in the file — not a conscious merge. Firmware does replace-write.
4. ~~Read path for sidecar content?~~ **Resolved**: `req:history:notes:get`. Already wired through MCP's `get_shot_notes`.
5. ~~`ratio`: stored or computed?~~ **Resolved**: computed client-side by native UIs; firmware passes through. MCP can compute and send (via `ShotRating.calculate_ratio`) or omit (next native save recomputes).

No open questions remain.
