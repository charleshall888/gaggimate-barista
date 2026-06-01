---
schema_version: "1"
uuid: c5880269-8375-44a3-9fd0-c64028fecf45
title: "Switch the grind map and user-setup to the DF64V"
status: refined
priority: high
type: chore
tags: [df64v-ssp-migration]
discovery_source: cortex/research/df64v-ssp-migration/research.md
parent: "024"
blocked-by: ["025"]
created: 2026-06-01
updated: 2026-06-01
complexity: complex
criticality: high
spec: cortex/lifecycle/switch-the-grind-map-and-user/spec.md
areas: []
---

# Switch the grind map and user-setup to the DF64V

## Why

The active data layer still describes the Sette: the user-setup Grinder field names the Sette 270, so every skill that keys off it selects the wrong grinder, and the grind map's Grind column holds Sette codes that cannot accept DF64V settings without blending two incompatible notations. The telemetry behind the proven five-star shots can also be silently purged by the device's free-space floor, so simply leaving the old rows in place risks an audit trail of dead references.

## Role

Flips the private-repo data layer to the new grinder: it freezes the Sette grind history into a read-only archive with its referenced shot telemetry snapshotted, starts a clean DF64V map that records settings in the shared notation plus an RPM column, and repoints the user-setup Grinder field to the DF64V with SSP V3 (and its RPM note), so the selector and the logging destination both reflect the actual equipment.

## Integration

Reads the shared dialing-notation contract for the fresh map's Grind column, sets the Grinder-field selector value the grinder-aware skills resolve against, and provides the fresh map as the destination the feedback workflow and profile re-dial write into. All targets live in the private data repo via the existing symlinks.

## Edges

- The grind-map archive must be a history-preserving move within the private data repo, not a lossy copy.
- "Lose nothing" holds only if the referenced shot telemetry is snapshotted before archiving, because the device's free-space purge can delete the companion sidecars.
- Roast, process, ratio, temperature, and rating stay transferable signal; the grind value does not translate and must not be carried forward as if it did.
- The user-setup overwrite erases the only in-repo record of the Sette, so the prior value must stay recoverable through committed git history under the auto-commit policy.
- Non-goals: converting old Sette codes into DF64V marks (there is no defined mapping), and changing other user-setup sections.
- Internal order: snapshot telemetry and archive the old map, start the fresh map, then repoint user-setup.

## Touch points

- grind-map.md (symlink into the private data repo; archived to grind-map-sette-270.archive.md via git mv)
- grind-map.example.md (fresh-map column format reference)
- user-setup.md (Grinder field; symlink into the private data repo)
- user-setup.example.md:8 (grinder-neutral example pattern)
