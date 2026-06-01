---
id: "007"
title: "Update .gitignore and add .example.md templates"
status: complete
priority: high
type: feature
parent: "005"
blocked-by: ["006"]
tags: [multi-user-data-isolation]
research: research/multi-user-data-isolation/research.md
spec: research/multi-user-data-isolation/spec.md
created: 2026-03-04
updated: 2026-03-04
---

# Update .gitignore and add .example.md templates

## What this delivers

- `.gitignore` entries for `coffees`, `grind-map.md`, `user-setup.md`, `.data-repo-path`
- `user-setup.example.md` with all sections populated with illustrative (non-personal) values
- `grind-map.example.md` with table header and one illustrative data row

## Spec references

- Must Have 1: gitignore covers personal file paths
- Should Have 8 (formerly 7): example files for new users

## Acceptance criteria

- `git check-ignore -v coffees` returns a match
- `git check-ignore -v grind-map.md` returns a match
- `git check-ignore -v user-setup.md` returns a match
- `git check-ignore -v .data-repo-path` returns a match
- `user-setup.example.md` committed to public repo with illustrative equipment/preferences (no real personal data)
- `grind-map.example.md` committed to public repo with header + one illustrative row

## Notes

- Gitignore entry for `coffees` must use the bare name (no trailing slash) to match the symlink that the setup script will create
- `user-setup.md` and `grind-map.md` are removed from tracking via `git rm --cached` after history rewrite (ticket 006) ensures they're clean
