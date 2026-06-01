---
id: "012"
title: "Update CLAUDE.md with data architecture note"
status: closed
priority: low
type: chore
parent: "005"
blocked-by: ["008"]
tags: [multi-user-data-isolation]
research: research/multi-user-data-isolation/research.md
spec: research/multi-user-data-isolation/spec.md
created: 2026-03-04
updated: 2026-03-04
closed-reason: already-done
---

# Update CLAUDE.md with data architecture note

## What this delivers

A brief note in CLAUDE.md that tells the agent (and human readers) about the two-repo model, so the agent understands where data files live and what to do if they're missing.

## Spec references

- Could Have 10: CLAUDE.md documents the data separation architecture

## Acceptance criteria

- CLAUDE.md includes a "Data Architecture" section or note explaining:
  - `coffees/`, `grind-map.md`, `user-setup.md` are symlinks to the private data repo
  - MCP `storage_path` points to the private data repo's `mcp-data/` directory
  - If `user-setup.md` reads as an unconfigured template, agent should prompt user to run `bin/setup-data-repo.sh`
- Note is concise (≤ 10 lines)
