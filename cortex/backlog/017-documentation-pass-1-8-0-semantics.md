---
id: "017"
title: "Document evt:status.bt semantic flip and retention shift"
status: complete
priority: medium
type: chore
parent: "013"
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-19
session_id: null
lifecycle_phase: complete
lifecycle_slug: document-evtstatusbt-semantic-flip-and-retention-shift
complexity: simple
criticality: medium
spec: lifecycle/document-evtstatusbt-semantic-flip-and-retention-shift/spec.md
areas: [docs]
---

# Document evt:status.bt semantic flip and retention shift

## What this delivers

The two **cross-cutting** firmware 1.8.0 semantic changes that don't belong in any single feature ticket are documented in the right places so future contributors don't trip on them.

## Scope (narrowed from earlier draft)

Earlier iterations of this ticket bundled seven doc topics. Critical review found that five of them (`vf` surfacing, DDSA availability, `rssi` fields, native analyzer UI mention, mixed-era compatibility note) belong inside their code-producing tickets (015, 018, and the implementation of 021 respectively) so the code and its docs ship together. What remains here is the two items that aren't tied to a code change:

- **`evt:status.bt` semantic flip** — pitfall alert: in 1.8.0 this field reflects `profile.isVolumetric()` (is the selected profile's final-phase target volumetric?) rather than `settings.isVolumetricTarget()` (is the user's BT-volumetric setting on?). Any future `diagnose_connection` extension reading this field must account for the flip.
- **Shot history retention shift**: `MAX_HISTORY_ENTRIES = 100` removed, replaced by `MIN_FREE_SPACE_BYTES = 500 KB` floor. Capacity purge also removes the companion `.json` sidecar alongside the `.slog`. Implication: grind-map.md references to old shot_ids may orphan silently.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md. Ticket narrowed from "full 1.8.0 doc pass" to "cross-cutting semantic traps only" during critical review — the `vf`/DDSA/`rssi` docs belong in their producing tickets.

## Acceptance criteria

- `CLAUDE.md` has a new subsection in the "Important Notes" section (or equivalent existing-patterns location) titled "Firmware 1.8.0 semantic traps" containing exactly these two bullets, with the `evt:status.bt` flip explained in one sentence and the retention shift explained in one sentence.
- `mcp/src/gaggimate_mcp/server.py` — the `diagnose_connection` tool docstring includes a one-line WARNING about the `evt:status.bt` semantic flip. (Not because diagnose_connection reads it today, but because it's the obvious future surface that would; inline warning prevents the trap.)
- `mcp/src/gaggimate_mcp/parsers/shot.py` — a top-of-file comment notes the retention policy shift so future maintainers understand why older shot_ids may not exist.
- MEMORY.md — no update required (the source-of-truth table already covers firmware semantics by pointing at CLAUDE.md).
- `/consult` skill — no update required; the `consult` skill routes by topic, and these two items live in CLAUDE.md which `/consult` already reads.

## Anti-scope

- Do NOT document `vf` surfacing here — that's in 015.
- Do NOT document DDSA exit-reason capability here — that's in 018.
- Do NOT document `rssi` or native analyzer UI presence here — those are knowledge-file updates that ship alongside their code tickets or in follow-ups if truly standalone.

## Size

XS (was S in earlier draft). Two bullets + two one-line comments. No cross-file audit spanning knowledge/reference/* etc.
