---
id: "022"
title: "BLE-precision round-trip drift investigation"
status: superseded
priority: low
type: spike
parent: "013"
blocked-by: ["016"]
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-18
superseded-by: "021"
---

> **Superseded** by ticket 021 during critical review. Same mechanical activity as 021's mixed-era check (pull pre/post-upgrade shots, diff fields) with a different analytical lens. Merged into 021 as question (c); priority elevated to `high` as part of the merge to reflect blast radius. Archive-only.

# BLE-precision round-trip drift investigation

## What this delivers

Empirical determination of whether firmware 1.8.0's BLE wire-format precision change (`snprintf("%.Nf", …)` → `std::to_string` with 6-digit default) causes least-significant-bit drift in parsed floats that end up in `.slog` samples.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Decomposition Candidate #7. The firmware schema diff agent reported the wire format change. The artifact initially dismissed the change as "we don't speak BLE directly," but the critical review flagged this as potentially leaking into the BLE→`.slog` pipeline if firmware round-trips BLE strings through `atof` before persisting.

## Hypothesis

If the firmware's internal BLE consumer does `atof(ble_string)` and that value gets written into shot log samples, the 2-digit → 6-digit precision change could introduce sub-LSB noise in pressure/flow/weight fields — small enough to pass unit-style tolerance checks but large enough to break any exact-match regression test.

## Acceptance criteria

- Pick a fixture shot from 016 (pre-upgrade era) and a post-upgrade shot with similar profile/conditions
- Compare raw sample values field-by-field (cp, fl, v, tf, pf, etc.) — look for any systematic bias or precision shift
- If drift is detected: document magnitude, affected fields, and whether any downstream metric (compliance metrics, flow summary) could be affected
- If no drift: document the negative result so we can trust our fixtures across the version boundary

## Dependencies

- 016 (regression harness) provides pre-upgrade fixture reference
- 021 (post-upgrade behavior verification) provides post-upgrade samples

## Notes

- Investigation-only — no code changes expected unless drift is detected
- If drift IS detected, follow-up work (version-gated parser or precision normalization) would be a new ticket
