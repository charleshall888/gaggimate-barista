---
id: "017"
title: "Documentation pass for 1.8.0 semantics"
status: open
priority: medium
type: chore
parent: "013"
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-18
---

# Documentation pass for 1.8.0 semantics

## What this delivers

Propagate firmware 1.8.0 semantic shifts and additive capabilities through our single-source-of-truth documentation so future agent work is correctly grounded.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Decomposition Candidate #4 (formerly sized XS, upgraded to S by critical review because of the project's single-source-of-truth architecture across CLAUDE.md + knowledge/ + knowledge/reference/ + skills/ + MEMORY.md).

## Topics to document

- **Shot history retention shift**: `MAX_HISTORY_ENTRIES = 100` removed, replaced by `MIN_FREE_SPACE_BYTES = 500 KB` floor. Capacity purge now also deletes the companion `.json` sidecar.
- **`evt:status.bt` semantic flip** — **pitfall alert**: now reflects `profile.isVolumetric()` rather than `settings.isVolumetricTarget()`. Any future `diagnose_connection` extension reading this field must account for the flip. Document prominently so future code doesn't inherit the trap.
- **Additive `rssi` fields** in `/api/status`, `/api/scales/list`, `/api/scales/info`.
- **Native shot analyzer UI availability**: deep-link `http://{host}/analyze/{shot_id}`, chart-image export, Note editor, statistics page. Knowledge files should mention this as a complementary surface.
- **DDSA / exit-reason capability in native UI**: brief mention so the concept is present in our knowledge base before 018 lands.
- **`vf` / weight flow in shot samples**: surfaced by 015.
- **Mixed-era shot compatibility**: version byte unchanged between 1.7.3 and 1.8.0, so parser can't tell them apart — document as a known limitation.

## Acceptance criteria

- CLAUDE.md has a terse "Firmware 1.8.0 notes" bullet list or section anchoring the above
- Relevant knowledge files (`knowledge/GAGGIMATE_PROFILE_CREATION_GUIDE.md` for `utility:` flag documentation context, `knowledge/reference/*` for deep references) updated where the concept fits
- MEMORY.md updated if a new "source of truth" table row applies
- `/consult` can answer "what changed in firmware 1.8.0" by routing to the right file
- No duplicated content; each fact in exactly one place per project convention
