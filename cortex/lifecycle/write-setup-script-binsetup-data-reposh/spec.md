> Source: research/multi-user-data-isolation/spec.md (bootstrapped from discovery)

# Specification: Write setup script (bin/setup-data-repo.sh)

## Problem Statement

New users cloning the repo need a single command to wire the public and private repos together. The script creates symlinks for agent-facing personal data files, configures `GAGGIMATE_STORAGE_PATH` in `mcp/.env`, and writes the private repo path to `.data-repo-path` for use by agent skills. Without it, every machine switch requires manual env file editing and symlink creation.

---

## Requirements

### Must Have

1. `bin/setup-data-repo.sh /path/to/gaggimate-barista-data` runs successfully on a fresh clone
2. Script validates the argument is a git repo; exits with clear error if not
3. Creates absolute-path symlinks: `coffees` → `{private-repo}/coffees`, `grind-map.md` → `{private-repo}/grind-map.md`, `user-setup.md` → `{private-repo}/user-setup.md`
4. Writes/updates `GAGGIMATE_STORAGE_PATH={private-repo}/mcp-data` in `mcp/.env` (creates file if absent, updates line if present)
5. Writes absolute private repo path to `.data-repo-path` at project root
6. Does NOT create a symlink for `mcp/data/`
7. Idempotent — re-running replaces existing symlinks with updated absolute paths
8. Warns before replacing an existing plain-file `user-setup.md` (data loss prevention)
9. Script is executable (`chmod +x`)

### Should Have

10. Creates `{private-repo}/mcp-data/` and `{private-repo}/coffees/` directories if they don't exist
11. Uses `realpath` for absolute path resolution; falls back to `$(cd ... && pwd)` if not available
12. Prints clear summary of what was created/updated on success

### Edge Cases Handled

- Private repo path argument missing or doesn't exist → exit with clear error
- Argument exists but is not a git repo → exit with clear error
- `user-setup.md` is a plain file (not symlink) → warn, require user to back up before proceeding (or skip with message)
- Existing symlinks → `ln -sf` (force replace) without prompt
- `mcp/.env` doesn't exist → create it with the `GAGGIMATE_STORAGE_PATH` line
- `mcp/.env` exists but lacks the key → append the line
- `mcp/.env` exists and has the key → update the value in-place

---

## Technical Constraints

- Symlinks must use absolute paths (relative paths break when `pwd` changes)
- `.gitignore` must cover symlink names (coffees, grind-map.md, user-setup.md) — verify separately
- `mcp/.env` is read by pydantic-settings when MCP server starts with `--directory /path/to/mcp`
- `.data-repo-path` is a gitignored plain-text file; skills read it to locate the repo for auto-commit
- Script runs in bash (not zsh/sh-only features)

---

## Out of Scope

- Migrating existing personal data to private repo (manual migration step, documented separately)
- Configuring `.mcp.json` (machine-specific, must be done manually per machine)
- Configuring device host/credentials in `.env` (separate from data path config)
