---
schema_version: "1"
uuid: f23d821e-b175-4769-b1d8-d8919bc4b3bb
title: "Build the grinder-agnostic knowledge layer (DF64V + notation + de-Sette)"
status: complete
priority: high
type: feature
tags: [df64v-ssp-migration]
discovery_source: cortex/research/df64v-ssp-migration/research.md
parent: "024"
blocked-by: []
created: 2026-06-01
updated: 2026-06-01
complexity: complex
criticality: high
spec: cortex/lifecycle/build-the-grinder-agnostic-knowledge-layer/spec.md
areas: ['docs']
---

# Build the grinder-agnostic knowledge layer

## Why

The repo's grinder knowledge is hardcoded to the Baratza Sette 270: the only grinder reference documents its stepped macro+micro dial, grind settings are expressed in Sette codes with no convention that survives a re-zero or burr swap, and the shared extraction files teach using the Sette as the worked example in Sette-specific "macro steps." A barista on the DF64V has no in-repo guidance for finding the chirp point, choosing an espresso RPM, seasoning the burrs, or the single-dose bellows workflow, and any other-grinder user gets adjustment instructions that do not map to their dial.

## Role

Establishes the grinder-agnostic knowledge layer: a per-grinder operating reference for the DF64V with SSP Cast Lab Sweet V3 Red Speed espresso burrs, a reusable per-grinder template, a grinder-neutral notation for recording a setting relative to a fixed reference, and shared extraction knowledge re-keyed to grinder-relative language that defers specifics to whichever grinder reference is active. After this lands, the repo teaches and dials for whatever grinder the setup names, not just the Sette.

## Integration

The DF64V reference and the template slot into the grinder-reference layer that is selected by the user-setup Grinder field; the reference and the grind map both express settings in the shared notation; the re-keyed shared knowledge cross-links to the active grinder reference instead of embedding Sette numbers. The notation is the common language the grind history and the grinder-aware skills also read and write.

## Edges

- The DF64V reference must document the correct hardware — the DF64V Gen 3 variable-speed unit and the SSP Cast Lab Sweet V3 Red Speed espresso burr — and must not carry filter-variant (V2 Silver Knight) or wrong-generation (the fixed DF64 / Gen 2) specs; the research recalibration is the authority on which adverse signals attach to the wrong variant.
- Must not replace the Sette hardcode with a DF64V hardcode: the reference is chosen via the user-setup Grinder field like any grinder, so the knowledge layer stays config-driven and forkable.
- The reference and grind records must speak the shared notation, not invent a per-document setting format.
- The notation must stay grinder-neutral and must not bless absolute printed-dial numbers as the canonical record, since those drift on re-zero and burr swap.
- The shared-knowledge change must preserve the high-fines-versus-low-fines teaching — re-key the examples, do not remove the lesson — and must not introduce adjustment vocabulary that diverges from the skills' relative-step language.
- The template must carry no DF64V-specific content so a forker can fill it for any grinder.
- Non-goals: documenting filter-grind use of the burrs, and prescribing a microns-per-mark figure.
- Internal order: establish the notation and the DF64V reference and template first, then re-key the shared knowledge to cross-link them.

## Touch points

- knowledge/grinders/ (new DF64V.md and _TEMPLATE.md)
- knowledge/grinders/SETTE_270.md (existing per-grinder doc; structural pattern)
- knowledge/reference/SETTE_270_REFERENCE.md (deep-dive companion pattern)
- grind-map.example.md (notation and Grind-column format)
- knowledge/EXTRACTION_SCIENCE.md (grinder-archetype table; Sette conical example)
- knowledge/SPECIAL_CATEGORIES.md (decaf macro-step advice)
- knowledge/reference/BEAN_FRESHNESS_REFERENCE.md (frozen-bean macro-step advice)
- knowledge/reference/ESPRESSO_BREWING_REFERENCE.md (turbo macro-step advice)
- knowledge/reference/PROFILE_LIBRARY_REFERENCE.md (turbo macro-step advice)
- knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md (Sette conical fines passage)
- cortex/research/df64v-ssp-migration/research.md (Q2 recalibration; correct DF64V Gen-3 / V3-Red-Speed-espresso variant data)
