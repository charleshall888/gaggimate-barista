---
id: "015"
title: "Surface weight_flow_g_s in TransformedSample + FlowSummary"
status: complete
priority: medium
type: feature
parent: "013"
blocked-by: []
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-20
session_id: null
lifecycle_phase: plan
lifecycle_slug: surface-weight-flow-g-s-in-transformedsample-flowsummary
complexity: complex
criticality: high
spec: lifecycle/surface-weight-flow-g-s-in-transformedsample-flowsummary/spec.md
areas: [mcp]
---

# Surface weight_flow_g_s in TransformedSample + FlowSummary

## What this delivers

Expose per-sample weight flow (grams/second) through `analyze_shot` so `/diagnose` can correlate pump flow vs weight flow — the primary visual indicator of channeling and the most reliable dose-out signal when BT scale readings are noisy.

## Priority: medium

Additive change — nothing regresses if this slips. The parser already reads `vf`; the gap is only transformer surfacing. `/diagnose` still works on pump flow alone. Medium priority reflects "useful feature" not "blocking".

## Context

The parser at `mcp/src/gaggimate_mcp/parsers/shot.py` line 33 already maps `'VF': 8` and line 64 defines a `FieldDef`. The binary format has always had it. The gap is purely on the transformer side — `TransformedSample` in `transformers/shot.py` exposes `flow_ml_s` (pump flow) but not weight flow.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Decision Record DR-4. Note: an earlier draft of the research claimed `vf` was not in `.slog` — that was factually wrong and has been corrected.

## Acceptance criteria

- `TransformedSample` exposes `weight_flow_g_s: float` sourced from parser's `vf` field.
- `FlowSummary` aggregates add: `peak_weight_flow_g_s`, `avg_weight_flow_g_s`, `time_to_first_nonzero_weight_flow_s`.
- `/diagnose` surfaces pump-flow vs weight-flow divergence as a diagnostic line when the divergence exceeds the threshold documented in DR-4 follow-up or in `knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md` (port from how native analyzer interprets it — specific threshold to be established during implementation, not left to reviewer judgment).
- Regression check: fixture-based test asserts transformer output matches golden values for all three added fields on each of 016's fixture shots. No "manual validation acceptable" escape hatch — this ticket hard-blocks on 016.
- Documentation: the tool docstring for `analyze_shot` is updated to include the three new fields. No separate docs ticket.

## Dependencies

- 016 (regression harness) is a hard block — the fixture-based test in the AC requires 016's fixtures and golden-output infrastructure.

## Supersedes content from

- Old ticket 017's "`vf` / weight flow in shot samples" documentation bullet — folded into this ticket's AC so code and docs ship together.
