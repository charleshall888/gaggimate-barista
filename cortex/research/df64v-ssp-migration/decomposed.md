# Decomposition: df64v-ssp-migration

## Epic
- **Backlog ID**: 024
- **Title**: Migrate grinder layer: Sette 270 → DF64V + SSP Cast Lab Sweet V3

## Work Items
| ID | Title | Priority | Size | Depends On |
|----|-------|----------|------|------------|
| 025 | Build the grinder-agnostic knowledge layer (DF64V + notation + de-Sette) | high | M | — |
| 026 | Switch the grind map and user-setup to the DF64V | high | S | 025 |
| 027 | Parameterize feedback/new-coffee/consult to read the active grinder | medium | M | 025 |
| 028 | Commission the DF64V and run the phased per-coffee profile re-dial | high | L | 026 |

## Suggested Implementation Order
1. **025** first — the grinder-agnostic knowledge layer (DF64V reference, per-grinder template, grinder-neutral notation, de-Setted shared knowledge). Unblocks everything else and has no external clock.
2. **026** and **027** in parallel after 025. 026 is the private-repo data flip (archive Sette map + telemetry snapshot, fresh map, repoint the Grinder field). 027 is the skills parameterization and is **lifecycle-gated** (protected paths) — route it through `/cortex-core:lifecycle`; it must not block the physical track.
3. **028** last — commission the grinder and run the phased per-coffee re-dial. Physical/clock-driven: commissioning can begin the moment the grinder arrives, but profile logging waits on the fresh map (026).

Two tracks: the software/knowledge track (025, 027) is grinder-agnostic from the start; the physical track (026 → 028) runs under the seasoning clock.

## Grouping Notes
- **Ticket 025** also absorbs the per-grinder `_TEMPLATE.md` — an aspect of the grinder-reference piece, not a separate analytical piece. Intra-ticket order: establish the notation + DF64V reference + template, then re-key the shared knowledge to cross-link them.
- **Ticket 028** absorbs the commission / first-light step (feasibility work-stream 0) as the physical front-end of the profile-strategy piece. Intra-ticket order: commission (alignment, chirp, season, learn RPM floor) → re-dial grind → conditional pressure/bloom experiments once seasoning flattens.

## Consolidation Notes
At the R15 batch-review gate the user chose `consolidate-pieces` ("consolidate as much as you can"). The seven 1:1 piece→ticket drafts were merged into four:
- **025** ← the grinder-reference, dialing-notation, and shared-extraction-knowledge pieces. They form one grinder-agnostic knowledge-layer unit: the DF64V reference and the notation are the contract the de-Setted shared files cross-link, none is lifecycle-gated, and they deliver value only together. Surviving role: build the grinder-agnostic knowledge layer.
- **026** ← the grind-history and setup-pointer pieces. Both are private-repo data-layer edits that together "flip the data to the DF64V" (archive the Sette map with a telemetry snapshot, start the fresh agnostic map, repoint the user-setup Grinder field); small and coupled by the same migration moment. Surviving role: switch the grind map and user-setup to the DF64V.
- **027** (skills) and **028** (commission + profile re-dial) were deliberately **left standalone** rather than merged further: 027 sits across the lifecycle-gated protected-path boundary (merging it would force the whole knowledge layer through `/cortex-core:lifecycle`), and 028 is the L-effort, ~2-week physical dial-in (merging it would bury operational work inside a quick file edit).

## Created Files
- `backlog/024-migrate-grinder-layer-to-df64v-ssp.md` — Epic: Migrate grinder layer: Sette 270 → DF64V + SSP Cast Lab Sweet V3
- `backlog/025-grinder-agnostic-knowledge-layer.md` — Build the grinder-agnostic knowledge layer
- `backlog/026-switch-grind-map-and-user-setup-to-df64v.md` — Switch the grind map and user-setup to the DF64V
- `backlog/027-parameterize-skills-active-grinder.md` — Parameterize the grinder-aware skills to read the active grinder
- `backlog/028-commission-df64v-phased-profile-redial.md` — Commission the DF64V and run the phased per-coffee profile re-dial
