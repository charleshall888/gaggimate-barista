---
id: "020"
title: "Add deep-link to /analyze/{shot_id} in /diagnose output"
status: superseded
priority: low
type: feature
parent: "013"
tags: [gaggimate-1-8-0-upgrade]
discovery_source: research/gaggimate-1-8-0-upgrade/research.md
created: 2026-04-18
updated: 2026-04-18
superseded-by: "018"
---

> **Superseded** by ticket 018 during critical review. Three-line URL addition to `/diagnose` output should land in the same PR as the DDSA port that also modifies `/diagnose` output. Archive-only.

# Add deep-link to /analyze/{shot_id} in /diagnose output

## What this delivers

`/diagnose` output includes a deep-link URL the user can click to open the shot in the 1.8.0 native analyzer UI, where they can see phase-stop overlays, pump-flow vs weight-flow chart, exit-reason classification, and export a chart image for sharing back into the conversation.

## Research context

From research/gaggimate-1-8-0-upgrade/research.md: Decision Record DR-1 option (b). User chose option (a) (full port) as the primary direction, but (b) remains a useful complement — even with the full port, a link to the interactive chart is genuinely valuable for visual pattern recognition and doesn't conflict with anything.

## Acceptance criteria

- Every `/diagnose` response includes a single line like `Interactive chart: http://{gaggimate_host}/analyze/{shot_id}` (or similar) at a sensible position in the output
- URL is built from the same `GAGGIMATE_HOST` env var the MCP already uses
- Shot ID formatting matches the device's URL scheme (confirm on first test)
- No other behavior change in `/diagnose` output

## Notes

- XS effort. Can ship independently of 018.
- Can also prompt the user: "Paste the exported chart image here if you want me to read it directly" — creates a vision-Claude + chart image channel at no extra implementation cost.
