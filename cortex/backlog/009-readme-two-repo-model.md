---
id: "009"
title: "Update README for two-repo model"
status: closed
priority: medium
type: feature
parent: "005"
blocked-by: ["008"]
tags: [multi-user-data-isolation]
research: research/multi-user-data-isolation/research.md
spec: research/multi-user-data-isolation/spec.md
created: 2026-03-04
updated: 2026-03-04
---

# Update README for two-repo model

## What this delivers

README updated to reflect the two-repo architecture with clear paths for two audiences:
1. **New users** — clone public repo, copy `.example.md` files, configure `.mcp.json`, start dialing
2. **Self on new machine** — clone both repos, run setup script, configure `.mcp.json`

## Spec references

- Must Have 5: Setup is documented and reproducible

## Acceptance criteria

- README has a clear "Setup" section covering both paths above
- New user path explicitly states data won't persist across machines without a private repo
- Self/returning user path shows the exact `bin/setup-data-repo.sh` invocation
- README warns that `GAGGIMATE_STORAGE_PATH` misconfiguration causes silent ratings loss (and that the setup script handles this automatically)
- Project structure diagram updated to reflect that `coffees/`, `grind-map.md`, `user-setup.md` are symlinks (private data, not included)
