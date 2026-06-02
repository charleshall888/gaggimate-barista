---
schema_version: "1"
uuid: fb432648-8be0-4756-92ac-d90088278c4e
title: "Commission the DF64V and run the phased per-coffee profile re-dial"
status: backlog
priority: high
type: feature
tags: [df64v-ssp-migration]
discovery_source: cortex/research/df64v-ssp-migration/research.md
parent: "024"
blocked-by: []
created: 2026-06-01
updated: 2026-06-02
---

# Commission the DF64V and run the phased per-coffee profile re-dial

## Why

The DF64V (flat SSP Cast Lab Sweet V3) is a fundamentally different grinder from the Sette 270 (conical): a cleaner, more unimodal particle distribution with far fewer fines. The existing per-coffee profiles were authored as *corrections* for the Sette's high-fines bimodal output — gentle shapes at reduced peak pressure to avoid choking and channeling. Carrying those corrections onto a burr that no longer has the problem would taint the dial-in from day one. The burr is also unseasoned with an unknown working point. So the deliberate choice is to **start fresh**: commission the grinder, then dial each coffee from a neutral baseline rather than porting Sette-era profiles. (Decision: 2026-06-02 — fresh start over in-place re-dial.)

## Role

Commissions the new grinder (alignment check, find the chirp point, season the burrs, learn the practical RPM floor), then dials each coffee **fresh** on the seasoned burr — grind first from a neutral starting point, building a custom pressure/flow profile only when a shot is diagnosed under-extracted, with telemetry as the arbiter. Starts each coffee from the firmware's Automatic Pro built-in profile (sized to dose) as the un-opinionated baseline. Does NOT re-dial or port the archived Sette profiles.

## Integration

Writes grind settings into the fresh DF64V grind map in the shared notation (RPM + chirp/marks). Builds new per-coffee profile JSONs from scratch following repo-first-then-device ordering (the repo JSON is the recoverable source of truth). The archived Sette profiles live at `coffees/<coffee>/sette/` as read-only historical reference and are never pulled as a DF64V starting point. Depends on the active grinder being the DF64V in user-setup and the fresh map existing as the logging destination.

## Edges

- Start fresh from a neutral baseline (Automatic Pro built-in for the dose) — do NOT carry the Sette-tuned profiles over; they were corrections for a grinder we no longer use.
- The archived Sette profiles (`coffees/<coffee>/sette/`) are kept for historical reference only; they stay recoverable but are never the starting point.
- New profile writes must follow repo-first-then-device ordering; the repo JSON stays the recoverable source of truth.
- A pressure or bloom change is triggered by an under-extraction *diagnosis*, not by mere thinness — lighter body / higher clarity is the expected flat-burr trade, managed via RPM and ratio first.
- Phase boundary: do not open pressure or bloom experiments until grind is dialed and the seasoning trend has flattened.
- Non-goal: porting or re-engineering the Sette-era profiles; building elaborate custom profiles up front before seasoning settles.

## Touch points

- coffees/<coffee>/sette/ (archived Sette-era profiles — read-only historical reference, never the DF64V starting point)
- knowledge/automatic-pro/ (neutral firmware baseline profile to start each coffee from; 16/18/20/22g working JSONs)
- knowledge/grinders/DF64V.md + knowledge/grinders/_NOTATION.md (DF64V adjustment system + grind-recording notation)
- knowledge/ESPRESSO_TASTING_GUIDE.md (under-extraction diagnosis methodology — the arbiter for any pressure/bloom change)
