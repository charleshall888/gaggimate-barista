# Decomposition: gaggimate-1-8-0-upgrade

## Epic
- **Backlog ID**: 013
- **Title**: Gaggimate firmware 1.8.0 upgrade adaptation

## Work Items
| ID | Title | Priority | Size | Depends On |
|----|-------|----------|------|------------|
| 014 | Round-trip verify manage_shot_notes on 1.8.0 | high | XS | — |
| 015 | Surface weight_flow_g_s in TransformedSample + FlowSummary | high | XS | (soft: 016) |
| 016 | Shot-fixture regression harness | high | S | — |
| 017 | Documentation pass for 1.8.0 semantics | medium | S | — |
| 018 | Port DDSA / PhaseEndStop algorithm into /diagnose | medium | L | 016 |
| 019 | Extend manage_shot_notes with native note fields | medium | S-M | 014 |
| 020 | Add deep-link to /analyze/{shot_id} in /diagnose output | low | XS | — |
| 021 | Post-upgrade behavior verification spike | low | S | — |
| 022 | BLE-precision round-trip drift investigation | low | S | 016 |

## Suggested Implementation Order

1. **Parallel P0 wave**: 014 (notes verification), 015 (weight-flow surfacing), 016 (fixture harness), 017 (docs pass), 020 (deep-link) — none block on each other; all have independent value
2. **After 014 lands**: 019 (field alignment) can start
3. **After 016 lands**: 018 (DDSA port) can start — this is the single biggest work item
4. **Verification tail**: 021 (post-upgrade behavior) and 022 (BLE precision) can run in parallel with 018 — 022 prefers 016 to land for fixture comparison

## Key Design Decisions

### Consolidation: merged two spikes into 021
Originally decomposed as two separate P3 tickets — "Mixed-era shot-history behavior check" and "Retention ordering + purge-order invariants check." Both are XS and both require the same investigation (pulling shots from the live device's history and observing behaviors). Merged into a single "Post-upgrade behavior verification spike" (021) sized S.

### Dropped during critical review
Three items from the initial decomposition candidate list were dropped:
- **mDNS discovery** — DR-3's own recommendation was against, survived into the list by inertia
- **Profile `utility: true` tagging** — cosmetic UI organization, zero extraction value
- **Pre-603 volumetric-index bug verification** — already resolved in the research artifact itself

### Critical review correcting a factual error
The research artifact initially claimed `vf` was not in `.slog` — the critical review caught this (`parsers/shot.py` line 33 already maps `'VF': 8`). DR-4 (ticket 015) was rescaled from S to XS as a result.

### User-chosen directions
Two strategic decisions were put to the user during critical review:
- **DR-1 direction**: user chose full algorithm port (L effort) over deep-link/vision-Claude path (XS) — explicit preference for agent autonomy even at higher effort + maintenance cost
- **DR-2 scope**: user chose verify + pursue full field alignment rather than verify-only YAGNI

Both choices were saved to memory as a user feedback signal.

## Created Files
- `backlog/013-firmware-1-8-0-upgrade-adaptation.md` — Gaggimate firmware 1.8.0 upgrade adaptation (epic)
- `backlog/014-verify-manage-shot-notes-1-8-0.md` — Round-trip verify manage_shot_notes on 1.8.0
- `backlog/015-surface-weight-flow-in-transformer.md` — Surface weight_flow_g_s in TransformedSample + FlowSummary
- `backlog/016-shot-fixture-regression-harness.md` — Shot-fixture regression harness
- `backlog/017-documentation-pass-1-8-0-semantics.md` — Documentation pass for 1.8.0 semantics
- `backlog/018-port-ddsa-algorithm-to-diagnose.md` — Port DDSA / PhaseEndStop algorithm into /diagnose
- `backlog/019-extend-manage-shot-notes-fields.md` — Extend manage_shot_notes with native note fields
- `backlog/020-deep-link-analyzer-in-diagnose.md` — Add deep-link to /analyze/{shot_id} in /diagnose output
- `backlog/021-post-upgrade-behavior-verification-spike.md` — Post-upgrade behavior verification spike
- `backlog/022-ble-precision-round-trip-investigation.md` — BLE-precision round-trip drift investigation
