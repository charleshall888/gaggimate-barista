# Review: puck-screen-support

## Stage 1: Spec Compliance

### R1: Equipment table row in user-setup.example.md
- **Expected**: Optional Puck Screen row in Equipment table, default `None`.
- **Actual**: Line 11 has `| **Puck Screen** | None |`. Both grep checks return 1.
- **Verdict**: PASS

### R2: knowledge/PUCK_SCREENS.md as quick-ref with classification dispatcher
- **Expected**: File with `## Screen Classification`, ≥4 other top-level sections (When to Use, Effects, Common Pitfalls, Cleaning), reference pointer; tokens `thin (≤ 1mm)`, `thick (> 1mm)`, `round-hole`, `mesh` cited.
- **Actual**: All sections present (lines 9, 35, 46, 66, 79). Reference pointer present at lines 5 and 146. Token counts: thin (≤ 1mm)=4, thick (> 1mm)=3, round-hole=11, mesh=12 — all ≥ thresholds.
- **Verdict**: PASS

### R3: knowledge/reference/PUCK_SCREENS_REFERENCE.md temperature compensation
- **Expected**: ≥60 lines, heat-buffer physics section, +1°C and +2–3°C numeric claims.
- **Actual**: 75 lines; "Heat-Buffer Physics" section at line 9; "+1°C" appears 3×; "+2–3°C" appears 2×. Compensation table at lines 43–47.
- **Verdict**: PASS

### R4: Migrate EXTRACTION_SCIENCE.md:42 row + update line 44
- **Expected**: Row stub `See [PUCK_SCREENS.md](PUCK_SCREENS.md) | — |`; original phrase migrated; line 44 forward reference.
- **Actual**: Stub matches at line 42. "Protects puck from shower screen imprint" returns 0 in EXTRACTION_SCIENCE.md and 1 in PUCK_SCREENS.md (line 75). Recommended-combo line at 44 includes `PUCK_SCREENS.md` reference.
- **Verdict**: PASS

### R5: BASKETS.md masking note (with paragraph proximity)
- **Expected**: Masking note in same/adjacent paragraph as the line-16 mesh-imprint rule, preserving original "mesh pattern pressed into the surface" + "reduce your dose by 0.5g".
- **Actual**: Line 16 reads as a single paragraph: existing mesh-pattern + 0.5g rule, then "If you have a puck screen installed, this check is masked — rely on flow behavior and measured headroom instead." Same paragraph (single sentence cluster, no blank line). Token counts: puck screen=1, masked=1, original phrases preserved.
- **Verdict**: PASS

### R6: grind-map.example.md Puck Screen? column
- **Expected**: Header has "Puck Screen?"; example row at line 9 has 14 fields by `awk -F'|'`.
- **Actual**: Header on line 7 includes "Puck Screen?"; `awk -F'|' 'NR==9 {print NF}'` returns 14.
- **Verdict**: PASS

### R7: grind-map.example.md semantic-contract comment
- **Expected**: "blank = unknown" + "NOT N / not no screen" contrast.
- **Actual**: Line 13: `Puck Screen? — "Y" if a screen was installed, blank if unknown. Blank is NOT "no screen" — use "N" to record explicit absence`. Both grep counts ≥1.
- **Verdict**: PASS

### R8: MEMORY.md two distinct rows
- **Expected**: Two distinct rows on different lines.
- **Actual**: Line 21: `Puck screens (quick) | knowledge/PUCK_SCREENS.md`; line 27: `Puck screens (deep) | knowledge/reference/PUCK_SCREENS_REFERENCE.md`. Two different lines confirmed.
- **Verdict**: PASS

### R9: consult/SKILL.md routing-table row (location)
- **Expected**: Row inside the routing/classification table, citing both quick + deep.
- **Actual**: Line 36 of consult SKILL.md is a routing-table row: `| puck screen, normcore, screen imprint, screen orientation | knowledge/PUCK_SCREENS.md | knowledge/reference/PUCK_SCREENS_REFERENCE.md |`. Both files cited on the single table row. `grep -o 'PUCK_SCREENS' ... | wc -l` = 2 (quirk noted: the `-c` grep returns 1 because both citations are on one line, but `grep -o` confirms two occurrences as expected).
- **Verdict**: PASS

### R10: diagnose/SKILL.md cold-screen guardrail
- **Expected**: ≥2 puck-screen mentions; preheat within 10 lines of a puck-screen mention.
- **Actual**: 4 lines mention "puck screen" (lines 145, 147, 153, 154); "preheat" appears twice (lines 153, 154); both adjacent (same row of the gated guardrail table). Co-location verified.
- **Verdict**: PASS

