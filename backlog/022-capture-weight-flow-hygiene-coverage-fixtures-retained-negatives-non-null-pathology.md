---
schema_version: "1"
uuid: 9ec1a00d-533a-4ac2-90b4-4cf865bc122b
title: "Capture weight-flow hygiene-coverage fixtures (retained-negatives + non-null pathology)"
status: backlog
priority: low
type: chore
tags: [gaggimate-1-8-0-upgrade]
created: 2026-04-20
updated: 2026-04-20
parent: "015"
---

## What this delivers

Two new committed fixtures in `mcp/tests/fixtures/shots/` that close the documented coverage gaps from backlog 015:

1. **Retained-negatives fixture** — a shot whose brew-phase (post-pump, `pf > 0`) samples contain at least one `vf < 0` reading (honest scale drift during extraction). This exercises the `avg_weight_flow_g_s` code path where the base hygiene rule is applied without an additional `vf > 0` filter. A silent `vf >= 0` filter slipping into `avg_weight_flow_g_s` would today escape 015's regression harness because all three committed fixtures (246, 247, 249) have their negative-`vf` samples pre-brew only.

2. **Non-null pathology-survivor fixture** — a shot where the Unified Hygiene Rule rejects some samples (tare spike, clamp sentinel, or pre-pump artifact) but leaves non-null `peak_weight_flow_g_s`, `avg_weight_flow_g_s`, and `time_to_first_nonzero_weight_flow_s` aggregates. Fixture 247 exercises the rejection paths but zeroes out all three aggregates; we need a fixture where the hygiene rule filters pathology AND retains valid data so the aggregates' non-null values can be verified as correct.

## Why

Both gaps are explicitly documented in 015's Scope Boundaries → "Known coverage gaps (critical review, not closed in 015)." A silent regression that adds a `vf >= 0` filter to `avg_weight_flow_g_s` or corrupts the non-null-survivor path would pass the current 246/247/249 regression suite.

Deferred from 015 because the existing fixture cohort (246–249) doesn't contain shots with the needed pathology, and synthesizing fixtures would undercut the 016 regression harness's "real device capture" foundation.

## Acceptance criteria

- One new `.slog` + `.golden.json` pair committed for the retained-negatives case.
- One new `.slog` + `.golden.json` pair committed for the non-null pathology-survivor case (may be the same shot if one captures both behaviors).
- `mcp/tests/fixtures/shots/README.md` updated with per-fixture prose naming which coverage gap each closes.
- Regeneration via `refresh_fixtures` reproduces the golden byte-stably.
- Regression test `pytest tests/test_shot_regression.py` passes.
- Added test invariants (shot-scoped, not cross-fixture): the retained-negatives fixture has `avg_weight_flow_g_s != null` with at least one brew-phase sample whose `vf < 0`; the pathology-survivor fixture has all three aggregates non-null.

## Capture strategy

The device's shot history is capacity-gated (see 021 for retention caveats), so the right moment to capture is opportunistic:

- Retained-negatives: look for a shot where an early brew-phase sample reads slightly negative `vf` before the real signal lands. Recent shots on the currently-active coffee may already contain this pattern.
- Non-null pathology-survivor: harder to produce deliberately. Tare-spike-then-real-signal pattern is the archetype — when a user zeroes the scale mid-shot, or scale-touch artifacts during bloom. Check recent pathological shots already on device.

One approach: query recent shots via `list_recent_shots` at implementation time, scan their `.slog` samples for `vf` patterns matching the two target archetypes, pull via `refresh_fixtures --fetch`.

## Dependencies

- 015 — hard block. Defines the hygiene-rule behaviors these fixtures validate.
- 016 — hard block. Provides the `refresh_fixtures` CLI and regression harness.

## Risk notes

- Fixture availability — if no suitable shot exists on device and none occurs during the investigation window, the ticket stalls. Document honestly and close as "deferred until a qualifying shot is captured" rather than synthesizing a fixture.
- S effort — mostly hunting for the right shot, then mechanical capture. No algorithm work.
