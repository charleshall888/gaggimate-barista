# Plan: update-gitignore-and-add-example-md-templates

## Overview

Three additive changes: gitignore entries for the four personal data paths, plus two committed example files (`user-setup.example.md` and `grind-map.example.md`) with illustrative non-personal content. No existing code modified. All tasks are independent.

## Status

**All tasks completed prior to lifecycle creation.** Work was delivered as part of the ticket 006 data migration. Acceptance criteria verified via `git check-ignore` and `git status`.

## Tasks

### Task 1: Add gitignore entries for personal data paths
- **Files**: `.gitignore`
- **What**: Add four entries — `coffees`, `grind-map.md`, `user-setup.md`, `.data-repo-path` — under a "Personal data" comment block. The `coffees` entry must use the bare name (no trailing slash) to match the symlink.
- **Depends on**: none
- **Context**: Existing `.gitignore` already covers `.mcp.json`, `.env`, `mcp/data/`. Append after the MCP runtime data block.
- **Verification**: `git check-ignore -v coffees grind-map.md user-setup.md .data-repo-path` returns four matches, all pointing to `.gitignore`.
- **Status**: [x] complete

### Task 2: Create user-setup.example.md
- **Files**: `user-setup.example.md`
- **What**: A fully-populated illustrative user setup file using fictional (non-Charlie) equipment: Gaggia Classic Pro + Gaggimate Standard, Baratza Encore ESP, 18g IMS basket, Felicita Arc scale. All sections present: Equipment, Workflow, Preferences, Active Coffee, Bluetooth Scale & Auto-Stop, Notes.
- **Depends on**: none
- **Context**: `user-setup.md` structure has these sections. Example must not contain Charlie's real grinder (Sette 270), basket (22g), or preferences (cortado/cappuccino). Active Coffee section should read "No active coffee."
- **Verification**: File committed to public repo. No real personal data. All sections populated.
- **Status**: [x] complete

### Task 3: Create grind-map.example.md
- **Files**: `grind-map.example.md`
- **What**: A grind map with the standard table header plus one illustrative row (fictional roaster, Ethiopia Yirgacheffe washed, light, 13C, Bloom Slide, 1:2.5, 94°C, 5 stars).
- **Depends on**: none
- **Context**: Follow the column structure from `grind-map.md`: Coffee, Roast, Process, Origin, Days Off Roast, Grind, Profile, Ratio, Temp, Rating, Date.
- **Verification**: File committed. One data row present. Column headers match `grind-map.md`.
- **Status**: [x] complete

## Verification Strategy

Run `git check-ignore -v coffees grind-map.md user-setup.md .data-repo-path` — all four paths must match `.gitignore`. Confirm `user-setup.example.md` and `grind-map.example.md` are tracked (`git ls-files`), committed, and contain no real personal data.
