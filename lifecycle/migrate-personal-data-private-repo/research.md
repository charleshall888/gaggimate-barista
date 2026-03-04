> Source: research/multi-user-data-isolation/research.md (bootstrapped from discovery)
# Research: Multi-User Data Isolation

## Research Questions

1. **What constitutes user-specific vs. generic/shareable content in this repo today?**
   → **Answered.** See Codebase Analysis. Three tracked personal files + one already-gitignored data directory. The boundary runs through `coffees/*/README.md` (mixed content).

2. **What git strategies exist for isolating personal data from shared repo content?**
   → **Answered.** Five viable patterns: gitignore + templates, GitHub template repo, personal data branch, separate data repo, fork model. See Domain & Prior Art.

3. **How does the MCP server currently locate `mcp/data/` — is the path hardcoded or configurable?**
   → **Answered.** Fully configurable via `GAGGIMATE_STORAGE_PATH` env var. Default is `./data` (relative to `mcp/` working dir). Already covered in `.gitignore`.

4. **What would be lost or broken if a user cloned this repo fresh?**
   → **Answered.** Three issues: (1) Charlie's personal data in `coffees/`, `grind-map.md`, `user-setup.md` would be present and confusing. (2) `mcp/data/` is gitignored so it correctly starts empty. (3) `.mcp.json` and `.env` must be created per-machine (already gitignored — by design).

5. **How do similar projects handle the personal-vs-shared pattern?**
   → **Answered.** Dotfiles, Obsidian vaults, and HomeAssistant configs all converge on the same pattern: gitignore personal/secret data, provide template files for the rest, optional private sidecar repo for personal history.

6. **What are the trade-offs of the most viable approaches?**
   → **Answered.** See Feasibility Assessment and Decision Records.

7. **What does the onboarding experience look like for a new user cloning this repo?**
   → **Answered.** Currently poor — Charlie's personal data is in the clone. With recommended approach: clean clone, fill in `user-setup.md`, configure `.mcp.json` and `.env`, start pulling shots.

8. **How should machine-switch portability work — what state must survive a hardware change?**
   → **Answered.** Two portability gaps exist today. `mcp/data/ratings.json` (gitignored — not tracked) and the personal data files. See Decision Records for resolution.

---

## Codebase Analysis

### Current Data Boundary

| File/Directory | Tracked in git | Personal or Generic | Portability today |
|---|---|---|---|
| `user-setup.md` | Yes | Personal (equipment, preferences, active coffee pointer) | Tracked — survives machine switch |
| `grind-map.md` | Yes | Personal (dialing history, 5-star shots) | Tracked — survives machine switch |
| `coffees/*/README.md` | Yes | **Mixed**: bean research (generic) + tasting notes table (personal) | Tracked — survives |
| `coffees/*/*.json` | Yes | Semi-generic (profiles are coffee-specific, not machine-specific) | Tracked — survives |
| `mcp/data/ratings.json` | No (.gitignore) | Personal (shot ratings, notes) | **NOT portable** — lost on machine switch |
| `mcp/data/profiles/` | No (.gitignore) | Personal (AI-generated profile versions/drafts) | Not portable, low importance |
| `knowledge/` | Yes | Generic (espresso knowledge base) | N/A |
| `mcp/src/` | Yes | Generic (MCP server code) | N/A |
| `.claude/skills/` | Yes | Generic (skill definitions) | N/A |
| `.mcp.json` | No (.gitignore) | Machine-specific (absolute paths) | By design — must configure per machine |
| `.env` | No (.gitignore) | Machine-specific (host, credentials) | By design — must configure per machine |

### The Mixed-Content Problem in `coffees/`

Each `coffees/*/README.md` contains two conceptually different sections:

- **Generic bean research** — origin, variety, altitude, processing, expected flavor characteristics, starting parameters. This is community-useful content analogous to a coffee reference guide. If someone buys Choco Coffee Hacienda La Papaya, Charlie's research and starting parameters are genuinely useful to them.
- **Personal tasting notes table** — shot numbers, dates, grind settings, in/out ratios, stars, observations. This is a personal dialing journal. Another user starting from scratch would have none of these shots.

Profile JSON files in `coffees/*/` are semi-generic: they capture well-designed extraction curves for a specific coffee. A new user dialing the same bean benefits from them as starting points, even if they'll iterate.

### MCP Data Path Configuration

`GaggimateConfig` (pydantic-settings) resolves `storage_path` from:
1. `GAGGIMATE_STORAGE_PATH` environment variable (if set in `mcp/.env`)
2. Default: `Path("./data")` — relative to the MCP working directory (`mcp/`)

