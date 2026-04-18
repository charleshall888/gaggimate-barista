---
id: "014"
title: "Round-trip verify manage_shot_notes on 1.8.0"
status: open
priority: high
type: chore
parent: "013"
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-18
---

# Round-trip verify manage_shot_notes on 1.8.0

## What this delivers

Empirical confirmation that `/feedback` still writes shot notes to a location the user (and native Note Editor) can read back, and vice-versa.

## Why this is front-line, not a decomp chore

Firmware 1.8.0 introduces a sidecar `.json` file next to each `.slog` containing `rating`, `beanType`, `grindSetting`, `doseIn`, `doseOut`, `ratio`. It is **unknown** whether our existing `req:shot:notes:set` WebSocket message:

- still writes to a location the native Note Editor reads, OR
- now writes to the sidecar (potentially with the wrong field set), OR
- has become a no-op that silently drops our notes.

`/feedback` is invoked after every rated shot. If this is broken, grind-map.md entries and tasting notes silently diverge from what the user sees in the native editor — and the user won't notice until a shot's notes are missing.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Decision Record DR-2, Open Question #1. This ticket is DR-2 #1 (the verification half of the split).

## Acceptance criteria

- Write a rating + notes + balance_taste via MCP `manage_shot_notes` on a real shot
- Open that shot in the native web analyzer's Note Editor — verify all written fields are visible
- Edit a different shot's notes in the native editor, including `beanType`, `grindSetting`, `doseIn`, `doseOut`
- Call MCP `manage_shot_notes` action=get (or equivalent read path) on that shot — record which fields survive the round trip and which do not
- Document the result in research/gaggimate-1-8-0-upgrade/verification-notes.md
- Surface findings to 019 which depends on this

## Blocks

- 019 (manage_shot_notes field alignment) — implementation path depends on which persistence path is authoritative
