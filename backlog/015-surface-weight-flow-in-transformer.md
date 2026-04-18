---
id: "015"
title: "Surface weight_flow_g_s in TransformedSample + FlowSummary"
status: open
priority: high
type: feature
parent: "013"
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-18
---

# Surface weight_flow_g_s in TransformedSample + FlowSummary

## What this delivers

Expose per-sample weight flow (grams/second) through `analyze_shot` so `/diagnose` can correlate pump flow vs weight flow — the primary visual indicator of channeling and the most reliable dose-out signal when BT scale readings are noisy.

## Context

The parser at `mcp/src/gaggimate_mcp/parsers/shot.py` line 33 already maps `'VF': 8` and line 64 defines a `FieldDef`. The binary format has always had it. The gap is purely on the transformer side — `TransformedSample` in `transformers/shot.py` exposes `flow_ml_s` (pump flow) but not weight flow.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Decision Record DR-4. Note: an earlier draft of the research claimed `vf` was not in `.slog` — that was factually wrong and has been corrected.

## Acceptance criteria

- `TransformedSample` exposes `weight_flow_g_s: float` sourced from parser's `vf` field
- `FlowSummary` aggregates add: peak weight flow, average weight flow, time to first nonzero weight flow
- `/diagnose` interprets pump-flow / weight-flow divergence as a channeling signal where appropriate
- Regression check: run against an existing checked-in fixture shot and verify values match a hand-computed baseline (requires 016 fixture harness to be in place first, but this ticket does not block on it — manual validation against a recent shot is acceptable as an interim step)

## Dependencies

- Prefer 016 (regression harness) to land first for safer validation, but not a hard block
