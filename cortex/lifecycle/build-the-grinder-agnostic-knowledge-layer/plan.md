# Plan: build-the-grinder-agnostic-knowledge-layer

## Overview

This is ticket **025** — the *content* layer of the DF64V migration. It builds, in the ticket-mandated internal order, a grinder-neutral foundation (Phase 1) then re-keys the shared extraction knowledge to cross-link it (Phase 2). It does NOT touch the live private `grind-map.md`/`user-setup.md` (026), the `/feedback`/`/new-coffee`/`/consult` skills (027), or any physical commissioning/profile re-dial (028).

Approach and ordering rationale:

1. **Phase 1 lands first (Tasks 1–6)** so the Phase-2 cross-links have stable targets. The ticket Edge and research Adversarial #7 are explicit: settle the final paths of `_NOTATION.md`, `DF64V.md`, and `DF64V_REFERENCE.md` *before* anything links to them. Decision A (notation → standalone `knowledge/grinders/_NOTATION.md`) and Decision B (two DF64V files mirroring the Sette split) are resolved in the spec, so the paths are fixed: `knowledge/grinders/_NOTATION.md`, `knowledge/grinders/DF64V.md`, `knowledge/reference/DF64V_REFERENCE.md`, `knowledge/grinders/_TEMPLATE.md`.
2. **The DF64V hardware files (Tasks 2, 3)** are authored against the seven "wrong-if-stated-baldly" facts from `cortex/research/df64v-ssp-migration/research.md` (Q2 recalibration). R14 is a *content-review gate*, not a grep — but every claim in those two files must be hedged-or-absent per the checklist. To make R14 verifiable rather than self-sealing, Task 14 is a dedicated reviewer pass that reads each file against the seven facts; the writing tasks (2, 3) carry the hedging requirements inline and provide the grep *aids* the spec names, but the binding gate is the independent review in Task 14.
3. **Phase 2 (Tasks 7–13)** re-keys six shared files + the example grind map. Every re-keyed cross-link uses grinder-neutral indirection ("the active grinder's reference, per the Grinder field in `user-setup.md`") — never a literal `SETTE_270.md` path — so 026 can later archive the Sette files without stranding these. This is enforced collectively by Task 13's repo-wide grep (R13).
4. **The Sette files stay in place** (R-scope: `SETTE_270.md` / `SETTE_270_REFERENCE.md` are NOT edited, moved, or deleted — they remain the structural pattern and a valid forkable reference). The CLAUDE.md index keeps its Sette bullet and *gains* a DF64V sibling (Task 6, R5).

Verification philosophy: each task's greps reference independently-observable artifacts (the file it creates, or a prior task's output). No task writes-then-checks-its-own-log. The one genuinely interactive gate (R14 content correctness) is isolated in Task 14 as a reviewer pass reading the Task 2/3 artifacts against the research's seven-fact list — the artifacts pre-exist the review, so the review is not self-sealing.

**Path note**: All `knowledge/...`, `CLAUDE.md`, and `grind-map.example.md` paths are repo-relative; verification commands run from the repo root (`/Users/charlie.hall/Workspaces/gaggimate-barista`). The spec's acceptance greps are quoted with repo-relative paths, matched here verbatim.

**Recovery history**: No `learnings/recovery-log.md` exists — this is a first-attempt plan, no prior approaches to avoid.

## Authoritative hardware source — the seven "wrong-if-stated-baldly" facts (binding on Tasks 2, 3; gated by Task 14)

From `cortex/research/df64v-ssp-migration/research.md` (Q1/Q2) and the spec's R14. `DF64V.md` and `DF64V_REFERENCE.md` must state each of these only in hedged-or-absent form:

