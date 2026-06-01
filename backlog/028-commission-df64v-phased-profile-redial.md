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
blocked-by: ["026"]
created: 2026-06-01
updated: 2026-06-01
---

# Commission the DF64V and run the phased per-coffee profile re-dial

## Why

The per-coffee profiles were authored against the Sette's high-fines bimodal output at a reduced peak pressure, and the new burr is unseasoned with an unknown working point, so pulling the existing profiles as-is on day one will mis-extract, and re-dialing before the burrs settle would tune against a moving target.

## Role

Commissions the new grinder (alignment check, find the chirp point, season, learn the practical RPM floor) and then re-dials grind on the seasoned burr per coffee, adjusting peak pressure or bloom only when a shot is diagnosed under-extracted — keeping the proven gentle profiles intact and recoverable — so each coffee returns to a dialed-in state on the DF64V with telemetry as the arbiter.

## Integration

Writes re-dialed settings into the fresh grind map in the shared notation, and updates the per-coffee profile JSONs following the repo-first-then-device ordering. Depends on the active grinder being the DF64V in user-setup and the fresh map existing as the logging destination.

## Edges

- Proven per-coffee profiles must be snapshotted before any in-place re-author, so a five-star configuration stays recoverable if the new burr underperforms.
- Profile writes must follow repo-first-then-device ordering; the repo JSON stays the recoverable source of truth.
- The pressure or bloom change is triggered by an under-extraction diagnosis, not by mere thinness, which is the expected flat-burr clarity trade managed via RPM and ratio.
- Phase boundary: do not open pressure or bloom experiments until grind is re-dialed and the seasoning trend has flattened.
- Non-goal: re-engineering profiles up front before seasoning settles.

## Touch points

- coffees/*/ (per-coffee profile JSONs; snapshot to *.sette.json before re-author)
- coffees/onyx-ethiopia-bochesa/bloom-slide.json (representative 7.5-bar bloom-slide profile)
- knowledge/ESPRESSO_TASTING_GUIDE.md (under-extraction diagnosis methodology)
