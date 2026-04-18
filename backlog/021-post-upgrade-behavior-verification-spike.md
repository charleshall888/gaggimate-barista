---
id: "021"
title: "Post-upgrade behavior verification spike"
status: open
priority: low
type: spike
parent: "013"
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-18
---

# Post-upgrade behavior verification spike

## What this delivers

Empirical confirmation of two behavioral invariants the research artifact flagged as "unverified" after upgrade: (a) mixed-era shot compatibility between 1.7.3 and 1.8.0 `.slog` files in the same history, and (b) shot-history ordering + purge-order invariants under the new capacity-based retention.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Decomposition Candidates #5 and #6 (mixed-era + retention ordering), consolidated here because both require the same investigation: pulling shots from the live device's history and comparing behaviors.

## Two questions to answer

### (a) Mixed-era shot compatibility

`SHOT_LOG_VERSION` is still 5 in 1.8.0 and no version gating exists in the parser. If the firmware introduced subtle internal semantic shifts (float precision round-trip through BLE serialization, phase-transition sample semantics, absence/presence of sidecar) while keeping the version byte fixed, our parser has no way to distinguish a 1.7.3 shot from a 1.8.0 shot.

- Pull one shot logged before upgrade and one logged after
- Run both through the full parser + transformer pipeline
- Diff transformed outputs — document any systematic differences (not per-shot variation, but cross-era deltas)

### (b) Retention ordering + purge-order invariants

`MAX_HISTORY_ENTRIES = 100` was removed; `MIN_FREE_SPACE_BYTES = 500 * 1024` now gates retention. Unknown whether index ordering is still newest-first and whether purges still happen oldest-first under space pressure.

- Query `/api/history/index.bin` and verify entry order is newest-first
- If possible: simulate space pressure (fill or probe the device's free space) and observe which entries are purged
- Document any change in ordering from 1.7.3 behavior

## Acceptance criteria

- Findings captured in `research/gaggimate-1-8-0-upgrade/verification-notes.md`
- If mixed-era drift is detected, flag as a ticket for parser version-gating
- If retention ordering changed, document in 017 (documentation pass)

## Notes

- Can be done informally — no code required, just observation
- Best run after a week or two of post-upgrade shots so mixed-era samples exist naturally
