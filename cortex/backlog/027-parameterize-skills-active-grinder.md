---
schema_version: "1"
uuid: efc26131-6a10-4bbb-82a0-ca5431457579
title: "Parameterize feedback/new-coffee/consult to read the active grinder"
status: refined
priority: medium
type: feature
tags: [df64v-ssp-migration]
discovery_source: cortex/research/df64v-ssp-migration/research.md
parent: "024"
blocked-by: ["025"]
created: 2026-06-01
updated: 2026-06-01
complexity: complex
criticality: high
spec: cortex/lifecycle/parameterize-feedback-new-coffee-consult-to/spec.md
areas: ['skills']
---

# Parameterize the grinder-aware skills to read the active grinder

## Why

Three skills hardcode the Sette: the feedback workflow records grind in Sette macro+micro notation, new-coffee falls back to the Sette reference when no grind-map match exists, and consult routes grinder questions to the Sette document — so on the DF64V the agent records settings in a dead notation and offers grinder advice for the wrong machine.

## Role

Makes the grinder-aware skills read the active grinder from the user-setup Grinder field and defer to whatever per-grinder reference and shared notation apply, falling back to grinder-relative step advice when no specific reference matches, so the skills behave correctly for the DF64V today and for any future grinder without code changes.

## Integration

Consumes the user-setup Grinder field as the selector, the active grinder reference as the specifics source, and the shared dialing notation as the recording format; writes grind settings into the fresh grind map in that notation. Replaces direct references to the Sette document with selector-driven loading.

## Edges

- Must read the active grinder from the user-setup Grinder field (config) and must not hardcode the DF64V in place of the Sette — swapping one hardcode for another defeats the grinder-agnostic goal.
- Must not break the existing feedback, new-coffee, and consult flows for users still on a Sette — the Sette path stays valid through the same selector.
- Breaks if the user-setup Grinder-field contract changes shape without updating the skills' parsing.
- These skills are protected paths: the change must go through the feature lifecycle, not ad-hoc edits.
- Non-goal: redesigning the skills' broader behavior beyond grinder selection and notation.

## Touch points

- skills/feedback/SKILL.md:136 (hardcoded Sette grind notation in the record-to-grind-map step)
- skills/feedback/SKILL.md:29 (loads SETTE_270.md on grind questions)
- skills/new-coffee/SKILL.md:58 (fallback to SETTE_270.md when no grind-map match)
- skills/consult/SKILL.md:28 (routes the "Sette" keyword to SETTE_270.md)
- skills/consult/SKILL.md:77 (loads SETTE_270_REFERENCE.md for calibration questions)
