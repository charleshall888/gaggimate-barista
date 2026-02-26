---
title: Expand TransformedShot TypedDict contracts for diagnostic output
status: wontfix
priority: low
type: chore
tags: [mcp, types, diagnostics]
created: 2026-02-26
updated: 2026-02-26
blocks: []
blocked-by: [2]
---

We already have TypedDicts for `ShotSummary`, `PhaseData`, etc. When the diagnostics module (#2) ships, add corresponding TypedDicts for its output so the schema is explicit and self-documenting.

Useful classes to add (adapting from upstream):
- `SummaryDiagnostics` — lightweight summary-level output (resistance avg/slope, channeling risk, temp stability, profile compliance RMSE/overshoot)
- `ShotDiagnostics` — full diagnostic output with sub-sections per metric group
- `ProfileComplianceMetrics` — RMSE, overshoot, undershoot, annotations
- `PhaseDiagnostics` — per-phase metrics by type (preinfusion / brew / decline)

The TypedDict approach makes the contract explicit for LLM consumers, enables IDE autocompletion, and serves as living documentation of what the agent can expect from each detail level. Keep annotations as dicts of string → string labels (e.g. `{"channeling_risk": "HIGH"}`) so the LLM gets both the numeric value and its interpretation.

Blocked by #2 since the types should be defined alongside the computation, not before it.
