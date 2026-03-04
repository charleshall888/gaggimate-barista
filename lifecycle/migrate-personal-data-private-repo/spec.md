> Source: research/multi-user-data-isolation/spec.md (bootstrapped from discovery)
# Specification: Multi-User Data Isolation

## Problem Statement

This repo currently contains personal extraction data (coffee research, tasting notes, grind settings, equipment config) mixed with generic framework files (knowledge base, MCP server, skills). Anyone cloning the repo gets Charlie's personal data embedded in both the working tree and git history, which is confusing for new users and means Charlie's dialing history is public. The repo should be restructured so the public repo contains only the shareable framework, while personal data lives in a separate private repo with full portability across machines and full git history.

---

## Requirements

### Must Have

1. **Personal data files are absent from the public repo working tree and history**: `coffees/`, `grind-map.md`, `user-setup.md`, and `mcp/data/` must not be tracked in `gaggimate-barista`, and historical commits containing personal data must be removed.
   - *Acceptance (new users via template)*: Clicking "Use this template" creates a new repo with a single commit. No personal data in working tree or history. ✓ Automatic via template mechanism.
   - *Acceptance (existing public repo)*: Running `git log --all -- coffees/` returns no commits. Personal data is not accessible via any SHA. Requires a history rewrite (see Decisions, DR-H).
   - *Acceptance (working tree)*: The gitignore covers `coffees/`, `grind-map.md` (as symlink), `user-setup.md` (as symlink).

2. **Personal data lives in a private git repo with full history**: All personal data (`coffees/`, `grind-map.md`, `user-setup.md`, `mcp-data/`) is tracked in a separate private GitHub repo (`gaggimate-barista-data`).
   - *Acceptance*: Private repo exists on GitHub. `git log` in the private repo shows complete history of data changes including pre-migration history.

3. **Existing skills work without modification**: `/new-coffee`, `/feedback`, `/gaggimate-profiles`, `/diagnose` write to the same paths they do today. No skill code changes required.
   - *Acceptance*: After running the setup script, `/new-coffee` creates a coffee directory at `coffees/{name}/` and the file physically lands in the private data repo. The agent reads `user-setup.md` and `grind-map.md` and edits them; changes land in the private repo. No skill `.md` files are modified.

4. **MCP server writes ratings to the private repo**: `mcp/data/ratings.json` and `mcp/data/profiles/` are stored inside the private data repo.
   - *Acceptance*: After setup, `manage_shot_notes` saves a rating; the file appears in `gaggimate-barista-data/mcp-data/`. `GAGGIMATE_STORAGE_PATH` is configured by the setup script in `mcp/.env`.

5. **Setup is reproducible via a single script**: A user on a new machine can run one script after cloning both repos and be fully configured. No manual env file editing required for the core data paths.
   - *Acceptance*: `bin/setup-data-repo.sh /path/to/gaggimate-barista-data` (a) creates symlinks for all agent-facing files, (b) writes `GAGGIMATE_STORAGE_PATH` to `mcp/.env`, (c) exits with an error and no partial changes if the private repo path doesn't exist or isn't a git repo. User still manually creates `.mcp.json` (machine-specific absolute paths) and configures device host in `.env`.

6. **Public repo becomes a GitHub Template**: Anyone can click "Use this template" and get a clean copy of the framework with no personal data and no shared commit history.
   - *Acceptance*: The "Template repository" checkbox is enabled in GitHub Settings. The "Use this template" button is visible on the public repo page.

### Should Have

7. **Agent commits and pushes the private data repo after writes**: After any skill step that writes personal data (`/new-coffee`, `/feedback`, `/gaggimate-profiles`), the agent commits and pushes the private data repo. No manual git work required.
   - *Acceptance*: After `/feedback` records a shot rating and updates `grind-map.md`, `git log` in the private data repo shows a new commit with the changes. The commit is pushed to `origin`. The agent does not ask for confirmation before committing (data writes are low-stakes and reversible via git).
   - *Note*: Skills need to know the private data repo path to run git commands there. The setup script writes the absolute path to a gitignored config file (`.data-repo-path`) at the public repo root. Skills read this file to locate the repo. If the file doesn't exist (new user without private repo), skills skip the commit step silently.

