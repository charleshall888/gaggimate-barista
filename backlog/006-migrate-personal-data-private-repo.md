---
id: "006"
title: "Migrate personal data to private repo and rewrite public history"
status: open
priority: high
type: feature
parent: "005"
tags: [multi-user-data-isolation]
research: research/multi-user-data-isolation/research.md
spec: research/multi-user-data-isolation/spec.md
created: 2026-03-04
updated: 2026-03-04
---

# Migrate personal data to private repo and rewrite public history

## What this delivers

- A new private GitHub repo (`gaggimate-barista-data`) containing all personal data with full history preserved
- The public repo's git history stripped of `coffees/`, `grind-map.md`, `user-setup.md` via `git filter-repo`
- A force-push of the cleaned public repo

## Spec references

- Must Have 1: Personal data absent from public repo working tree and history (DR-H)
- Must Have 2: Personal data lives in private git repo with full history

## Acceptance criteria

- `git log --all -- coffees/` in the public repo returns no commits
- Private repo exists on GitHub (private), `git log` shows full data history
- `coffees/`, `grind-map.md`, `user-setup.md` are no longer in the public repo working tree

## Sequence

1. Create `gaggimate-barista-data` repo on GitHub (private)
2. Copy `coffees/`, `grind-map.md`, `user-setup.md` into it; commit with message preserving context
3. Copy `mcp/data/` contents into `gaggimate-barista-data/mcp-data/`; commit
4. In the public repo: run `git filter-repo --path coffees/ --path grind-map.md --path user-setup.md --invert-paths`
5. Force-push the public repo

## Notes

This ticket must complete before any .gitignore changes (007) — gitignoring tracked files before removing them from history leaves the history dirty.
