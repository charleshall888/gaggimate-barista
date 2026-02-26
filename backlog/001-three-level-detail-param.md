---
title: Add three-level detail parameter to analyze_shot
status: open
priority: low
type: idea
tags: [mcp, diagnostics, tokens]
created: 2026-02-26
updated: 2026-02-26
blocks: []
blocked-by: []
---

`analyze_shot` currently returns the same blob for every call. Add a `detail` parameter so callers can request the granularity they need:

| Level | Contents | When to use |
|-------|----------|-------------|
| `summary` (default) | Key indicators only — no phase samples | Quick feedback loop, first triage |
| `per_phase` | Full diagnostics + per-phase breakdowns | Diagnosing a specific phase problem |
| `per_phase_detailed` | Everything + representative samples per phase | Deep dive, timing matters |

The `/feedback` skill should default to `summary`. The `/diagnose` skill should start with `summary` and escalate to `per_phase` when it needs to localize a problem.

**Implementation notes to explore:**
- Add `detail: str = "summary"` to `server.py` `analyze_shot`, validate against `VALID_DETAIL_LEVELS`, silently fall back to `summary` for unknown values (log a warning)
- Dispatch from `transform_shot_for_ai()` to different output builders
- Keep the detail-level naming stable before the skill files reference it — upstream changed `detailed` → `per_phase_detailed` in the very next PR after introducing it
- This item blocks the diagnostics module (#2) and profile compliance (#3) since those feed into `per_phase` output
