# Plan: migrate-personal-data-private-repo

## Overview

Build all public-repo infrastructure (gitignore additions, example files, setup script, documentation updates) in committed, verifiable state before touching the private repo or running any destructive git operations. The destructive step — `git filter-repo` + force-push — comes last, after private repo creation, data migration, and symlink wiring are all confirmed working. This sequence means that if anything goes wrong during the rewrite, the data is already safely in the private repo and the infrastructure is committed.

---

## Tasks

### Task 1: Add personal data paths to `.gitignore`

- **Files**: `/Users/charlie.hall/Workspaces/gaggimate-barista/.gitignore`
- **What**: Append four entries — `coffees` (no trailing slash, to match a symlink), `grind-map.md`, `user-setup.md`, and `.data-repo-path` — so personal data can never accidentally re-enter the public repo.
- **Depends on**: none
- **Context**:
  - Current `.gitignore` at `/Users/charlie.hall/Workspaces/gaggimate-barista/.gitignore` already has `mcp/data/` and `.env`. Follow the same style.
  - Spec constraint: `coffees` without trailing slash covers the symlink; `coffees/` with slash may not match a symlink. Verify with `git check-ignore -v coffees` after adding.
  - `.data-repo-path` is a gitignored plain-text file at project root written by the setup script containing the absolute path to the private repo (used by skills for auto-commit).
  - Note: adding these entries to `.gitignore` does NOT untrack the currently-tracked files — that happens in Task 9 via `git rm --cached`.
