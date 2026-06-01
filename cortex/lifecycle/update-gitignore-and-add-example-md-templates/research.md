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