### R11: diagnose/SKILL.md channeling-nuance + hedge clauses
- **Expected**: Both prep-driven and shower-screen-driven tokens (≥2 combined); reasoning sentence ("mitigated/reduced"); orientation hedge ("upside-down/wrong size/bent/orientation"); explicit "likely" not "almost certainly".
- **Actual**: Line 154: `the remaining channeling is **likely** (NOT "almost certainly") puck-prep-driven`; uses "already mitigates shower-screen-driven channeling" (matches mitigat/reduc); orientation hedge present ("upside-down? smooth side vs textured side... wrong size for the basket... bent/warped"). Token counts: prep-driven/shower-screen-driven=4 lines; mitigat/reduc=1; orientation tokens=2.
- **Verdict**: PASS

### R12: CLAUDE.md Core Rule byte-preservation
- **Expected**: SHA256 = `7976b6a572f2879ef72eb62e7c6ff9b71555ab34ae80807d808292dfcaf8f7ae`.
- **Actual**: `awk '/Sour AND bitter = channeling/,/^$/' CLAUDE.md | shasum -a 256` produces `7976b6a572f2879ef72eb62e7c6ff9b71555ab34ae80807d808292dfcaf8f7ae` — exact match.
- **Verdict**: PASS

### R13: CLAUDE.md Knowledge Files entry + Unconfigured rule + parsing contract
- **Expected**: PUCK_SCREENS in Knowledge Files list, Unconfigured-check rule for Puck Screen, parsing contract documented; Puck Screen referenced ≥2× in CLAUDE.md.
- **Actual**: Line 33 lists `PUCK_SCREENS.md`; line 46 contains the Unconfigured-check rule with "Treat a missing Puck Screen row, or one with value `None`/blank/whitespace, as no screen present"; line 48 documents the full parsing contract. `grep -c 'Puck Screen' CLAUDE.md` = 6.
- **Verdict**: PASS

### R14: Safety — never propose a screen as a fix
- **Expected**: ≥1 "never propose / will not suggest" phrase in PUCK_SCREENS.md.
- **Actual**: Line 125 section title "Safety: never propose a screen as a diagnostic fix"; body says "**never propose** installing a puck screen as the answer to a diagnostic problem".
- **Verdict**: PASS

### R15: Honesty — light-roast hedge co-located
- **Expected**: Hedge phrase within 3 lines of a "light roast" mention.
- **Actual**: Line 41: "**Light roasts** — community-reported benefit … This claim is **anecdotal** and **not controlled** — no controlled A/B testing has been located, so the effect size is unverified." Hedge co-located on the same line.
- **Verdict**: PASS

### R16: Honesty — vendor-marketing exclusion
- **Expected**: 0 hits for `22% uniformity|4-7% yield|90% channeling|copper-core` across both files.
- **Actual**: Both files return 0. Reference file's Sources section explicitly excludes vendor marketing.
- **Verdict**: PASS

### R17: Negative-write invariant — no skill writes Puck Screen row of user-setup.md
- **Expected**: None of the four skills contain instructions to write/append/modify the Puck Screen row in user-setup.md.
- **Actual**: All four skills inspected. Consult: only routing references. Diagnose: lines 145–154 only "Scan… for a Puck Screen row" (read). Feedback: line 137 explicitly states "stateless read; do NOT write"; the only "Append a new row" instruction (line 135) targets grind-map.md, not user-setup.md. New-coffee: line 23 only "Conditionally Load" reference (read). No write instructions found.
- **Verdict**: PASS

### R18: user-setup.example.md Notes section with thin + thick examples
- **Expected**: Puck Screen ≥2 mentions; thin AND thick canonical examples.
- **Actual**: 2 mentions (Equipment row + Notes line 55); Notes line 55 includes both `Normcore 58.5mm round-hole (0.8mm thin, 316 stainless)` AND `Pesado Diffuser 58mm mesh (1.7mm thick)`.
- **Verdict**: PASS

### R19: feedback/SKILL.md cold-screen guardrail (R10 equivalent for /feedback)
- **Expected**: ≥1 puck-screen mention; preheat co-located with puck screen mention; adjustment hierarchy preserved as pre-check.
- **Actual**: 6 puck-screen mentions; 1 preheat mention; co-located in the gated guardrail table (line 85). Line 81 explicitly states the cold-screen check is "a pre-check inserted before the existing sour → grind-finer path, NOT a reordering of the adjustment hierarchy above"; lines 70–76 preserve "Grind → Yield → Temp → Pressure → Puck Prep" hierarchy.
- **Verdict**: PASS

### R20: feedback/SKILL.md grind-map writer extends to 12 columns + read-then-append shape
- **Expected**: 12 fields named in order; semantic Y/blank rule; no back-fill of existing 11-col rows; read-then-append preserved (no header/data row mutation).
- **Actual**: Line 135 names all 12 fields in correct order: `Coffee, Roast, Process, Origin, Days Off Roast, Grind, Profile, Ratio, Temp, Rating, Date, Puck Screen?`. Line 137 spells out semantic rule: missing/blank/None → blank cell; any other value → `Y`. Line 140 explicitly states "No back-fill of existing rows. Old 11-column rows … are left untouched". Step 4b lines 134–140 preserve read-then-append shape: step 1 reads, step 2 appends new row to end; "Do NOT touch the header line, the alignment line, or any existing data rows."
- **Verdict**: PASS

