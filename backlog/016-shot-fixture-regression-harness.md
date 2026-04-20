---
id: "016"
title: "Shot-fixture regression harness"
status: complete
priority: high
type: chore
parent: "013"
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-20
session_id: null
lifecycle_phase: complete
lifecycle_slug: shot-fixture-regression-harness
complexity: complex
criticality: medium
spec: lifecycle/shot-fixture-regression-harness/spec.md
areas: [tests]
---

# Shot-fixture regression harness

## What this delivers

A checked-in set of representative `.slog` fixture files plus golden transformer output, so any future change to the parser or transformer can be validated against known-good output before merging.

## Why now

The research artifact flagged this as the missing safety net behind several 1.8.0 tickets: the DDSA algorithm port (018), the weight-flow surfacing (015), and the post-upgrade drift investigation (021's BLE-precision sub-question). All three risk silent regression on historical-shot diagnosis. We have no fixtures today, so every transformer change is validated by hand against whatever shot happens to be fresh in history.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Feasibility Assessment. Critical review through-line: "No regression harness means every S-effort ticket is actually S + risk of silent regression."

## Fixture sourcing guidance (not "find something somewhere")

Three shots are needed. Specific candidates:

- **(a) Healthy bloom-slide profile**: Shot 170 (Choco Coffee Hacienda La Papaya Typica Anaerobic, 5★ dialed-in, 13E grind, 94°C, Bloom Slide 7.5→4 bar, 1:2.5). Referenced in MEMORY.md as a known-clean reference. Pull via `list_recent_shots` + `analyze_shot`.
- **(b) Decline profile**: pick any shot from a pre-bloom-era profile (e.g. the "Fruit Slide" 9-bar peak profile mentioned in MEMORY.md). If no such shot is in current history, capture one by running an older profile intentionally during this ticket's implementation. Document which shot_id was used.
- **(c) BT-scale artifact shot**: grep recent shot history for shots with `weight_anomalies` flagged in the transformer output or obvious 0g drops / spikes. If none exist in current history, use a shot from the decline-profile era when BT-scale drift was more common. Document which shot_id was used.

If any specific shot_id referenced above has been evicted under capacity-based retention, document what was substituted and why in the fixture README.

## Acceptance criteria

- Create `mcp/tests/fixtures/shots/` directory with at least 3 `.slog` files per the sourcing guidance above.
- Alongside each `.slog`, a `<shot_id>.golden.json` containing the full `TransformedSample` + `ShotSummary` output of running the current transformer on that `.slog`. Checked in.
- Create `mcp/tests/fixtures/shots/README.md` documenting: origin shot_id, profile, coffee (if known), why this shot was chosen, how to regenerate the golden if a transformer change is intentional.
- New pytest file `mcp/tests/test_shot_regression.py` that loads each fixture, runs the full parser + transformer pipeline, and asserts deep equality against the golden JSON (tolerance: exact match on categorical fields, `1e-6` on floats).
- Test command documented in the fixtures README: `pytest mcp/tests/test_shot_regression.py`.
- Test is wired into any existing CI config; if none exists, note that in the epic and flag as a follow-up.
- Procedure for "refreshing fixtures intentionally" is specified: `python -m gaggimate_mcp.tools.refresh_fixtures <shot_id>` OR step-by-step instructions if a script is overkill. No vague "document how" requirement.

## Blocks

- 015 (weight-flow surfacing)
- 018 (DDSA port)
- 021's BLE-precision drift sub-investigation
