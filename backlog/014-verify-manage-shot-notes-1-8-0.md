---
id: "014"
title: "Align manage_shot_notes with 1.8.0 native sidecar schema"
status: open
priority: critical
type: feature
parent: "013"
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-18
---

# Align manage_shot_notes with 1.8.0 native sidecar schema

## What this delivers

`manage_shot_notes` on firmware 1.8.0 is **verified to round-trip with the native Note Editor** and extended to carry the 1.8.0 schema (`dose_in_g`, `dose_out_g`, `grind_setting`, `bean_type`) alongside our existing `rating`, `notes`, `balance_taste`. Single ticket because verification and implementation share the same file (`mcp/src/gaggimate_mcp/server.py`) and split earlier as 014 + 019 which duplicate effort.

## Why this is critical priority

`/feedback` is invoked after **every rated shot**. If 1.8.0 shifted `req:shot:notes:set` persistence (likely, since 1.8.0 introduced a sidecar `.json` per shot), our notes silently divert from what the user sees in the native editor. Grind-map entries would diverge from the user's visible tasting history and they won't notice until a shot's notes are missing. This is silent corruption for the most-used skill in the system — `critical` tier is warranted.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Decision Record DR-2 (revised). Earlier decomposition split this into 014 (verification) + 019 (alignment); consolidated per decompose skill §3 (same-file S-sized items merge).

## Native schema to align with

Per 1.8.0 sidecar JSON structure: `rating`, `beanType`, `grindSetting`, `doseIn`, `doseOut`, `ratio` (derived, not stored).

## Acceptance criteria

### Phase 1: Verify current behavior (first AC)

- Pick any recent shot on the device. Write a rating + notes + `balance_taste` via MCP `manage_shot_notes`.
- Open that shot in the native web analyzer's Note Editor. Record which fields are visible:
  - Is `rating` displayed?
  - Is the notes text displayed?
  - Is `balance_taste` displayed?
- Edit a different shot's notes in the native editor — include `beanType`, `grindSetting`, `doseIn`, `doseOut`. Save.
- Call MCP `manage_shot_notes` (via `list_recent_shots` or equivalent read path) on that shot.
- Record in `research/gaggimate-1-8-0-upgrade/verification-notes.md` using this format:
  ```markdown
  ## 2026-MM-DD — manage_shot_notes verification on 1.8.0
  **WS → Native read-back**:
    - rating: visible / not visible
    - notes: visible / not visible
    - balance_taste: visible / not visible
  **Native → WS read-back**:
    - beanType: round-tripped / lost
    - grindSetting: round-tripped / lost
    - doseIn: round-tripped / lost
    - doseOut: round-tripped / lost
  **Persistence authority**: WebSocket endpoint / sidecar .json / split / no-op
  **Conclusion**: [one sentence on which persistence path is authoritative]
  ```

### Phase 2: Extend `manage_shot_notes`

Based on Phase 1's conclusion:

- Add optional parameters to `manage_shot_notes`: `dose_in_g`, `dose_out_g`, `grind_setting`, `bean_type`.
- Document the name mapping (Python → JS) in the tool's docstring in `mcp/src/gaggimate_mcp/server.py`. No external mapping doc needed.
- Writing via MCP → reading in native Note Editor shows all new fields with correct values.
- Editing in native Note Editor → reading via MCP returns all new fields with correct values.
- `balance_taste` is preserved additively — never clobbered by native edits that don't carry it. Verified by a round-trip test: WS-write `balance_taste=bitter`, native-edit a different field, WS-read, confirm `balance_taste=bitter` intact.
- `ratio` is always computed on read (not stored) to match native behavior.
- `/feedback` skill updated to pass the new fields when the user provides them.

## Size note

S if Phase 1 reveals the WebSocket endpoint is still authoritative (just extend the existing message). M if Phase 1 reveals the sidecar `.json` is now authoritative (requires MCP to write the sidecar directly — new persistence path).

## Supersedes

- Old ticket 019 (extend manage_shot_notes with native note fields) — merged here.