### R21: new-coffee/SKILL.md gated PUCK_SCREENS.md load (no parameter change)
- **Expected**: Conditional load gated on Equipment row; grind/temp/ratio recommendations unchanged.
- **Actual**: Lines 19–23 add a "Conditionally Load" table with the trigger explicitly gated: "`user-setup.md` Equipment table has a Puck Screen row with value ≠ `None`"; trailing parenthetical: "informs discussion only — does NOT alter grind/temp/ratio starting recommendations". Step 4 (synthesis logic, lines 64–71) is unchanged from prior shape: temperature from BREWING_BASICS, grind from grind-map/SETTE_270, ratio/pressure from PRESSURE_GUIDE — no puck-screen branching.
- **Verdict**: PASS

### R22: Edge Cases mirrored as user-facing reference
- **Expected**: ≥3 of (missing row | blank value | non-canonical | mesh screen | thick screen | upside-down) documented in PUCK_SCREENS.md.
- **Actual**: PUCK_SCREENS.md "Edge Cases (parsing & handling)" section (lines 131–142) covers all six categories: missing row, blank value, non-canonical value, mesh screen, thick screen, upside-down screen. `grep -ci` returns 14.
- **Verdict**: PASS

## Requirements Drift

**State**: none
**Findings**:
- No requirements/ directory exists; drift assessed against CLAUDE.md and MEMORY.md conventions.
- Single source of truth: PUCK_SCREENS.md §Diagnostic Guardrails is named explicitly as SoT, and both /diagnose and /feedback route to it rather than duplicating wording. Consistent with CLAUDE.md's "Reference these files" pattern.
- Knowledge-file-per-topic: One quick + one deep file (PUCK_SCREENS.md + reference/PUCK_SCREENS_REFERENCE.md), matching every other topic in MEMORY.md SoT table.
- Symlink data architecture preserved: public template `grind-map.example.md` updated to 12 columns; private `grind-map.md` was migrated separately as Task 13. `user-setup.example.md` template defaults to `None`.
- MEMORY.md SoT table received both rows on distinct lines (21, 27) following the one-topic-per-row convention.
- CLAUDE.md got Knowledge Files entry, Unconfigured-check addition, parsing contract, all under Data Architecture as the natural home for these read-side rules.
- Core Rule byte-for-byte preserved (SHA256 match).

**Update needed**: None.

## Stage 2: Code Quality

- **Naming conventions**: Consistent. New file path follows existing pattern (`knowledge/PUCK_SCREENS.md` + `knowledge/reference/PUCK_SCREENS_REFERENCE.md`) matching MEMORY.md SoT table convention. The classification token vocabulary (`thin`, `thick`, `round-hole`, `mesh`) is canonical and used uniformly across PUCK_SCREENS.md, the reference, CLAUDE.md parsing contract, and skills.
- **Pattern consistency**: New skill content uses the existing patterns: "Conditionally Load" table in `/new-coffee` mirrors the same table in `/feedback`; `/consult` routing table row matches the format of all other rows; `/diagnose` and `/feedback` both use a "Puck Screen presence detection" pre-check + gated guardrail table that is structurally parallel between the two skills.
- **Documentation**: Parsing contract in CLAUDE.md is unambiguous: explicit (a)/(b)/(c) cases, case-insensitive substring rules, explicit "do not invent additional categories" guidance. The orthogonality note prevents likely confusion. Forward references in EXTRACTION_SCIENCE.md maintain reader navigation.
- **Adversarial considerations**:
  - Silent-skill-ignore risk for `/new-coffee`: gated load is "Conditionally Load" entry; mitigated because step 1 already reads `user-setup.md`.
  - 11-col/12-col grind-map skew: explicitly addressed in spec Edge Cases and feedback skill ("No back-fill"). User repaired private repo header before any 12-col write occurs in practice.
  - R17's read-only invariant eliminates the lost-write race.
  - Cold-screen misdiagnosis loop closed in both `/feedback` and `/diagnose` (sour-shot entry paths). Ad-hoc conversational diagnosis outside these skills relies on CLAUDE.md parsing contract — acceptable scope.
  - The `grep -c 'PUCK_SCREENS' .claude/skills/consult/SKILL.md` = 1 quirk is a verification-command issue; routing table row correctly cites both files (`grep -o` confirms 2 occurrences).

## Verdict

```json
{"verdict": "APPROVED", "cycle": 1, "issues": [], "requirements_drift": "none"}
```
