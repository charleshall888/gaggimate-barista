# Plan: write-setup-script-binsetup-data-reposh

## Overview

`bin/setup-data-repo.sh` was implemented as part of the `migrate-personal-data-private-repo` lifecycle. All acceptance criteria from the spec are met. This plan documents the completed work and the verification steps used to confirm it.

## Tasks

### Task 1: Write bin/setup-data-repo.sh
- **Files**: `bin/setup-data-repo.sh`
- **What**: Shell script that validates the private repo argument, creates absolute-path symlinks for coffees/grind-map.md/user-setup.md, writes GAGGIMATE_STORAGE_PATH to mcp/.env, writes .data-repo-path, and creates mcp-data/ if absent.
- **Depends on**: none
- **Context**: Script uses `set -euo pipefail`, `$(cd ... && pwd)` for realpath, `ln -s` with prior `rm -f`, `grep -v` + append pattern for idempotent env line update
- **Verification**: `ls -la bin/setup-data-repo.sh` shows `-rwxr-xr-x`. Inspect script for all required behaviors. Run a dry validation: `bash -n bin/setup-data-repo.sh` (no errors).
- **Status**: [x] completed

### Task 2: Verify .gitignore coverage
- **Files**: `.gitignore`
- **What**: Confirm coffees, grind-map.md, user-setup.md, and .data-repo-path are all gitignored so symlinks can never accidentally enter the public repo.
- **Depends on**: [1]
- **Context**: Use `git check-ignore -v <path>` for each name. All four must match `.gitignore` entries.
- **Verification**: `git check-ignore -v coffees grind-map.md user-setup.md .data-repo-path` — all four lines return hits from `.gitignore`.
- **Status**: [x] completed

### Task 3: Verify acceptance criteria against spec
- **Files**: none (read-only check)
- **What**: Confirm each Must Have acceptance criterion from the spec is satisfied by the existing script.
- **Depends on**: [1, 2]
- **Context**: Spec acceptance criteria: (1) runs on fresh clone, (2) validates git repo, (3) absolute-path symlinks, (4) mcp/.env GAGGIMATE_STORAGE_PATH, (5) .data-repo-path written, (6) no mcp/data/ symlink, (7) idempotent, (8) warns before replacing plain-file user-setup.md, (9) executable.
- **Verification**: All 9 criteria confirmed by reading the script. See lifecycle events log.
- **Status**: [x] completed

## Verification Strategy

Run `bin/setup-data-repo.sh` against the actual private data repo path and confirm:
1. Symlinks are created at coffees, grind-map.md, user-setup.md pointing into the private repo
2. `mcp/.env` contains `GAGGIMATE_STORAGE_PATH={private-repo}/mcp-data`
3. `.data-repo-path` contains the absolute private repo path
4. Re-running produces no errors and updates symlinks correctly (idempotency check)