8. **Example files for user-setup and grind-map**: The public repo includes `user-setup.example.md` and `grind-map.example.md` as valid, filled-out examples (not blank stubs). New users copy and customize them. Operational filenames (`user-setup.md`, `grind-map.md`) are gitignored so they never accidentally enter the public repo.
   - *Acceptance*: `user-setup.example.md` exists in public repo with all sections populated with illustrative (not Charlie's real) values. `grind-map.example.md` has the table header plus one illustrative row. Both operational filenames appear in `.gitignore`.
   - *Note*: New users without a private repo: copy `.example.md` → `user-setup.md` to get started. With private repo: setup script creates symlinks; `.example.md` files remain as reference.

9. **Setup script creates symlinks, configures MCP storage, and writes data repo path**: `bin/setup-data-repo.sh` is idempotent — re-running on an already-set-up machine actively replaces existing symlinks with freshly computed absolute paths. This ensures correctness when the repos move.
   - *Acceptance*: The script takes the private repo path as its first argument. It creates absolute-path symlinks for: `coffees` → `{private-repo}/coffees`, `grind-map.md` → `{private-repo}/grind-map.md`, `user-setup.md` → `{private-repo}/user-setup.md`. It writes/overwrites `GAGGIMATE_STORAGE_PATH={private-repo}/mcp-data` in `mcp/.env`. It writes the absolute private repo path to `.data-repo-path` at the public repo root (gitignored — used by skills for auto-commit). It does NOT create a symlink for `mcp/data/`. Re-running on any machine produces correct link targets.

9. **`.env.example` documents the storage path variable**: `mcp/.env.example` includes `GAGGIMATE_STORAGE_PATH` with a comment explaining that the setup script configures it automatically.
   - *Acceptance*: The variable and comment appear in `.env.example`. Manual override is documented for advanced users.

### Could Have

10. **CLAUDE.md documents the data separation architecture**: A brief note tells the agent (and human readers) where data files live and what to do if the private repo isn't configured.
    - *Acceptance*: CLAUDE.md includes a "Data Architecture" note stating that `coffees/`, `grind-map.md`, `user-setup.md` are expected to be symlinks to a private data repo, and that the MCP storage path should point there too. Instructs the agent to warn the user if `user-setup.md` appears to be an unconfigured template.

### Won't Do

- **CI/CD or cron-based sync**: No automated pipelines. Commits and pushes are agent-driven, triggered after data-writing skill steps — not by external schedulers.
- **Community-contributed coffee database**: The `coffees/` directory becomes fully personal. Sharing coffee research is a separate future concern.
- **Monorepo with `users/` subdirectory**: Each user gets their own independent repo, not a subdirectory in a shared one.
- **Branch-based personal data**: Ruled out — requires ongoing git discipline and branch-context awareness that breaks the agent's relative-path assumptions.
- **Symlink for `mcp/data/`**: Only one mechanism should control MCP data path. The env var (`GAGGIMATE_STORAGE_PATH`) is the authoritative mechanism. Creating a symlink for `mcp/data/` at the same time would create conflicting configuration with unclear precedence.

---

## Edge Cases

- **Private repo path doesn't exist**: Setup script must validate the argument is a valid git repo before creating any symlinks or writing `.env`. Exit with a clear error message listing what it expected to find.
- **Repos cloned to different absolute paths on different machines**: Setup script uses `realpath` or equivalent to compute absolute paths at run time. Re-running on a new machine produces correct paths. Old symlinks are deleted before new ones are created (not `ln -s`, use `ln -sf` or remove-then-create).
- **New user without a private repo**: Operational `user-setup.md` and `grind-map.md` don't exist. Agent reads missing files and encounters an error, OR user manually copies from `.example.md`. README must clearly state: "Copy `user-setup.example.md` to `user-setup.md` to get started without a private repo. Note: changes will not persist across machines until you configure the private repo."
- **Pre-setup data written to local `user-setup.md`**: If a new user copies `.example.md`, customizes it, then later sets up the private repo — the setup script replaces `user-setup.md` with a symlink. Their customizations are lost. The script must warn: "user-setup.md will be replaced by a symlink. Back up your customizations first."
- **Git tracks symlinks, not symlink targets**: The `.gitignore` entries for `user-setup.md`, `grind-map.md`, and `coffees/` must cover the symlink names. Symlinks are gitignored so they never enter the public repo. Verify with `git check-ignore -v user-setup.md`.
- **`GAGGIMATE_STORAGE_PATH` not configured**: If the MCP server starts without this env var, `storage_path` defaults to `./data` (relative to `mcp/`). This causes ratings to be written to `mcp/data/` inside the public repo — which is gitignored — silently losing data. The setup script is the only mechanism that prevents this; its usage must be prominent in the README.
- **Existing personal data migration**: `coffees/`, `grind-map.md`, `user-setup.md` are currently tracked in git. Migration sequence: (1) copy files to private repo, (2) commit to private repo, (3) `git rm --cached` in public repo, (4) add to `.gitignore`, (5) create symlinks via setup script. If steps are done out of order, data can be in an inconsistent state — document the exact sequence.

---

## Technical Constraints

- **Symlinks must use absolute paths**: Relative symlinks break when `pwd` changes. The setup script must resolve absolute paths using `realpath` (macOS/Linux) at setup time.
- **`pydantic-settings` reads `GAGGIMATE_STORAGE_PATH` from `mcp/.env`**: The MCP server launches with `--directory /path/to/mcp`, so it reads `.env` from `mcp/.env`. The setup script must write to `mcp/.env`, not the project root.
- **`.gitignore` must cover symlink names, not just directory names**: Adding `coffees/` to `.gitignore` ignores a directory. A symlink named `coffees` (no trailing slash) may not be matched by `coffees/`. Must use `coffees` (without slash) or verify behavior. Similarly for `grind-map.md` and `user-setup.md`.
- **`mcp/data/` is already in `.gitignore`**: No change needed here. But the path is only gitignored — it still physically exists inside the public repo's `mcp/` subdirectory if not configured. The env var redirects where the MCP server writes; it does not prevent accidental default-path writes if the env var is missing.
- **Skills write relative paths from project root**: `coffees/{name}/README.md`, `grind-map.md`, `user-setup.md` are resolved from the CWD where `claude` is launched (the project root). Symlinks at those paths are resolved by the OS transparently. Skills require minimal changes — only to read `.data-repo-path` and run a commit+push after writing.
- **`.data-repo-path` is a gitignored plain-text file**: Contains the absolute path to the private data repo. Written by the setup script. Read by skills at the end of any data-writing workflow to locate the repo for `git add`, `git commit`, `git push`. If absent, skills skip the commit step.
- **History rewrite requires force-push**: Rewriting the public repo's history to remove personal data requires `git push --force`. This is destructive for any users who have already cloned. Since this happens during the initial conversion, force-push is acceptable but must be coordinated.

---

## Decisions

- **DR-1**: Gitignore `coffees/` entirely — the whole directory becomes personal. No file splitting needed.
- **DR-2**: Gitignore operational filenames `grind-map.md` and `user-setup.md`. Provide `.example.md` variants (not blank stubs — filled with illustrative data) as committed reference files.
- **DR-3**: Enable GitHub Template repository setting for the public repo.
- **DR-4**: Personal data lives in a private GitHub repo (`gaggimate-barista-data`). Agent-facing files linked via symlinks; MCP data configured via `GAGGIMATE_STORAGE_PATH`.
- **DR-5**: `mcp/data/ratings.json` is included in the private repo via `GAGGIMATE_STORAGE_PATH` set by the setup script. No symlink for `mcp/data/`.
- **DR-H (History rewrite)**: The public repo's history must be rewritten to remove personal data before converting to a template. Use `git filter-repo --path coffees/ --path grind-map.md --path user-setup.md --invert-paths` to strip the paths from history, then force-push. This is a one-time operation performed as part of the migration. Old SHAs become inaccessible.

---

## Open Decisions

- **Private repo name**: `gaggimate-barista-data` is the working name. Low stakes — user decides at creation time. The setup script takes the path as an argument, so the name doesn't affect the implementation.
- **Private repo structure**: Proposed layout: `coffees/`, `grind-map.md`, `user-setup.md`, `mcp-data/` (for ratings and profile drafts). To be confirmed during planning when the repo is created.