This means the data path is already designed to be externalized. A user can set `GAGGIMATE_STORAGE_PATH=/Users/alice/espresso-data` to put personal data anywhere, including a separate private repo. No code changes needed.

### Current `.gitignore` State

`mcp/data/` is already gitignored, which handles ratings and draft profiles correctly. The gap is the three tracked personal files: `coffees/`, `grind-map.md`, `user-setup.md`. The `.gitignore` already follows the right pattern for MCP data — the tracked personal files are the remaining inconsistency.

### Portability Gap: `mcp/data/ratings.json`

Shot ratings and tasting notes are stored in `mcp/data/ratings.json` — gitignored, so lost on machine switch. The agent's skills (`/feedback`) sync ratings to the Gaggimate device via WebSocket, but the device is a hardware appliance, not a backup system. If the user switches to a new machine and the device is reset or replaced, ratings are gone. This is a latent bug in the current design.

---

## Web & Documentation Research

### GitHub Template Repositories vs. Forks

A GitHub Template Repository (one checkbox in Settings) allows users to click "Use this template" and get a clean copy with no commit history. Key characteristics:

- **No shared history**: The new repo has a single initial commit. Charlie's personal data commits don't appear.
- **No upstream PR relationship**: Users can't easily submit PRs back upstream (unlike a fork). This matters less here since users don't contribute changes to the knowledge base.
- **Users own their repo**: Each user's repo is independent — they can make it private, track their own coffees, etc.
- **Manual upstream sync**: To get knowledge base updates, a user adds the original as a remote and merges. Doable but not automatic. Merge conflicts on personal data files are avoided if those files are gitignored.

### dotfiles / Personal Config Repos: Prior Art

The dotfiles community has iterated on this exact problem for decades. Dominant patterns:

1. **Gitignore + template files**: `.gitignore` lists all machine-specific or personal files. `.gitconfig.example`, `config.example` etc. are committed as starters. Users copy and fill in. The private data lives locally or in a separate private repo.

2. **`local.*` override pattern**: A committed `config.base` is loaded first; a gitignored `config.local` overrides it. The override file is never in the repo. Used by oh-my-zsh, vim, and many frameworks.

3. **Private sidecar repo**: Public framework repo (`dotfiles-public`) + private data repo (`dotfiles-private`). The private repo contains secrets, personal settings, and history. Setup script clones both and links them.

### Obsidian Community Vaults

Obsidian publish templates as blank template vaults — no personal notes. Users clone/fork the template, then track their own notes privately. The template's value is structure (folders, CSS, plugins config), not content. The analogy to this project is direct: structure + skills = the template; coffees + grind-map = the personal notes.

---

## Domain & Prior Art

### HomeAssistant Config Repos

HomeAssistant users routinely share their `configuration.yaml` on GitHub. The established pattern:
- Secrets (`!secret api_key`) are stored in `secrets.yaml` (gitignored)
- Personal entity configs (`customize.yaml`) can be split out and gitignored
- The shareable parts (automations, scripts, lovelace dashboards) are tracked and shared

This mirrors the split here: knowledge files + skills are the automations; `user-setup.md` + `grind-map.md` are the secrets/entity config.

### "Starter Kit" Repos (Create React App, Next.js scaffolding)

These repos are pure templates — no user data. They're not forked; they're cloned/used once and then owned entirely by the user. The original author's repo is the upstream source; users who want upstream updates add it as a remote. This is clean but requires deliberate effort to pull updates.

---

## Feasibility Assessment

| Approach | Effort | Risks | Prerequisites |
|---|---|---|---|
| **A. gitignore + templates (recommended)** | S | Requires `user-setup.md` to be recreated by each user; existing users must adapt | None — purely `.gitignore` and file additions |
| **B. GitHub template repo** | S | No upstream sync mechanism for users; history of personal data visible in old commits until squashed | Complementary with A — should be done alongside |
| **C. Personal data branch** | M | Requires ongoing git discipline; confusing for non-git-savvy users; branch not visible in normal workflow | Git competency in users |
| **D. Separate data repo (private)** | M | Two-repo mental model; more setup steps; requires `GAGGIMATE_STORAGE_PATH` config | MCP env var support already exists |
| **E. Split `coffees/*/README.md`** | S | Slightly more files per coffee; skills must be updated to write separate notes file | Skills update for `/feedback` and `/new-coffee` |
| **F. Track `mcp/data/ratings.json`** | XS | Potential for large file growth over years; sensitive to merge conflicts | None |

---

## Decision Records

### DR-1: Whether to gitignore `coffees/` entirely or split its content

