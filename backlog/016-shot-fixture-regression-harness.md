---
id: "016"
title: "Shot-fixture regression harness"
status: open
priority: high
type: chore
parent: "013"
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-18
---

# Shot-fixture regression harness

## What this delivers

A checked-in set of representative `.slog` fixture files plus golden transformer output, so any future change to the parser or transformer can be validated against known-good output before merging.

## Why now

The research artifact flagged this as the missing safety net behind several other 1.8.0 tickets: the DDSA algorithm port (018), the weight-flow surfacing (015), and the BLE-precision drift investigation (022) all risk silent regression on historical shot diagnosis. We have no fixtures today, so every transformer change is validated by hand against whatever shot happens to be fresh in history.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Feasibility Assessment noted the absence of fixtures as a cross-cutting risk. Also in the Through-lines of the critical review: "No regression harness means every S-effort ticket is actually S + risk of silent regression."

## Acceptance criteria

- A `mcp/tests/fixtures/shots/` directory containing at least 3 representative `.slog` files covering: (a) a healthy bloom-slide profile, (b) a decline profile, (c) a shot with BT-scale artifacts
- Golden transformer output (JSON snapshot) checked in alongside each fixture
- A pytest test that loads each fixture, runs it through the full parser + transformer pipeline, and diffs against the golden output
- Document how to refresh fixtures intentionally (when a transformer change is expected)
- Must run in CI if CI exists; locally via `pytest mcp/tests/test_shot_regression.py` otherwise

## Blocks

- 018 (DDSA port)
- 022 (BLE-precision drift investigation)
