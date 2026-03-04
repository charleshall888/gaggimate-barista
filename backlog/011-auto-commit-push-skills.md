---
id: "011"
title: "Add auto-commit and push to data-writing skills"
status: open
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

# Add auto-commit and push to data-writing skills

## What this delivers

After any skill step that writes personal data, the agent automatically commits and pushes the private data repo. No manual `git` work required from the user.

## Spec references

- Should Have 7: Agent commits and pushes after writes

## Skills to update

- `/new-coffee` (SKILL.md) — writes new coffee directory to `coffees/`
- `/feedback` (SKILL.md) — writes tasting notes, updates `grind-map.md`, syncs ratings
- `/gaggimate-profiles` (SKILL.md) — writes profile JSON to `coffees/{name}/`

## Acceptance criteria

- After `/feedback` completes, `git log` in the private data repo shows a new commit with the changes
- Commit is pushed to `origin`
- The agent does not prompt for confirmation before committing
- If `.data-repo-path` does not exist (new user without private repo), the commit step is skipped silently with no error
- Commit message reflects the skill and coffee being updated (e.g., "Record feedback: Typica Anaerobic shot 173")

## Implementation pattern

At the end of each data-writing skill's final step:
1. Read `.data-repo-path` from project root
2. If file exists: `cd {data-repo-path} && git add . && git commit -m "{message}" && git push`
3. If file absent: skip silently