- **Verification**: `git check-ignore -v coffees grind-map.md user-setup.md .data-repo-path` returns all four paths matched. `git status` does not show staged changes to the personal files (they're still tracked, just gitignored for new additions). Run `git add . --dry-run` from project root and confirm no `coffees/` contents appear in the output — this verifies that the `coffees` gitignore entry prevents symlink traversal.
- **Status**: [x] complete

---

### Task 2: Add `user-setup.example.md` and `grind-map.example.md`

- **Files**:
  - `/Users/charlie.hall/Workspaces/gaggimate-barista/user-setup.example.md` (new)
  - `/Users/charlie.hall/Workspaces/gaggimate-barista/grind-map.example.md` (new)
- **What**: Commit filled-out example files — not blank stubs — using illustrative (not Charlie's real) values. These serve two purposes: (1) reference documentation for new users who don't have a private repo yet, (2) a copy-to-start onboarding path.
- **Depends on**: [1] (gitignore must be in place so the operational filenames are not accidentally committed)
- **Context**:
  - Source structure: `/Users/charlie.hall/Workspaces/gaggimate-barista/user-setup.md` — use as structural template, replace values with illustrative data (e.g., machine: "Gaggia Classic Pro + Gaggimate Standard", grinder: "Baratza Encore ESP", basket: "IMS 18g"). All sections must be present: Equipment table, Workflow, Preferences, Active Coffee, Bluetooth Scale, Notes. Active Coffee section should show the "No active coffee" placeholder state.
  - Source structure: `/Users/charlie.hall/Workspaces/gaggimate-barista/grind-map.md` — copy header, replace rows with one illustrative entry (e.g., "Example Roaster Ethiopia Yirgacheffe | Light | Washed | Ethiopia | 21 | 13C | Bloom Slide | 1:2.5 | 94°C | 5 | Jan 15").
  - The CLAUDE.md "if `user-setup.md` appears to be an unconfigured template, warn the user" instruction (Task 5) depends on these examples existing as a recognizable signal.
- **Verification**: Both files committed and visible in `git status`. `git check-ignore -v user-setup.md grind-map.md` still shows the operational filenames gitignored (the `.example.md` variants are tracked, the bare filenames are not). Content contains no references to Charlie's personal equipment, coffees, or grind history.
- **Status**: [x] complete

---

### Task 3: Update `mcp/.env.example` to document `GAGGIMATE_STORAGE_PATH`

- **Files**: `/Users/charlie.hall/Workspaces/gaggimate-barista/mcp/.env.example`
- **What**: Add `GAGGIMATE_STORAGE_PATH` with an inline comment explaining that `bin/setup-data-repo.sh` configures it automatically, the default behavior if unset, and that advanced users can override manually.
- **Depends on**: none (file already exists at `mcp/.env.example`)
- **Context**:
  - `GaggimateConfig` at `/Users/charlie.hall/Workspaces/gaggimate-barista/mcp/src/gaggimate_mcp/config.py` uses `env_prefix="GAGGIMATE_"` and field name `storage_path`, resolving to env var `GAGGIMATE_STORAGE_PATH`. Default: `Path("./data")` relative to the `mcp/` working dir.
  - The MCP server runs with `--directory /path/to/mcp`, so pydantic-settings reads `mcp/.env`. The setup script writes to `mcp/.env`, not the project root `.env`.
  - Follow the existing format in `.env.example`. The actual `mcp/.env` (gitignored) is not modified by this task.
- **Verification**: `GAGGIMATE_STORAGE_PATH` appears in `mcp/.env.example` with explanatory comment. File is committed. `git check-ignore -v mcp/.env.example` returns no match (not gitignored).
- **Status**: [x] complete

---

### Task 4: Write `bin/setup-data-repo.sh`

- **Files**: `/Users/charlie.hall/Workspaces/gaggimate-barista/bin/setup-data-repo.sh` (new directory + file)
- **What**: Write the idempotent setup script that wires a private data repo into the public repo on any machine. Creates absolute-path symlinks, configures MCP storage path in `mcp/.env`, and writes `.data-repo-path`.
- **Depends on**: [1, 2, 3]
- **Context**:
  - Script signature: `bin/setup-data-repo.sh /absolute/path/to/gaggimate-barista-data`
  - Validation: check argument exists, is a directory, contains a `.git/` directory. Exit non-zero with a clear message if not.
  - Safety checks before creating symlinks:
    - If `coffees` is a real directory (not a symlink): `[ -d coffees ] && [ ! -L coffees ]` → exit 1 with message "coffees/ is a real directory — run `git rm -r --cached coffees/` and manually move it to the private repo before running this script."
    - If `user-setup.md` is a regular file (not a symlink): `[ -f user-setup.md ] && [ ! -L user-setup.md ]` → print warning "user-setup.md will be replaced by a symlink — back up your customizations first." Print warning but continue.
    - Same check for `grind-map.md` as a regular file.
  - Absolute path resolution: use `$(cd "$1" && pwd)` as the primary method — works on stock macOS without Homebrew. Do NOT use `realpath` as primary (requires `brew install coreutils`). Fallback: `python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))'`.
  - Symlinks:
    - `coffees` → `{private_repo}/coffees`
    - `grind-map.md` → `{private_repo}/grind-map.md`
    - `user-setup.md` → `{private_repo}/user-setup.md`
  - Use `rm -f` then `ln -s` (not `ln -sf`) so re-runs replace stale symlinks correctly on macOS. The directory check above ensures `rm -f` is only called when the target is a symlink or file, never a real directory.
  - `mcp/.env` handling: upsert `GAGGIMATE_STORAGE_PATH={private_repo}/mcp-data` — strip any existing line with `grep -v` before appending, so re-runs don't duplicate the line. Preserve all other `.env` lines.
  - Write absolute private repo path to `.data-repo-path` at project root (single line, no trailing newline).
  - Script does NOT create a symlink for `mcp/data/` — the env var is the sole mechanism (spec DR-5).
  - Script must be executable (`chmod +x`).
- **Verification**: `bash bin/setup-data-repo.sh /nonexistent/path` exits non-zero with a clear error. `bash bin/setup-data-repo.sh /path/to/gaggimate-barista-data` creates three symlinks, writes `mcp/.env`, writes `.data-repo-path`. `ls -la coffees` shows a symlink. `cat .data-repo-path` returns the correct absolute path. `grep GAGGIMATE_STORAGE_PATH mcp/.env` returns the correct value. Re-running produces no errors or duplicates.
- **Status**: [x] complete

---

### Task 5: Update `CLAUDE.md` with data architecture note

- **Files**: `/Users/charlie.hall/Workspaces/gaggimate-barista/CLAUDE.md`
- **What**: Add a "Data Architecture" section documenting: (1) `coffees/`, `grind-map.md`, `user-setup.md` are expected to be symlinks to a private data repo; (2) `GAGGIMATE_STORAGE_PATH` in `mcp/.env` points to `{private-repo}/mcp-data/`; (3) if `user-setup.md` reads like an unconfigured example, warn and suggest running setup script or copying from `.example.md`. Also add auto-commit policy: after any data-writing skill step, read `.data-repo-path` and commit+push to private repo; if absent, skip silently.
- **Depends on**: [1, 2, 4]
- **Context**:
  - Add after the "Dynamic Data Files" section in `/Users/charlie.hall/Workspaces/gaggimate-barista/CLAUDE.md`. The section should be ≤15 lines — a pointer/policy, not a duplicate of the skills workflow.
  - Skills write to `coffees/`, `grind-map.md`, `user-setup.md` via relative paths from project root — the OS resolves symlinks transparently. No skill writes need to change.
  - Auto-commit: the agent reads `.data-repo-path`, then runs `git add`, `git commit`, `git push` as separate Bash tool calls targeting the private repo (not the public repo). Never chain with `&&`. Never use `git -C` (per global CLAUDE.md). Use `--git-dir={private_repo}/.git --work-tree={private_repo}` pattern or `cd` to the private repo directory first.
- **Verification**: CLAUDE.md includes "Data Architecture" section visible under Dynamic Data Files. Running the agent and asking it to explain its data storage gives an accurate answer referencing symlinks and the private repo.
- **Status**: [x] complete

---

### Task 6: Update `README.md` for the two-repo model

- **Files**: `/Users/charlie.hall/Workspaces/gaggimate-barista/README.md`
- **What**: Update setup instructions with two onboarding paths (with/without private repo) and update the Project Structure section to show `coffees/`, `grind-map.md`, `user-setup.md` as symlinks. Add upstream sync instructions for template users.
- **Depends on**: [2, 4]
- **Context**:
  - Current README has a Setup section (steps 1–6) and a Project Structure section. Insert a "Personal Data Setup" step after step 1 (Clone) presenting both paths:
    - Without private repo: `cp user-setup.example.md user-setup.md`, fill in equipment. Data does not persist across machines.
    - With private repo: `bin/setup-data-repo.sh /path/to/gaggimate-barista-data`
  - Project Structure section: update `user-setup.md`, `grind-map.md`, `coffees/` to show `(symlink → private repo)`. Add `user-setup.example.md` and `grind-map.example.md` as new entries.
  - Add upstream sync note: `git remote add upstream {url}` then `git fetch upstream && git merge upstream/main`.
  - Update "forking" language: template repo users don't fork — they use "Use this template".
- **Verification**: README has a clear two-track onboarding path. `bin/setup-data-repo.sh` command appears verbatim. Project structure diagram shows symlink notation for personal data files.
- **Status**: [x] complete

---

### Task 7: Update data-writing skills for auto-commit to private repo

- **Files**:
  - `/Users/charlie.hall/Workspaces/gaggimate-barista/.claude/skills/feedback/SKILL.md`
  - `/Users/charlie.hall/Workspaces/gaggimate-barista/.claude/skills/new-coffee/SKILL.md`
  - `/Users/charlie.hall/Workspaces/gaggimate-barista/.claude/skills/gaggimate-profiles/SKILL.md`
- **What**: Add a terminal "COMMIT to private data repo" step to each data-writing skill. Reads `.data-repo-path`; if present, commits and pushes to the private repo; if absent, skips silently.
- **Depends on**: [4, 5] (setup script must write `.data-repo-path`; CLAUDE.md must document the pattern)
- **Context**:
  - In `/feedback` SKILL.md: add after Step 4 (RECORD section, after tasting notes and grind map are written). Commit message: `"feedback: shot {shot_id} — {rating}★ {balance}"`.
  - In `/new-coffee` SKILL.md: add after Step 8 (Set Active Coffee). Commit message: `"new-coffee: add {coffee-name}"`.
  - In `/gaggimate-profiles` SKILL.md: add after the save-to-coffees step. Commit message: `"gaggimate-profiles: {profile-name} for {coffee-name}"`.
  - Git commands must NOT chain with `&&`. Must NOT use `git -C` (per global CLAUDE.md). Run as separate Bash tool calls. Pattern: read `.data-repo-path` → `git --git-dir={private_repo}/.git --work-tree={private_repo} add -A` → `git --git-dir={private_repo}/.git --work-tree={private_repo} commit -m "..."` → `git --git-dir={private_repo}/.git --work-tree={private_repo} push`.
  - If `.data-repo-path` is absent (new user without private repo): skip silently, no error shown to user.
  - If `.data-repo-path` is present but `git push` fails (e.g., no credentials configured): do NOT skip silently. Inform the user: "Private repo push failed — changes saved locally. Run `git push` manually in `{private_repo_path}` when credentials are available." This distinguishes "not configured" (silent skip) from "configured but failing" (inform user).
- **Verification**: After `/feedback` records a shot, `git log` in the private repo shows a new commit with the shot ID. After `/new-coffee`, private repo has new coffee directory committed. Skills complete without error when `.data-repo-path` is absent. Skills display the push-failure message when `.data-repo-path` exists but push fails.
- **Status**: [x] complete

---

### Task 8: Create private GitHub repo and migrate data

- **Files**: In the private repo (outside public repo working tree):
  - `coffees/` (all 7 subdirectories and files)
  - `grind-map.md`
  - `user-setup.md`
  - `mcp-data/ratings.json` (migrated from `mcp/data/ratings.json`)
  - `mcp-data/profiles/` (migrated from `mcp/data/profiles/`)
- **What**: Create the private GitHub repo `gaggimate-barista-data`, copy all personal data into it with the correct directory structure, commit with a migration message, push, and run the setup script to wire up symlinks.
- **Depends on**: [1, 2, 3, 4, 5, 6] (all public repo infrastructure committed and verified before touching data)
- **Context**:
  - Create via: `gh repo create gaggimate-barista-data --private` or via GitHub UI.
  - Private repo structure: `coffees/`, `grind-map.md`, `user-setup.md`, `mcp-data/ratings.json`, `mcp-data/profiles/` (note: `mcp-data/` not `mcp/data/` — renamed for clarity).
  - Source personal data in current public repo: `coffees/` (7 subdirs), `grind-map.md`, `user-setup.md`, `mcp/data/ratings.json`, `mcp/data/profiles/`.
  - After pushing private repo: run `bin/setup-data-repo.sh /path/to/gaggimate-barista-data`. This creates symlinks, writes `mcp/.env`, writes `.data-repo-path`.
  - **Hard gate before Task 9**: Verify all three symlinks are in place and resolving correctly. Do not proceed to Task 9 if any symlink check fails — the public repo's tracked files are still intact as a fallback until Task 9 runs.
- **Verification**: Private repo exists on GitHub (private setting confirmed). `git log` shows initial commit with all data. Symlinks in public repo: `ls -la coffees grind-map.md user-setup.md` shows all three as symlinks pointing into private repo. `cat user-setup.md` shows Charlie's equipment (served through symlink). `cat coffees/choco-coffee-hacienda-la-papaya-typica-anaerobic/README.md` works. `readlink coffees` returns the absolute private repo path. All three symlink checks must pass before proceeding to Task 9.
- **Status**: [x] complete

---

### Task 9: Untrack personal data files from public repo index

- **Files**: Public repo git index (no working tree edits — index-only operation)
- **What**: Run `git rm -r --cached` to remove `coffees/`, `grind-map.md`, and `user-setup.md` from git's tracking index. After this commit, these paths are gitignored and untracked in the public repo. The symlinks remain in the working tree (gitignored, not committed).
- **Depends on**: [8] (private repo must exist and symlinks must be verified before removing from public repo)
- **Context**:
  - Commands (run as separate Bash tool calls, do not chain):
    - `git rm -r --cached coffees/`
    - `git rm --cached grind-map.md`
    - `git rm --cached user-setup.md`
  - The working tree entries are now symlinks (from Task 8 setup script run). `git rm --cached` removes the tracking entry; the symlinks remain on disk.
  - After this step: `git ls-files coffees grind-map.md user-setup.md` returns nothing. `git status` shows the removals staged. Commit the result.
  - Note: filter-repo in Task 10 will strip the history of these paths anyway. This Task 9 commit produces a clean state in the working tree before the rewrite, making the post-rewrite state predictable.
- **Verification**: `git ls-files coffees/ grind-map.md user-setup.md` returns no output. `git status` shows staged deletions ready to commit. After commit: `ls -la coffees` still shows symlink (working tree intact). `cat grind-map.md` still shows grind history (served via symlink).
- **Status**: [x] complete

---

### Task 10: Rewrite public repo history and force-push; enable GitHub Template

- **Files**: Public repo git history (destructive, no working tree files changed). GitHub repo settings (UI action).
- **What**: Run `git filter-repo` to strip all historical commits touching `coffees/`, `grind-map.md`, and `user-setup.md` from the public repo's history, then force-push to GitHub. Enable the GitHub Template setting.
- **Depends on**: [9] (working tree must be clean; all data safely in private repo)
- **Context**:
  - Prerequisite: `git filter-repo` must be installed (`pip install git-filter-repo` or `brew install git-filter-repo`).
  - **Before running filter-repo**: create a recovery tag on the current HEAD: `git tag pre-filter-repo-backup`. This tag is local only and does not affect the public repo, but gives a SHA anchor to recover from if the rewrite produces unexpected results. After verifying the rewrite is correct, this tag can be deleted.
  - Command: `git filter-repo --path coffees/ --path grind-map.md --path user-setup.md --invert-paths`
  - How filter-repo handles infrastructure commits (Tasks 1–9): filter-repo removes entire commits only if they exclusively touch the listed paths. Task 1 commit touches `.gitignore` (not listed) → survives. Task 2 creates `.example.md` files (not listed) → survives. Task 4 creates `bin/setup-data-repo.sh` (not listed) → survives. Task 9 commit (`git rm --cached`) touches only the listed paths → this commit is stripped, which is correct (history reads as if they were never tracked).
  - After filter-repo: `origin` remote is removed for safety. **Explicit step**: check `git remote -v` — if `origin` is missing, run `git remote add origin https://github.com/{owner}/gaggimate-barista.git`. Verify with `git remote -v` before proceeding.
  - Force-push: `git push origin main --force`.
  - Enable GitHub Template: `gh api -X PATCH repos/{owner}/gaggimate-barista -f is_template=true` or via GitHub Settings UI.
- **Verification**: `git log --all -- coffees/` returns no output. `git log --all -- grind-map.md` returns no output. `git log --all -- user-setup.md` returns no output. Infrastructure commits (`.gitignore`, setup script, example files) are present in the rewritten history. Working tree symlinks still resolve correctly. `gh api repos/{owner}/gaggimate-barista --jq '.is_template'` returns `true`.
- **Status**: [x] skipped — data not sensitive, history rewrite deferred

---

## Verification Strategy

End-to-end validation after Task 10:

1. **History clean**: `git log --all -- coffees/ grind-map.md user-setup.md` returns no commits.
2. **Symlinks work**: `ls -la coffees user-setup.md grind-map.md` shows symlinks pointing to absolute paths inside the private repo. `cat grind-map.md` shows full grind history.
3. **MCP storage**: Start MCP server, call `manage_shot_notes` to save a test rating. Verify rating appears in `{private_repo}/mcp-data/ratings.json`, not in `mcp/data/ratings.json`.
4. **Skills work without modification**: Launch `claude`, run `/feedback` on a test shot. Verify: (a) tasting notes appended to correct coffee README via symlink, (b) grind-map updated via symlink, (c) private repo has a new commit.
5. **New user simulation**: Clone the public repo to a temp directory. Verify: `coffees/`, `grind-map.md`, `user-setup.md` are NOT present. `user-setup.example.md` and `grind-map.example.md` ARE present. Confirm `git log --all -- coffees/` returns empty.
6. **Setup script idempotency**: Run `bin/setup-data-repo.sh /path/to/private-repo` twice. No errors on second run. Symlinks correct.
7. **GitHub Template**: `gh api repos/{owner}/gaggimate-barista --jq '.is_template'` returns `true`. "Use this template" button visible on repo page.
