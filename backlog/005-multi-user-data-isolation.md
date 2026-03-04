---
id: "005"
title: "Multi-user data isolation"
status: open
priority: high
type: feature
tags: [multi-user-data-isolation]
research: research/multi-user-data-isolation/research.md
spec: research/multi-user-data-isolation/spec.md
created: 2026-03-04
updated: 2026-03-04
---

# Multi-user data isolation

Restructure the repo so personal data (coffees, grind map, user setup, shot ratings) lives in a separate private GitHub repo while the public framework repo contains only knowledge files, MCP server code, and skills.

## Motivation

Others want to use this repo. Currently it contains Charlie's personal extraction data embedded in the working tree and git history, which is confusing for new users and exposes private dialing history publicly.

## Scope

- Private data repo (`gaggimate-barista-data`) holds all personal data
- Public repo is cleaned of personal data, history rewritten
- Symlinks + env var bridge the two repos transparently for the agent
- Setup script automates the link on any machine
- Skills auto-commit and push the private data repo after writes

## Children

- 006: Migrate personal data to private repo and rewrite public history
- 007: Update .gitignore and add .example.md templates
- 008: Write setup script (bin/setup-data-repo.sh)
- 009: Update README for two-repo model
- 010: Enable GitHub Template setting
- 011: Add auto-commit+push to data-writing skills
- 012: Update CLAUDE.md with data architecture note
