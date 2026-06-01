---
id: "019"
title: "Extend manage_shot_notes with native note fields"
status: superseded
priority: medium
type: feature
parent: "013"
blocked-by: ["014"]
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-18
superseded-by: "014"
---

> **Superseded** by ticket 014 during critical review of the decomposition. Verification (old 014) and alignment (this 019) were merged because they modify the same file and split per decompose skill §3 same-file rule. Archive-only; do not work this ticket.

# Extend manage_shot_notes with native note fields

## What this delivers

`manage_shot_notes` accepts and round-trips the full 1.8.0 native note schema (`dose_in_g`, `dose_out_g`, `grind_setting`, `bean_type`) alongside our existing `rating`, `notes`, `balance_taste` — so edits made in the native Note Editor and edits made via the agent stay in sync.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Decision Record DR-2 (revised), issue #2. User chose to pursue field alignment in addition to verification. Implementation path depends on what ticket 014 reveals about persistence authority (WebSocket `req:shot:notes:set` vs sidecar `.json`).

## Native schema to align with

From the 1.8.0 Note Editor sidecar JSON: `rating`, `beanType`, `grindSetting`, `doseIn`, `doseOut`, `ratio` (derived).

## Acceptance criteria

- `manage_shot_notes` accepts optional parameters: `dose_in_g`, `dose_out_g`, `grind_setting`, `bean_type`
- Our Python names map to native JS names consistently (document the mapping)
- Writing via MCP → reading in native Note Editor shows all fields correctly
- Editing in native Note Editor → reading via MCP returns all fields correctly
- If the native schema omits `balance_taste`, our agent-specific field is preserved without clobbering native fields (additive, not replacing)
- `/feedback` skill updated to pass these fields when the user provides them
- `ratio` is always computed (not stored) to match native behavior

## Dependencies

- 014 (round-trip verification) must complete first — determines whether to extend the WebSocket message or write the sidecar directly

## Risk notes

- Implementation path is unknown until 014 reports
- S if we extend the existing WebSocket message, M if we have to write the sidecar directly (involves a different persistence layer)
