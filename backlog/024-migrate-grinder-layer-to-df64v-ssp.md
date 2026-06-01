---
schema_version: "1"
uuid: bffcb516-5ec4-4d67-a732-93e0bdd2bf1f
title: "Migrate grinder layer: Sette 270 -> DF64V + SSP Cast Lab Sweet V3"
status: backlog
priority: high
type: epic
tags: [df64v-ssp-migration]
discovery_source: cortex/research/df64v-ssp-migration/research.md
created: 2026-06-01
updated: 2026-06-01
---

# Migrate grinder layer: Sette 270 → DF64V + SSP Cast Lab Sweet V3

Retire the Baratza Sette 270 and adopt the **DF64V (Gen 3, variable-speed)** with **SSP Cast Lab Sweet V3 Red Speed *espresso* burrs** as the sole grinder, and rebuild the repo's grinder layer to be **grinder-agnostic** — a per-grinder knowledge file selected by the `user-setup.md` Grinder field, a grinder-neutral grind-logging notation, and skills/knowledge that defer to config rather than hardcoding any one grinder — so another user can fork the repo and plug in their own grinder.

Full research, decision records, and the recalibrated evidence picture (including why the "can't build espresso pressure" reputation belongs to the V2 filter Silver Knight burr / other grinders / fixable alignment, **not** the V3 Red Speed espresso burr on a DF64V) live in `cortex/research/df64v-ssp-migration/research.md`.

## Scope
- **025** — Build the grinder-agnostic knowledge layer (DF64V reference + per-grinder template, grinder-neutral notation, de-Setted shared knowledge).
- **026** — Switch the grind map and user-setup to the DF64V (archive Sette map with telemetry snapshot; fresh agnostic map; repoint the Grinder field).
- **027** — Parameterize feedback / new-coffee / consult to read the active grinder from config (lifecycle-gated; protected skill paths).
- **028** — Commission the DF64V and run the phased per-coffee profile re-dial (physical, clock-driven).

## Tracks & order
The software/knowledge track (025, 027) is grinder-agnostic from the start and runs on no external clock; the physical track (026 → 028) runs under the seasoning clock. Suggested order: **025 → (026, 027 in parallel) → 028**. Commissioning can begin the moment the grinder arrives; profile logging waits on 026.
