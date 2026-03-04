# Decomposition: multi-user-data-isolation

## Epic
- **Backlog ID**: 005
- **Title**: Multi-user data isolation

## Work Items

| ID | Title | Priority | Size | Depends On |
|----|-------|----------|------|------------|
| 006 | Migrate personal data to private repo and rewrite public history | high | L | — |
| 007 | Update .gitignore and add .example.md templates | high | S | 006 |
| 008 | Write setup script (bin/setup-data-repo.sh) | high | M | 007 |
| 009 | Update README for two-repo model | medium | S | 008 |
| 010 | Enable GitHub Template setting | low | S | 006 |
| 011 | Add auto-commit and push to data-writing skills | medium | M | 008 |
| 012 | Update CLAUDE.md with data architecture note | low | S | 008 |

## Suggested Implementation Order

**Phase 1 — Critical path (must be sequential):**
1. **006** — Migrate + history rewrite. The foundation. Nothing else is safe until personal data is out of the public repo.
2. **007** — Gitignore + example templates. Establishes the correct public repo state.
3. **008** — Setup script. Makes the system usable on any machine; required by skills and README.

**Phase 2 — Can be done in any order after 008:**
- **009** — README update (medium, should finish before sharing)
- **011** — Auto-commit in skills (medium, closes the manual-git gap)
- **010** — GitHub Template setting (low, UI-only action; do after 006)
- **012** — CLAUDE.md note (low, polish)