1. **Stall** = largely a *fixed early control-board* protection issue + a low-RPM edge case (dense light roast fed all at once), **NOT a DC-motor-torque flaw**. (MiiCoffee retailer's "motor lacks torque" line is the wrong framing.)
2. **Espresso RPM ~1000–1200** is the default; **1400 = retailer/more-body preference, NOT a floor**. Note the low-RPM stall floor.
3. **NO unqualified claim** that the SSP-Multipurpose stall-elimination transfers to the **Cast** line (Cast makes *more* fines).
4. **Seasoning** = the *span* "~2–3 kg before trusting settings, real settling out to ~5–10 kg, coffee-only (not rice)" — never a bald "2–3 kg then trust it".
5. **No microns-per-mark figure** (burr-gap displacement ≠ particle size; ticket non-goal — decline and say why).
6. **"Flats tolerate higher pressure" / "RPM is a body lever"** presented as contested/vendor-framed, NOT fact (Hoffmann null result; McKeon Aloe's RPM→coarser measurement contradicts the vendor "higher RPM = more body" story).
7. **"Red Speed adds body"** presented as vendor-reported, NOT measured.

Plus: **no V2 Silver Knight filter-burr spec** and **no fixed-DF64 / Gen-2 spec** carried — any "Silver Knight" / "DF64 " / "Gen 2" mention must be an explicit do-not-confuse *contrast*, not an imported spec.

## Tasks

### Task 1: Create `knowledge/grinders/_NOTATION.md` (grinder-neutral grind-logging notation contract)

- **Files**: `knowledge/grinders/_NOTATION.md` (new)
- **What**: Author the notation contract file with concrete, loggable mechanics (not just principles). Satisfies R1.
- **Depends on**: none
- **Complexity**: complex
- **Context**:
  - This is the single source of truth for how grind settings are logged on ANY grinder (stepless or stepped). Decision A resolved its home to standalone `knowledge/grinders/_NOTATION.md` (underscore-prefixed to mark "not a grinder" beside `_TEMPLATE.md`). It is referenced by `DF64V.md`, `_TEMPLATE.md`, and `grind-map.example.md` — so its path is FIXED before any of those link to it.
  - **Required content** (all six R1 sub-clauses):
    - **(a) Reference-relative recording**: record settings relative to a fixed reference — the chirp/zero point, e.g. "chirp + N marks". The printed dial "0" is meaningless; do not bless absolute printed-dial numbers as the canonical record.
    - **(b) Coordinate-not-micron statement**: the logged value is an **operator coordinate, explicitly NOT a micron or particle-size claim**. MUST NOT prescribe a microns-per-mark figure.
    - **(c) Epoch-binding mechanic + worked example**: a concrete recorded "zero set: <date>" anchor (or equivalent epoch tag) bound to each "chirp + N marks" value, shown in a worked example so a value is never ambiguous about which zero it was measured from.
    - **(d) Row-superseding convention**: a concrete convention for marking a prior-epoch row dead/superseded on re-zero or burr-swap (e.g. a strike-through or a "pre-rezero" divider), so a prior-epoch row is never silently reused.
    - **(e) Seasoning-state caveat**: the zero drifts coarser through break-in, so early values re-mean themselves until the burr settles.
    - **(f) Prior-grinder dead-coordinate statement**: values logged in a prior grinder's units (e.g. Sette `13D`) are dead-coordinate data — they do NOT translate and are NOT carry-forward. (Consumed later by 026/027 — see Edge Cases.)
  - Keep it grinder-agnostic: it defines the *grammar*, not any one grinder's marks. The DF64V's specific zeroing procedure lives in `DF64V.md`/`DF64V_REFERENCE.md`, not here.
  - **CLAUDE.md Core Rules guard**: "chirp + N marks" is a logging *coordinate*, never an adjustment-step unit. State this so future skills (027) never confuse it with the "go finer/coarser by a small step" adjustment vocabulary.
  - Mirror the repo's cross-link-don't-duplicate pattern: `_TEMPLATE.md` and `DF64V.md` reference this file rather than restating the contract.
- **Verification**:
  - `test -f knowledge/grinders/_NOTATION.md && echo OK` — pass if "OK".
  - `grep -ci 'chirp' knowledge/grinders/_NOTATION.md` ≥ 1 — pass if ≥ 1 (R1a).
  - `grep -i 'not a micron\|operator coordinate\|not.*particle' knowledge/grinders/_NOTATION.md | wc -l` ≥ 1 — pass if ≥ 1 (R1b).
  - `grep -ci 'zero set\|epoch\|re-zero\|supersede\|pre-rezero' knowledge/grinders/_NOTATION.md` ≥ 2 — pass if ≥ 2 (R1c worked-example anchor + R1d row-superseding convention).
  - No prescribed µm/mark number: `grep -Eci 'micron[s]?[ /-]?(per|/)[ ]?mark|[0-9.]+ ?(µm|um|micron)[s]?[ /-]?(per|/)[ ]?mark' knowledge/grinders/_NOTATION.md` = 0 — pass if 0 (R1: must NOT prescribe a microns-per-mark figure).
  - Prior-grinder dead-coordinate statement present: `grep -ci 'dead.coordinate\|do not translate\|don.t translate\|not carry.forward\|prior grinder' knowledge/grinders/_NOTATION.md` ≥ 1 — pass if ≥ 1 (R1f).
- **Status**: [ ] not started

### Task 2: Create `knowledge/grinders/DF64V.md` (operating quick-ref)

- **Files**: `knowledge/grinders/DF64V.md` (new)
- **What**: Author the DF64V operating quick-ref mirroring `SETTE_270.md`'s shape, documenting the correct hardware with all hardware claims hedged per the seven-fact checklist. Satisfies R2; subject to R14 (gated in Task 14).
- **Depends on**: [1]
- **Complexity**: complex
- **Context**:
  - **Structural pattern to mirror** (`knowledge/grinders/SETTE_270.md`, ~64 lines): opens with a `> **Deep dive:**` blockquote linking down to the reference; `## Adjustment System` → `## Quick Adjustment Guide` (problem→adjustment→magnitude table); opens/closes with a pointer to `grind-map.md`.
  - **Correct hardware** (research Q1/Q2): DF64V Gen-3 variable-speed unit + **SSP Cast Lab Sweet V3 Red Speed *espresso* burr (factory pre-installed)**. The V3 Red Speed IS the espresso burr (V3 = espresso re-cut of filter V2; Red Speed = TiAlCN coating → more friction/fines).
  - **Required content**:
    - Stepless collar + chirp/zero dialing (defer the logging *format* to `_NOTATION.md`; this file gives the DF64V's zeroing procedure).
    - Espresso operating point **~1000–1200 RPM** with the low-RPM stall floor noted (fact #2: 1400 = more-body retailer option, not a floor).
    - Espresso starting window **~10–20 marks from zero** (light roast at the finer end; move 1–3 marks at a time).
    - A quick-adjust table using CLAUDE.md-consistent relative vocabulary: "too fast/sour → finer; too slow/bitter → coarser". The magnitude column uses marks as a *logging* coordinate, NOT as an adjustment-step unit — phrase the adjustment as "a small step finer/coarser".
    - Espresso range section (mirroring the Sette's roast×range table, but grinder-relative — marks-from-zero, not Sette macro numbers).
    - **A short, explicitly-hedged "burr character" note** (the deferral target for R6/R7): this flat SSP Cast burr *tends* clarity-leaning (as flats do) but is a *higher*-fines flat than typical; manage body via RPM/ratio. Flagged as a tendency / vendor-framed, NOT a guarantee (facts #6, #7).
  - **Seven-fact hedging (binding; gated by Task 14)**: every quantitative or character claim needs a "this Cast burr / this line" qualifier or omission. Specifically: stall framed per fact #1; RPM per fact #2; no MP-stall-transfer claim (fact #3); no microns-per-mark (fact #5); body/RPM levers hedged (fact #6); Red Speed body hedged (fact #7). Do NOT import V2 Silver Knight filter specs or fixed-DF64/Gen-2 specs (contrast-only if mentioned).
  - **Opening blockquote**: `> **Deep dive:** ... [\`../reference/DF64V_REFERENCE.md\`](../reference/DF64V_REFERENCE.md)`.
  - **Links**: to `_NOTATION.md` (the file from Task 1, same directory: `[\`_NOTATION.md\`](_NOTATION.md)`) for the logging format; pointer to `grind-map.md` for personal settings.
  - **CLAUDE.md guard**: do not introduce absolute temp/pressure numbers competing with the CLAUDE.md Temperature-by-Roast / Pressure-by-Processing tables. RPM is a DF64V control, not a temp/pressure claim.
- **Verification**:
  - `test -f knowledge/grinders/DF64V.md && echo OK` — pass if "OK".
  - `grep -c 'Red Speed' knowledge/grinders/DF64V.md` ≥ 1 — pass if ≥ 1 (R2 correct burr).
  - `grep -E '1[01]00|1200' knowledge/grinders/DF64V.md | wc -l` ≥ 1 — pass if ≥ 1 (R2 RPM operating point).
  - Hedged burr-character note: `grep -ci 'tend\|vendor\|not a guarantee\|higher.*fines' knowledge/grinders/DF64V.md` ≥ 1 — pass if ≥ 1 (R2).
  - Deep-dive link present: `grep -c '../reference/DF64V_REFERENCE.md' knowledge/grinders/DF64V.md` ≥ 1 — pass if ≥ 1 (R2).
  - Notation link present: `grep -c '_NOTATION.md' knowledge/grinders/DF64V.md` ≥ 1 — pass if ≥ 1 (R2 links to `_NOTATION.md`).
  - No microns-per-mark figure: `grep -Eci 'micron[s]?[ /-]?(per|/)[ ]?mark|[0-9.]+ ?(µm|um|micron)[s]?[ /-]?(per|/)[ ]?mark' knowledge/grinders/DF64V.md` = 0 — pass if 0 (R14 fact #5).
  - R14 content-correctness gate is performed in Task 14, not here (this verification confirms the grep *aids*; correctness is the reviewer's call).
- **Status**: [ ] not started

### Task 3: Create `knowledge/reference/DF64V_REFERENCE.md` (deep-dive companion)

- **Files**: `knowledge/reference/DF64V_REFERENCE.md` (new)
- **What**: Author the DF64V deep-dive companion mirroring `SETTE_270_REFERENCE.md`, with all hardware claims hedged per the seven-fact checklist. Satisfies R3; subject to R14 (gated in Task 14).
- **Depends on**: [2]
- **Complexity**: complex
- **Context**:
  - **Structural pattern to mirror** (`knowledge/reference/SETTE_270_REFERENCE.md`, ~156 lines): opens with a `> **Quick lookup:**` blockquote linking back up; sections like Single-Dosing Tips (Retention/Workflow) → Clumping/Static → Calibration → Maintenance → Common Issues.
  - **Required content**:
    - **Seasoning schedule** stated as the *span* (fact #4): **~2–3 kg before trusting settings, real settling out to ~5–10 kg, coffee-only — NOT rice**. Never a bald "2–3 kg then trust it".
    - **RDT / bellows single-dose workflow**: retention **~0.1 g**, **bellows mandatory**; static/clumping → RDT.
    - **Commissioning + factory-alignment check**: burrs are **factory pre-installed — no self-install step**; verify factory alignment within the return window (DF64V QC isn't flawless — chute magnet, occasional shim).
    - **Troubleshooting**: frame the low-RPM stall as **largely a fixed early control-board issue + a low-RPM edge case, NOT a motor-torque flaw** (fact #1). "Can't grind fine enough" is usually alignment/debris/loose-upper-plate, NOT the burr.
  - **Seven-fact hedging (binding; gated by Task 14)**: stall per fact #1; seasoning span per fact #4; no MP-stall-transfer (fact #3); no microns-per-mark (fact #5); no measured body claims for Red Speed (fact #7). No V2 Silver Knight filter spec / no fixed-DF64 / Gen-2 spec carried (contrast-only if mentioned).
  - **Opening blockquote**: `> **Quick lookup:** ... [\`../grinders/DF64V.md\`](../grinders/DF64V.md)`.
- **Verification**:
  - `test -f knowledge/reference/DF64V_REFERENCE.md && echo OK` — pass if "OK".
  - `grep -ci 'bellows' knowledge/reference/DF64V_REFERENCE.md` ≥ 1 — pass if ≥ 1 (R3).
  - `grep -ci 'season' knowledge/reference/DF64V_REFERENCE.md` ≥ 1 — pass if ≥ 1 (R3).
  - Quick-lookup link present: `grep -c '../grinders/DF64V.md' knowledge/reference/DF64V_REFERENCE.md` ≥ 1 — pass if ≥ 1 (R3).
  - Seasoning stated as a span, not a bald figure: `grep -Eci '5[ -]?(to|–|-)[ ]?10 ?kg|5.10 ?kg|settl' knowledge/reference/DF64V_REFERENCE.md` ≥ 1 — pass if ≥ 1 (R14 fact #4 — the ~5–10 kg settle leg is present, not just "2–3 kg").
  - No microns-per-mark figure: `grep -Eci 'micron[s]?[ /-]?(per|/)[ ]?mark|[0-9.]+ ?(µm|um|micron)[s]?[ /-]?(per|/)[ ]?mark' knowledge/reference/DF64V_REFERENCE.md` = 0 — pass if 0 (R14 fact #5).
  - R14 content-correctness gate is performed in Task 14, not here.
- **Status**: [ ] not started

### Task 4: Create `knowledge/grinders/_TEMPLATE.md` (per-grinder scaffold, no DF64V content)

- **Files**: `knowledge/grinders/_TEMPLATE.md` (new)
- **What**: Author a reusable per-grinder template scaffolding a grinder doc for any forker, encoding the operate-vs-maintain seam as explicit headed sections with placement instructions. Satisfies R4.
- **Depends on**: [1]
- **Complexity**: medium
- **Context**:
  - **No DF64V-specific content** — this is generic scaffolding. (Acceptance forbids `df64v|ssp|cast|red speed` substrings.)
  - **Encode the operate-vs-maintain seam as explicit headed sections with placement instructions** (research Adversarial #8 — an "optional `_REFERENCE`" left to judgment is under-specified). Tell the forker explicitly what belongs in the quick-ref (`grinders/<NAME>.md`: adjustment system, espresso range, quick-adjust table) vs the optional `<NAME>_REFERENCE.md` companion (seasoning, maintenance, calibration, troubleshooting, single-dosing workflow). Mirror the Sette/DF64V two-file split as the worked structural precedent.
  - **References `_NOTATION.md` for the notation contract** rather than restating it — the template says "log settings per `_NOTATION.md`", it does not re-define chirp/epoch mechanics.
  - Include the bidirectional blockquote convention (`> **Deep dive:**` down / `> **Quick lookup:**` up) as a placeholder so forkers preserve it.
- **Verification**:
  - `test -f knowledge/grinders/_TEMPLATE.md && echo OK` — pass if "OK".
  - No DF64V-specific content: `grep -ciE 'df64v|ssp|cast|red speed' knowledge/grinders/_TEMPLATE.md` = 0 — pass if 0 (R4).
  - Placement-instruction text for the optional reference companion: `grep -i 'reference companion\|deep-dive\|_REFERENCE' knowledge/grinders/_TEMPLATE.md | wc -l` ≥ 1 — pass if ≥ 1 (R4).
  - References `_NOTATION.md`: `grep -c '_NOTATION.md' knowledge/grinders/_TEMPLATE.md` ≥ 1 — pass if ≥ 1 (R4).
- **Status**: [ ] not started

### Task 5: Add `grinders/DF64V.md` bullet to the CLAUDE.md Knowledge Files index (Sette entry retained)

- **Files**: `CLAUDE.md`
- **What**: Add a `grinders/DF64V.md` bullet to the CLAUDE.md Knowledge Files index, sibling to the existing `grinders/SETTE_270.md` line, leaving the Sette entry in place. Satisfies R5.
- **Depends on**: [2]
- **Complexity**: simple
- **Context**:
  - The Knowledge Files index is a flat bullet list (CLAUDE.md ~line 20–33). The Sette line is exactly (CLAUDE.md:29): `- \`grinders/SETTE_270.md\` - Sette 270 adjustment system, espresso range table, quick adjustment guide`.
  - Add a sibling bullet immediately after it, e.g.: `- \`grinders/DF64V.md\` - DF64V stepless collar + SSP Cast Lab Sweet V3 dialing, espresso RPM operating point, quick adjustment guide`.
  - **Leave the Sette bullet in place** (R5 + scope: Sette files are not removed). `_REFERENCE` files are NOT in this index (they live in the `/consult` router, which is 027's to wire) — so do NOT add a `DF64V_REFERENCE.md` index line, and do NOT add a `_NOTATION.md` index line (Decision A: referenced on `/consult`'s grind row by 027, not a top-level index bullet).
  - **CLAUDE.md edit safety**: edit ONLY the Knowledge Files bullet list (~line 20–33). Do NOT touch the Core Rules block, the Temperature/Pressure tables, or the Data Architecture section.
- **Verification**:
  - `grep -c 'grinders/DF64V.md' CLAUDE.md` ≥ 1 — pass if ≥ 1 (R5 DF64V entry added).
  - `grep -c 'grinders/SETTE_270.md' CLAUDE.md` ≥ 1 — pass if ≥ 1 (R5 Sette entry retained).
- **Status**: [ ] not started

### Task 6: Re-key `knowledge/EXTRACTION_SCIENCE.md` (archetype table, cross-ref, paper-filter parenthetical)

- **Files**: `knowledge/EXTRACTION_SCIENCE.md`
- **What**: Re-frame the grinder-archetype table to fines-driven (burr shape a loose proxy), scope the body↔clarity hedge to cup-character while preserving the fines→grind-size lesson, reconcile the "SSP burrs" low-fines-flat label against the higher-fines Cast, re-point the L21 cross-ref to grinder-neutral indirection, and re-key the L46 paper-filter parenthetical. Satisfies R6 (and R13 for this file's cross-link).
- **Depends on**: [2, 3]
- **Complexity**: complex
- **Context**:
  - **(a) Archetype table (~L13–17)**: keep BOTH archetype examples (`High-fines conical (Sette 270, Niche)` and `Low-fines flat (EK43, SSP burrs)`) but **reframe so the driver is fines content, with burr *shape* a loose proxy** (high-fines vs low-fines). Scope the **"contested / not deterministic" hedge specifically to the body↔clarity *cup-character* claim** — cite that burr shape alone does not cleanly predict body/clarity (judge the burr set, per Hoffmann's null result, research Adversarial #3). **Preserve the well-supported fines→required-grind-size lesson unhedged** (more-unimodal/low-fines → needs finer grind for surface area).
  - **(b) Reconcile the "SSP burrs" label** in the low-fines-flat row (L16) with the fact that the user's SSP Cast is a *higher*-fines flat. Do NOT leave a bare "SSP → low-fines → clarity" implication; do NOT stamp the user's Cast as an authoritative low-fines-clarity exemplar. (Research Adversarial #3 is the HIGHEST CORRECTNESS RISK — soften to contested tendencies, do not canonize.) The per-user body/clarity implication **defers to the active grinder reference's hedged burr-character note** (DF64V.md, Task 2) — teaching becomes config-dependent.
  - **(c) L21 cross-ref**: currently `> *For Sette 270-specific settings and maintenance, see grinders/SETTE_270.md*`. Re-point to grinder-neutral indirection, e.g. `> *For grinder-specific settings, see the active grinder's reference (per the Grinder field in user-setup.md).*` — NOT a hardcoded `SETTE_270.md` path.
  - **(d) L46 paper-filter parenthetical**: currently `...high-fines grinders (like the Sette 270)...`. Re-key to grinder-relative `...high-fines grinders...` (drop the Sette example or replace with "high-fines grinders" generically).
  - **CLAUDE.md Core Rules guard**: do not introduce competing absolute pressure numbers; the "may benefit from 7–8 bar" guidance stays as-is (it already matches the Pressure matrix) — the change is the *attribution*, not the numbers.
- **Verification**:
  - Both archetype examples still present: `grep -c 'conical' knowledge/EXTRACTION_SCIENCE.md` ≥ 1 AND `grep -ci 'flat' knowledge/EXTRACTION_SCIENCE.md` ≥ 1 — pass if both ≥ 1 (R6: both archetype examples retained).
  - Body/clarity claim carries a tendency/contested qualifier: `grep -iE 'tend|contested|burr set' knowledge/EXTRACTION_SCIENCE.md | wc -l` ≥ 1 — pass if ≥ 1 (R6).
  - Fines→grind-size lesson still present (not hedged away): `grep -ci 'finer grind\|finer.*compensate\|fines.*grind' knowledge/EXTRACTION_SCIENCE.md` ≥ 1 — pass if ≥ 1 (R6 — the lesson survives).
  - No hardcoded Sette link: `grep -c 'grinders/SETTE_270.md' knowledge/EXTRACTION_SCIENCE.md` = 0 — pass if 0 (R6 + R13).
- **Status**: [ ] not started

### Task 7: Re-key `knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md` (conical-vs-flat section, cross-ref, retention figure)

- **Files**: `knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md`
- **What**: Scope the hedge to the cup-character dichotomy while preserving the cited Gagné fines→grind-size lesson unhedged, re-key the Sette name to one example among several, re-point the L139 cross-ref to grinder-neutral indirection, and genericize/re-key the L165 "Sette 270 has ~0.5 g retention" line. Satisfies R7 (and R13 for this file's cross-link).
- **Depends on**: [2, 3]
- **Complexity**: complex
- **Context**:
  - **Conical-vs-flat section (L124–137)**: L126 (`The Sette 270 uses conical burrs...`) and L134 (`Conical burr grinders (like the Sette 270)...`) — re-key the Sette name to one example among several (e.g. "conical grinders such as the Sette 270 or Niche"). Scope the **tendency/contested qualifier to the cup-character dichotomy** (the L128–131 body/clarity table). **Explicitly preserve the cited Gagné fines→grind-size lesson (L137) unhedged**: "more unimodal grinders require a much finer average grind size" — this is the canonical high-fines-vs-low-fines lesson the ticket says must survive.
  - **L139 cross-ref**: currently `> *For Sette 270-specific settings and maintenance, see ../grinders/SETTE_270.md*`. Re-point to grinder-neutral indirection (the active grinder's reference per the Grinder field) — NOT a hardcoded path.
  - **L165 retention**: currently `**The Sette 270 has ~0.5g retention** — relatively low.` Re-key to the active grinder or genericize the retention/purge lesson (drop the Sette gram figure). Preserve the purge-before-first-shot / single-dosing teaching. (Research Adversarial #10: this is NOT a Sette-correctness adjudication — drop/genericize the figure and the 0.5g-vs-1g contradiction dissolves as a side effect.)
  - Stays grinder-neutral (serves conical + flat; defers cup-character specifics to the active reference).
- **Verification**:
  - Conical-vs-flat section retains the fines→grind-size lesson: `grep -ci 'unimodal.*finer\|finer.*grind size\|finer average grind' knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md` ≥ 1 — pass if ≥ 1 (R7 Gagné lesson preserved).
  - Cup-character hedge present: `grep -iE 'tend|contested|burr set' knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md | wc -l` ≥ 1 — pass if ≥ 1 (R7 hedge scoped to cup-character).
  - No hardcoded Sette link: `grep -c 'grinders/SETTE_270.md' knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md` = 0 — pass if 0 (R7 + R13).
  - "~0.5g" Sette retention figure removed/genericized: `grep -c '0.5g retention\|~0.5g\|0.5 g retention' knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md` = 0 — pass if 0 (R7).
- **Status**: [ ] not started

### Task 8: Re-key `knowledge/SPECIAL_CATEGORIES.md` (decaf macro-step + "On the Sette 270" sentence)

- **Files**: `knowledge/SPECIAL_CATEGORIES.md`
- **What**: Re-key the decaf "macro steps" language (L17, L24) to grinder-relative, replace the "On the Sette 270, …" sentence with grinder-neutral phrasing, preserving the decaf-flows-faster → start-coarser teaching. Satisfies R8.
- **Depends on**: [2, 3]
- **Complexity**: simple
- **Context**:
  - **L17** (table row): currently `| **Grind** | Your baseline | 1–3 macro steps *coarser* | ...`. Re-key "macro steps" → grinder-relative, e.g. "a small step coarser" / "slightly coarser".
  - **L24**: currently `**Expect:** Decaf shots flow *noticeably* faster at the same grind setting. On the Sette 270, start 2–3 macro steps coarser than your regular setting and adjust from there.` Replace the "On the Sette 270, …" sentence with grinder-neutral phrasing, e.g. "start a small step coarser than your regular setting and adjust from there."
  - **Preserve** the decaf-flows-faster → start-coarser teaching (do not remove the lesson, only re-key the units).
  - CLAUDE.md guard: "a small step coarser" is the safe relative phrasing; do not reintroduce macro-step units or absolute numbers.
- **Verification**:
  - No "macro step" language: `grep -ci 'macro step' knowledge/SPECIAL_CATEGORIES.md` = 0 — pass if 0 (R8).
  - Decaf coarser-grind guidance retained: `grep -ci 'coarser' knowledge/SPECIAL_CATEGORIES.md` ≥ 1 — pass if ≥ 1 (R8 teaching preserved).
  - No "Sette" mention in the decaf guidance: `grep -ci 'Sette' knowledge/SPECIAL_CATEGORIES.md` = 0 — pass if 0 (grinder-neutral; supports R13's spirit).
- **Status**: [ ] not started

### Task 9: Re-key `knowledge/reference/BEAN_FRESHNESS_REFERENCE.md` (frozen-bean macro-step, L149)

- **Files**: `knowledge/reference/BEAN_FRESHNESS_REFERENCE.md`
- **What**: Re-key the frozen-bean "macro steps" language (L149) to grinder-relative, preserving the frozen-grinds-finer → go-coarser teaching. Satisfies R9.
- **Depends on**: [2, 3]
- **Complexity**: simple
- **Context**:
  - **L149**: currently `Frozen beans grind finer than room-temperature beans at the same grinder setting. Adjust **1–2 macro steps coarser** to compensate, then dial in from there...`. Re-key "1–2 macro steps coarser" → grinder-relative, e.g. "a small step coarser".
  - **Preserve** the frozen-grinds-finer → go-coarser teaching and the following lower-pressure note.
- **Verification**:
  - No "macro step" language: `grep -ci 'macro step' knowledge/reference/BEAN_FRESHNESS_REFERENCE.md` = 0 — pass if 0 (R9).
  - Frozen-bean coarser guidance retained: `grep -ci 'coarser' knowledge/reference/BEAN_FRESHNESS_REFERENCE.md` ≥ 1 — pass if ≥ 1 (R9 teaching preserved).
- **Status**: [ ] not started

### Task 10: Re-key `knowledge/reference/ESPRESSO_BREWING_REFERENCE.md` (turbo macro-step L35 + Sette retention L169)

- **Files**: `knowledge/reference/ESPRESSO_BREWING_REFERENCE.md`
- **What**: Re-key the turbo "2-4 macro steps coarser" (L35) to grinder-relative, and re-key/genericize the "Sette 270 … ~1g retention" line (L169), preserving the turbo coarser-grind + low-pressure teaching. Satisfies R10.
- **Depends on**: [2, 3]
- **Complexity**: simple
- **Context**:
  - **L35**: currently `- **Grind:** Coarser (medium-fine, 2-4 macro steps coarser than traditional)`. Re-key "2-4 macro steps coarser" → grinder-relative, e.g. "Coarser (medium-fine, a few steps coarser than traditional)" / "noticeably coarser than traditional".
  - **L169**: currently `- **Purge grinder retention** when switching coffees — run 2-3g through to clear the old grounds. The Sette 270 has relatively low retention (~1g), but stale grounds...`. Re-key to the active grinder or genericize (drop the Sette gram figure). Preserve the purge-when-switching teaching. (Genericizing here dissolves the pre-existing 0.5g-vs-1g Sette inconsistency as a side effect — NOT adjudicated as a Sette-correctness question, per research Adversarial #10.)
  - **Preserve** the turbo coarser-grind + low-pressure teaching (the surrounding turbo block stays intact).
- **Verification**:
  - No "macro step" language: `grep -ci 'macro step' knowledge/reference/ESPRESSO_BREWING_REFERENCE.md` = 0 — pass if 0 (R10).
  - No Sette-specific retention gram figure: `grep -Eci 'Sette 270 has.*retention|retention \(~?[0-9.]+ ?g\)|~1g\b|~0.5g\b' knowledge/reference/ESPRESSO_BREWING_REFERENCE.md` = 0 — pass if 0 (R10: no Sette-specific retention gram figure remains).
  - Turbo coarser teaching retained: `grep -ci 'coarser' knowledge/reference/ESPRESSO_BREWING_REFERENCE.md` ≥ 1 — pass if ≥ 1 (R10 teaching preserved).
- **Status**: [ ] not started

### Task 11: Re-key `knowledge/reference/PROFILE_LIBRARY_REFERENCE.md` (turbo macro-step, L353)

- **Files**: `knowledge/reference/PROFILE_LIBRARY_REFERENCE.md`
- **What**: Re-key the turbo "2-4 macro steps coarser on most grinders" (L353) to grinder-relative, preserving the turbo coarser + longer-ratio teaching. Satisfies R11.
- **Depends on**: [2, 3]
- **Complexity**: simple
- **Context**:
  - **L353**: currently `**Note:** Requires coarser grind than typical espresso. Expect 2-4 macro steps coarser on most grinders. The longer ratio is essential...`. Re-key "2-4 macro steps coarser on most grinders" → grinder-relative, e.g. "Expect to go noticeably coarser than typical espresso."
  - **Preserve** the turbo coarser + longer-ratio (1:2.5–1:3) teaching.
- **Verification**:
  - No "macro step" language: `grep -ci 'macro step' knowledge/reference/PROFILE_LIBRARY_REFERENCE.md` = 0 — pass if 0 (R11).
  - Turbo coarser guidance retained: `grep -ci 'coarser' knowledge/reference/PROFILE_LIBRARY_REFERENCE.md` ≥ 1 — pass if ≥ 1 (R11 teaching preserved).
- **Status**: [ ] not started

### Task 12: Re-key the example grind map value (`grind-map.example.md`, value-only — no RPM column)

- **Files**: `grind-map.example.md`
- **What**: Re-key the Grind-column value (L9, `13C`) to grinder-neutral notation and update the surrounding legend/prose to reference `_NOTATION.md`, WITHOUT adding the RPM column or changing column structure. Satisfies R12.
- **Depends on**: [1]
- **Complexity**: simple
- **Context**:
  - **L9** Grind cell: currently `13C` in the example row `| Example Roaster Ethiopia Yirgacheffe | Light | Washed | Ethiopia | 21 | 13C | Bloom Slide | 1:2.5 | 94°C | 5 | Jan 15 |  |`. Re-key the Grind cell value to chirp-relative notation, e.g. `chirp + 18`.
  - **Update surrounding legend/prose** to reference `_NOTATION.md` (the Task 1 file) for the notation format. Add a one-line legend note, e.g. `*Grind — recorded relative to the chirp/zero point per [\`knowledge/grinders/_NOTATION.md\`](knowledge/grinders/_NOTATION.md). Prior-grinder codes do not carry forward.*`
  - **Do NOT add the RPM column or change column structure** — ticket 026 owns the fresh-map structure and the RPM column. The table currently has 12 columns (incl. the trailing `Puck Screen?` column added by a prior ticket); preserve that exact column count. Only the Grind *value* and legend prose change.
  - **Boundary with 026** (Decision C / research Adversarial #4): value-only re-key is decisively safer — 026 lands the RPM column atomic with its writer.
- **Verification**:
  - No `13C` value: `grep -c '13C' grind-map.example.md` = 0 — pass if 0 (R12).
  - Grind cell uses chirp-relative notation: `grep -ci 'chirp' grind-map.example.md` ≥ 1 — pass if ≥ 1 (R12 chirp-relative notation in the cell/legend).
  - References `_NOTATION.md`: `grep -c '_NOTATION.md' grind-map.example.md` ≥ 1 — pass if ≥ 1 (R12 legend references the contract).
  - Column count unchanged (no RPM column added): `awk -F'|' 'NR==7 {print NF}' grind-map.example.md` equals the pre-edit value — capture the pre-edit header NF first (`awk -F'|' 'NR==7 {print NF}' grind-map.example.md` before editing; it is 14 = 12 columns + 2 outer pipes), then confirm it is unchanged after editing. Pass if the post-edit header NF equals the pre-edit header NF (R12: no RPM column added). The example row (NR==9) NF must likewise be unchanged.
- **Status**: [ ] not started

### Task 13: Cross-link indirection sweep — no broken Sette links across all de-Setted files

- **Files**: none modified (verification-only sweep across the six Tasks 6–11 files)
- **What**: Confirm that every re-keyed cross-link in the de-Setted files points to grinder-neutral indirection or `_NOTATION.md`, never to a hardcoded `grinders/SETTE_270.md` or `reference/SETTE_270_REFERENCE.md` path. Satisfies R13.
- **Depends on**: [6, 7, 8, 9, 10, 11]
- **Complexity**: simple
- **Context**:
  - This is the collective R13 acceptance: the de-Setted files must not strand when 026 later archives the Sette files. It checks the six files Tasks 6–11 edited for any residual `SETTE_270` path reference.
  - Note: the *index* file `CLAUDE.md` (Task 5) and the unmodified `SETTE_270.md`/`SETTE_270_REFERENCE.md` themselves legitimately retain `SETTE_270` references and are NOT in this sweep's file list — R13 scopes the sweep to the six de-Setted shared-knowledge files only.
  - This verification reads artifacts produced by Tasks 6–11 (pre-existing at sweep time) — it is not self-sealing.
- **Verification**:
  - `grep -rl 'SETTE_270' knowledge/EXTRACTION_SCIENCE.md knowledge/reference/EXTRACTION_SCIENCE_REFERENCE.md knowledge/SPECIAL_CATEGORIES.md knowledge/reference/BEAN_FRESHNESS_REFERENCE.md knowledge/reference/ESPRESSO_BREWING_REFERENCE.md knowledge/reference/PROFILE_LIBRARY_REFERENCE.md` returns nothing (empty output, no files listed) — pass if no files are listed (R13).
- **Status**: [ ] not started

### Task 14: Hardware-correctness content review of the two DF64V files (R14 seven-fact checklist)

- **Files**: none modified; reviewer pass reading `knowledge/grinders/DF64V.md` and `knowledge/reference/DF64V_REFERENCE.md` (produced by Tasks 2, 3)
- **What**: A reviewer (human or fresh sub-agent) reads each DF64V file against the seven "wrong-if-stated-baldly" facts and confirms each is either correctly hedged or absent — no unqualified version present — plus confirms no V2 Silver Knight / fixed-DF64 / Gen-2 spec is carried. Satisfies R14.
- **Depends on**: [2, 3]
- **Complexity**: complex
- **Context**:
  - **This is the load-bearing correctness gate** — the spec is explicit that this CANNOT be verified by string-presence greps (a file can pass every grep while asserting a wrong-variant fact). The review reads the two files (which pre-exist this task, authored in Tasks 2/3) against the seven-fact checklist in the "Authoritative hardware source" section above. This is NOT self-sealing: the artifacts under review are produced by prior tasks, not by this task.
  - **The seven facts to confirm hedged-or-absent** (verbatim from spec R14):
    1. Stall framed as fixed-early-board + low-RPM edge case, NOT a motor-torque flaw.
    2. Espresso RPM ~1000–1200 as default (1400 = retailer/more-body, not a floor).
    3. NO unqualified claim that SSP-Multipurpose stall-elimination transfers to the Cast line.
    4. Seasoning stated as the ~2–3 kg-then / ~5–10 kg-settle *span*, never a bald "2–3 kg then trust it".
    5. No microns-per-mark figure.
    6. "Flats tolerate higher pressure" / "RPM is a body lever" presented as contested/vendor-framed, not fact.
    7. "Red Speed adds body" presented as vendor-reported, not measured.
  - Also confirm no V2 Silver Knight filter-burr spec and no fixed-DF64/Gen-2 spec is carried (any "Silver Knight" / "DF64 " / "Gen 2" mention is an explicit do-not-confuse contrast, NOT an imported spec).
  - **Grep aid** (locates candidate lines for inspection; NOT a pass/fail by itself): `grep -niE 'silver knight|gen 2|DF64 ' knowledge/grinders/DF64V.md knowledge/reference/DF64V_REFERENCE.md` — every hit must be inspected to be a contrast line, not a carried spec.
- **Verification**:
  - **Interactive/session-dependent (the R14 gate):** the reviewer reads `knowledge/grinders/DF64V.md` and `knowledge/reference/DF64V_REFERENCE.md` line-by-line and confirms each of the 7 facts is hedged-or-absent (no unqualified wrong-variant present), and that no V2 Silver Knight / fixed-DF64 / Gen-2 spec is carried. Recorded as a pass only when all 7 + the no-wrong-variant check hold. This is a content judgment over artifacts authored by Tasks 2/3, not a grep.
  - **Grep aid (run, then inspect each hit):** `grep -niE 'silver knight|gen 2|DF64 ' knowledge/grinders/DF64V.md knowledge/reference/DF64V_REFERENCE.md` — each hit must be a contrast line. Zero hits also passes (no contrast lines needed).
- **Status**: [ ] not started

### Task 15: Final integration verification — full R1–R14 acceptance sweep

- **Files**: none modified; verification-only
- **What**: Run every R1–R13 grep acceptance in sequence and confirm the R14 content review (Task 14) recorded a pass, so any drift across the implementation tasks surfaces in one place before review.
- **Depends on**: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
- **Complexity**: simple
- **Context**:
  - Read-only end-to-end check. Each requirement's grep acceptance from Tasks 1–13 is replicated as a single sweep; R14's interactive gate is confirmed via Task 14's recorded reviewer outcome.
  - All checks read artifacts produced by prior tasks — not self-sealing.
- **Verification**:
  - All grep commands from Tasks 1–13 verifications run and pass — pass if every command's count/exit assertion holds.
  - R14 reviewer pass (Task 14) is recorded as passed for both DF64V files — pass if the seven-fact + no-wrong-variant content review confirmed hedged-or-absent.
  - Phase-1-before-Phase-2 ordering held: the four foundation files (`knowledge/grinders/_NOTATION.md`, `knowledge/grinders/DF64V.md`, `knowledge/reference/DF64V_REFERENCE.md`, `knowledge/grinders/_TEMPLATE.md`) all exist (`ls` them) before the Phase-2 cross-links resolve — pass if all four exist and Task 13's no-broken-link sweep returned empty.
- **Status**: [ ] not started

## Verification Strategy

End-to-end, the change is correct when:

1. **Foundation files exist and are self-consistent** (Phase 1): `knowledge/grinders/_NOTATION.md` (R1: chirp, coordinate-not-micron, epoch anchor + row-superseding ≥2, dead-coordinate, no µm/mark), `knowledge/grinders/DF64V.md` (R2: Red Speed, ~1000–1200 RPM, hedged burr-character, deep-dive + `_NOTATION` links), `knowledge/reference/DF64V_REFERENCE.md` (R3: bellows, seasoning span, quick-lookup link), `knowledge/grinders/_TEMPLATE.md` (R4: no DF64V content, placement instructions, references `_NOTATION.md`) all pass their grep checks.
2. **CLAUDE.md index** gains a `grinders/DF64V.md` bullet while retaining `grinders/SETTE_270.md` (R5) — no Core Rules / Temperature / Pressure table edits.
3. **De-Setted shared knowledge** (Phase 2): each of the six files (Tasks 6–11) drops its "macro step" units / Sette-named advice while preserving its teaching (fines→grind-size, decaf-coarser, frozen-coarser, turbo-coarser), and the body/clarity claims carry a tendency/contested qualifier scoped to cup-character. Sette retention gram figures are removed/genericized (the 0.5g-vs-1g contradiction dissolves as a side effect).
4. **No broken Sette links** (R13): the repo-wide `grep -rl 'SETTE_270'` over the six de-Setted files returns nothing — they use grinder-neutral indirection / `_NOTATION.md` only, so 026 can archive the Sette files without stranding them.
5. **Example grind map** (R12): `13C` → chirp-relative notation, legend references `_NOTATION.md`, column count unchanged (no RPM column — that's 026's).
6. **Hardware correctness** (R14 — the load-bearing gate): the Task 14 reviewer pass confirms all seven "wrong-if-stated-baldly" facts are hedged-or-absent in both DF64V files and no V2 Silver Knight / fixed-DF64 / Gen-2 spec is carried. This is a content judgment over the Task 2/3 artifacts, isolated from the writing tasks so it is independently observable, not self-sealing.
7. **Final sweep** (Task 15) reruns every R1–R13 grep and confirms the R14 reviewer outcome, catching any cross-task drift in one place.

**Self-sealing avoidance**: No task writes an artifact then checks for that same artifact to satisfy verification. Tasks 1–12 verify the files they create/edit via grep on independently-observable content. Task 13 (link sweep), Task 14 (content review), and Task 15 (final sweep) all read artifacts produced by *prior* tasks. The single interactive gate (R14) reviews pre-existing Task 2/3 files against the externally-fixed seven-fact list from `cortex/research/df64v-ssp-migration/research.md`.

## Scope Boundaries (per spec Non-Requirements)

- Does NOT switch the live private `grind-map.md` / `user-setup.md`, archive the Sette map, snapshot telemetry, or add the RPM column to the live or example map — **ticket 026**.
- Does NOT edit `/feedback`, `/new-coffee`, or `/consult` skills (grinder selection, Sette hardcodes, `/consult` keyword router, the invalid `"10M"` example) — **ticket 027** (lifecycle-gated protected paths). 025 only stays *consistent* with the skills' relative-step vocabulary; it does not wire `DF64V.md`/`DF64V_REFERENCE.md` into the `/consult` router (027 hands-off list).
- Does NOT archive, move, or delete `SETTE_270.md` / `SETTE_270_REFERENCE.md` — they stay in place as the structural pattern and a valid forkable Sette reference.
- Does NOT add a `DF64V_REFERENCE.md` or `_NOTATION.md` bullet to the CLAUDE.md top-level index (`_REFERENCE`/notation files live on the `/consult` router, which is 027's to wire).
- Does NOT document filter-grind use of the burrs, and does NOT prescribe a microns-per-mark figure.
- Does NOT commission the grinder or re-dial any per-coffee profile — **ticket 028**.

## Handoff to ticket 027 (informational; 025 does not edit these)

Skill lines still naming the Sette, for 027 to repoint off hardcoded Sette paths and wire in `DF64V.md`/`DF64V_REFERENCE.md`:
- `.claude/skills/new-coffee/SKILL.md:58,66`
- `.claude/skills/new-coffee/references/SELF_CHECK.md:14,133`
- `.claude/skills/consult/SKILL.md:28` (grind keyword router → `SETTE_270.md`) and `:77` (deep-reference route → `SETTE_270_REFERENCE.md`)
- `.claude/skills/feedback/SKILL.md:29,136` (the `:136` line includes an invalid `"10M"` Sette example — Sette micro letters are A–I — for 027 to correct)

Note: skills live at `.claude/skills/`, not `skills/` as the tickets originally cite.
