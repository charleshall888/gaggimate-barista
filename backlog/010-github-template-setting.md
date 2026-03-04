---
id: "010"
title: "Enable GitHub Template repository setting"
status: open
priority: low
type: chore
parent: "005"
blocked-by: ["006"]
tags: [multi-user-data-isolation]
research: research/multi-user-data-isolation/research.md
spec: research/multi-user-data-isolation/spec.md
created: 2026-03-04
updated: 2026-03-04
---

# Enable GitHub Template repository setting

## What this delivers

The public repo is marked as a GitHub Template, so new users can click "Use this template" and get a clean single-commit copy with no personal data history.

## Spec references

- Must Have 6: Public repo becomes a GitHub Template

## Acceptance criteria

- "Template repository" checkbox enabled in GitHub Settings → General
- "Use this template" button visible on the public repo page
- A test clone via template produces a repo with a single commit and no `coffees/`, `grind-map.md` personal data

## Notes

This is a UI action, not a code change. Must be done after ticket 006 (history rewrite) so the template base is already clean. No lifecycle needed — just a GitHub settings change.
