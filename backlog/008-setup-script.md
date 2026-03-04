---
id: "008"
title: "Write setup script (bin/setup-data-repo.sh)"
status: complete
priority: high
type: feature
parent: "005"
blocked-by: []
tags: [multi-user-data-isolation]
research: research/multi-user-data-isolation/research.md
spec: research/multi-user-data-isolation/spec.md
created: 2026-03-04
updated: 2026-03-04
lifecycle_phase: complete
---

# Write setup script (bin/setup-data-repo.sh)

## What this delivers

A single shell script that fully links the public and private repos on any machine. Running it is the only step required after cloning both repos (beyond machine-specific `.mcp.json`).

## Spec references

- Must Have 5: Setup is reproducible via a single script
- Should Have 9 (formerly 8): Script creates symlinks, configures MCP storage, writes data repo path

## Acceptance criteria

- `bin/setup-data-repo.sh /path/to/gaggimate-barista-data` runs successfully on a fresh clone
- Script validates the argument is a git repo; exits with clear error if not
- Creates absolute-path symlinks: `coffees`, `grind-map.md`, `user-setup.md`
- Writes `GAGGIMATE_STORAGE_PATH={private-repo}/mcp-data` to `mcp/.env` (creates or updates the line)
- Writes absolute private repo path to `.data-repo-path` at project root
- Does NOT create a symlink for `mcp/data/`
- Re-running on an already-set-up machine replaces existing symlinks with updated paths (idempotent)
- Warns before replacing an existing plain-file `user-setup.md` (pre-setup user data loss prevention)
- Script is executable (`chmod +x`)

## Notes

- Use `realpath` for absolute path resolution (available on macOS via `brew install coreutils` or use `$(cd ... && pwd)` as fallback)
- Private repo's `mcp-data/` and `coffees/` directories must exist before symlinks are created; script should create them if absent