- **Context**: `coffees/*/README.md` contains both community-useful bean research and personal dialing journals. The JSON profiles are useful starting points for others. Gitignoring the whole directory loses the sharable value.
- **Options considered**:
  1. Gitignore `coffees/` entirely — clean but loses community value of bean research
  2. Keep `coffees/` tracked but move tasting notes to a separate `notes/` or `sessions/` file per coffee — clean split
  3. Keep everything tracked, rely on users to overwrite — current approach, confusing
- **Recommendation**: Option 2. Split each coffee into `README.md` (research + starting parameters, tracked) and `notes.md` or a dedicated `sessions.md` (tasting journal, gitignored). Profile JSONs stay tracked as useful references.
- **Trade-offs**: Requires `/feedback` and `/new-coffee` skills to write notes to `notes.md` instead of the README. Small one-time update.

### DR-2: Whether to gitignore `grind-map.md` and `user-setup.md`

- **Context**: Both are purely personal. No value to others. New users must overwrite them anyway.
- **Options considered**:
  1. Keep tracked — simplest, but pollutes clones with Charlie's data
  2. Gitignore + provide template files (`user-setup.example.md`, `grind-map.example.md`) — standard pattern
  3. Gitignore with onboarding script that copies examples to real files on first `claude` invocation
- **Recommendation**: Option 2. Gitignore both. Commit `user-setup.md` (empty template, no personal data) and `grind-map.md` (header only, no rows) as the canonical blank slate. This is the most common convention — the real file and the example are the same file, committed without personal data. New users clone and fill in.
- **Trade-offs**: Existing users (Charlie) must track their personal data elsewhere. See DR-4.

### DR-3: Whether to mark the repo as a GitHub Template

- **Context**: GitHub Template Repos allow users to get a clean copy without Charlie's commit history.
- **Options considered**:
  1. Fork model — users fork the repo; Charlie's data visible in history
  2. Template repo — users click "Use this template"; no shared history, no relationship back to upstream
  3. Both (Template setting on, but also advise forking for contributors)
- **Recommendation**: Enable the GitHub Template setting. This is a one-checkbox change in repository Settings and changes the default "clone" CTA on the GitHub UI. Users who want to contribute to the knowledge base can still fork; users who just want the framework use "Use this template." The distinction is clear and correct.
- **Trade-offs**: Template users can't easily submit PRs. This is fine — the knowledge base is not expected to be community-contributed in the short term.

### DR-4: Portability of Charlie's existing personal data

- **Context**: After gitignoring `coffees/*/notes.md`, `grind-map.md`, and `user-setup.md`, Charlie's existing data won't be tracked. On a machine switch, it would be lost.
- **Options considered**:
  1. Private GitHub repo (`gaggimate-barista-data`) for personal data files — full portability
  2. Manual backup (sync to iCloud, Dropbox, or Time Machine) — simple but not automatic
  3. Track in a `personal` branch of Charlie's fork — portable via git, requires branch awareness
- **Recommendation**: Option 1 (private data repo) is cleanest. Configure `GAGGIMATE_STORAGE_PATH` and a symlink or data-dir path for coffees to point into the private repo. Option 2 is fine as a minimum. Option 3 adds git ceremony for a single-user system. The choice is low-stakes since `mcp/data/` is already externalized — this just extends the same pattern.

### DR-5: Fixing the `mcp/data/ratings.json` portability gap

- **Context**: Shot ratings are gitignored and not portable. They could be lost on machine switch.
- **Options considered**:
  1. Track `mcp/data/ratings.json` — but this was gitignored intentionally (personal data)
  2. Move ratings to the personal data repo (via `GAGGIMATE_STORAGE_PATH` pointing there)
  3. Accept the gap — ratings are reconstructible from the device if needed; the tasting notes are also in `coffees/*/notes.md` (if we implement DR-1)
- **Recommendation**: Option 2 if using a private data repo; Option 3 if not. The key insight is that the notes written to `coffees/*/notes.md` by the `/feedback` skill are the human-readable record — `ratings.json` is machine metadata. If notes are tracked, the loss of `ratings.json` is not catastrophic.

---

## Open Questions

- **Upstream sync UX**: If users use "Use this template," how do they get knowledge base updates? An `upstream` remote and occasional `git merge upstream/main` is workable but needs documentation in README. This is a workflow decision, not a technical blocker.
- **How many others want to use this repo?**: If it's 2-3 people, a lighter approach (just clean up the tracked personal data files) may be sufficient. If it's intended as a community project, the full template + private data repo model is worth the extra setup.
- **Coffees directory as community resource**: If multiple users contribute their bean research, `coffees/` could evolve into a shared coffee database. This is valuable but requires a governance model (PRs for new coffees, quality bar for research). Out of scope for initial isolation work but worth noting.
