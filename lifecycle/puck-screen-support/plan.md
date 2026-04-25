# Plan: puck-screen-support

## Overview

Build knowledge layer first (PUCK_SCREENS.md + reference), then migrate the existing EXTRACTION_SCIENCE row out to it, then propagate references through BASKETS.md, the public templates (user-setup.example.md, grind-map.example.md), the SoT table (MEMORY.md), and the four affected skills (`/consult`, `/diagnose`, `/feedback`, `/new-coffee`). CLAUDE.md is touched last so the captured pre-implementation Core Rule SHA256 (`7976b6a572f2879ef72eb62e7c6ff9b71555ab34ae80807d808292dfcaf8f7ae`) verifies byte-identical preservation per R12.

## Pre-implementation captured state (R12)

- **Captured digest** (Source of Truth): `7976b6a572f2879ef72eb62e7c6ff9b71555ab34ae80807d808292dfcaf8f7ae`. The hex literal in this plan IS the captured state — there is no external snapshot file the verification depends on.
- **Captured block** (two bullet lines between blank lines):
  ```
  - **Sour AND bitter = channeling.** Fix puck prep (WDT, distribution, even tamp) — NOT grind. Grinding finer makes channeling worse.
  - **Turbo shots require 1:2.5-1:3 ratio.** Coarse grind + short contact time needs more water.
  ```
- **Pre-flight verification** (run BEFORE Task 12 begins editing CLAUDE.md): `awk '/Sour AND bitter = channeling/,/^$/' CLAUDE.md | shasum -a 256 | awk '{print $1}'` MUST equal `7976b6a572f2879ef72eb62e7c6ff9b71555ab34ae80807d808292dfcaf8f7ae`. If it doesn't, the digest is stale or the file changed since plan-write — STOP and recapture; do not proceed.
- **Awk-range structural invariant**: the awk range `/Sour AND bitter = channeling/,/^$/` MUST cover BOTH bullets. Verify with `awk '/Sour AND bitter = channeling/,/^$/' CLAUDE.md | grep -c '^- \*\*'` = 2 — if any edit inserts a blank line within the block, this count drops to 1 and the regression is caught even if the SHA256 happens to match a partial extraction.
- **Spec-deviation note**: R12's literal acceptance command `diff <(git show HEAD~1:CLAUDE.md | awk ...) <(awk ... CLAUDE.md)` is replaced by the captured-digest comparison above. Reason: spec form requires CLAUDE.md to be edited in exactly one commit and that commit to be HEAD~1 at verify time; captured-digest form is robust to fix-cycle commit cadence. A `plan_deviation` event recording this substitution is appended to events.log when the plan is approved.
- **Commit-cadence guidance** (advisory, not blocking): Task 12 SHOULD land all CLAUDE.md edits in one commit. If a fix-cycle creates additional CLAUDE.md commits, the captured-digest verification still works (stateless on git history); only the spec-literal R12 form would fail.

## Tasks

### Task 1: Create `knowledge/PUCK_SCREENS.md` (quick-ref + classification dispatcher)

- **Files**: `knowledge/PUCK_SCREENS.md` (new)
- **What**: Author the quick-ref knowledge file with classification dispatcher (thin/thick × round-hole/mesh), four required behavior sections, hedged light-roast claim, safety/never-propose statement, edge-case documentation, and pointer to the deep reference. Satisfies R2, R14, R15, R16, R22.
- **Depends on**: none
- **Complexity**: complex
- **Context**:
  - Sibling structural pattern to follow: `knowledge/BASKETS.md` (quick-ref ~100 lines; sections like "Dose = Basket Size", "Common Headroom Issues") and `knowledge/PRESSURE_GUIDE.md` (top-of-file matrix → quick-ref guidance → "See reference" pointer).
  - **Required top-level sections** (`## ` headings):
    1. `## Screen Classification` — names BOTH thickness tokens (`thin ≤ 1mm`, `thick > 1mm`) AND BOTH hole-type tokens (`round-hole`, `mesh`). Each downstream section labels its applicability with these tokens.
    2. `## When to Use` — mention light roasts with the explicit hedge tokens from R15 (`community-reported`, `not controlled`, or `anecdotal`/`unverified`/`no controlled`); the hedge phrase MUST be within 3 lines of any "light roast" mention (R15 colocation acceptance).
    3. `## Effects on Extraction` — covers channeling-reduction (shower-screen-driven only, NOT puck-prep-driven), heat-buffer note (defer numerics to reference file), pre-infusion qualitative note. **Excludes** vendor-marketing numbers (R16 prohibits `22% uniformity`, `4-7% yield`, `4-7% yield`, `90% channeling`, `copper-core`).
    4. `## Common Pitfalls` — cold screen → sour, over-dosing → choke/bent, upside-down/wrong-size/bent screen orientation, oil retention on mesh, diminishing returns. Include the "Protects puck from shower screen imprint" phrase (migration target from R4 — `grep -c 'Protects puck from shower screen imprint' knowledge/PUCK_SCREENS.md` ≥ 1).
    5. `## Cleaning & Maintenance` — daily rinse, weekly Cafiza, mesh-vs-round-hole cleaning cadence difference.
    6. `## Diagnostic Guardrails` — **Single Source of Truth** for skill-side guardrails. Two named sub-sections:
       - **Cold-Screen Sour Guardrail** — when a shot tastes sour AND a puck screen is installed, ASK about preheat discipline before recommending a grind-finer adjustment. Cold metal pulls heat from the surface; preheat fixes the cause, grinding finer makes it worse. Skills (`/diagnose`, `/feedback`) reference this section by name; they do NOT carry their own copy of the wording.
       - **Channeling-Nuance Note** — when diagnosing sour+bitter with a puck screen present, remaining channeling is **likely** (NOT "almost certainly") puck-prep-driven, BECAUSE shower-screen-driven channeling is already mitigated by the screen. EXCEPT when the screen itself could be misaligned (upside-down, wrong size, bent) — verify orientation/fit first. Recommendation remains "fix puck prep, NOT grind" per CLAUDE.md Core Rule. Skills referencing this guardrail get both the nuance and the screen-orientation check.
    7. **Safety statement** (R14): explicit sentence using one of these phrases — `never propose`, `do not propose`, `will not suggest`, `never suggest` — that the agent will not recommend installing a puck screen as a diagnostic action.
    8. **Edge cases section** (R22): documents at least three of {missing row, blank value, non-canonical value, mesh screen, thick screen, upside-down screen}. Acceptance: `grep -ci 'missing.*row\|blank.*value\|non[- ]canonical\|mesh.*screen\|thick.*screen\|upside[- ]down' knowledge/PUCK_SCREENS.md` ≥ 3.
    9. Reference pointer: `See reference for deep physics:` linking to `reference/PUCK_SCREENS_REFERENCE.md`.
  - Source material is in `lifecycle/puck-screen-support/research.md` §Web Research (lines 50–101). Use the qualitative claims; reject the vendor-marketing numbers explicitly listed at lines 96–100.
  - Canonical tokens from spec Technical Constraints: `None`, `thin`, `thick`, `round-hole`, `mesh`. Substring-match case-insensitively.
- **Verification**:
  - `test -f knowledge/PUCK_SCREENS.md && echo OK` — pass if "OK".
  - `grep -c 'thin ≤ 1mm\|thin (≤ 1mm)\|thin (≤1mm)' knowledge/PUCK_SCREENS.md` ≥ 1 — pass if count ≥ 1 (R2).
  - `grep -c 'thick > 1mm\|thick (> 1mm)\|thick (>1mm)' knowledge/PUCK_SCREENS.md` ≥ 1 — pass if count ≥ 1 (R2).
  - `grep -c 'round-hole' knowledge/PUCK_SCREENS.md` ≥ 2 — pass if count ≥ 2 (R2).
  - `grep -c 'mesh' knowledge/PUCK_SCREENS.md` ≥ 2 — pass if count ≥ 2 (R2).
  - `grep -ci 'never propose\|do not propose\|will not suggest\|never suggest' knowledge/PUCK_SCREENS.md` ≥ 1 — pass if ≥ 1 (R14).
  - `grep -ci 'community-reported\|not controlled\|anecdotal\|unverified\|no controlled' knowledge/PUCK_SCREENS.md` ≥ 1 — pass if ≥ 1 (R15).
  - `grep -B3 -A3 -i 'light roast' knowledge/PUCK_SCREENS.md | grep -ci 'community-reported\|not controlled\|anecdotal\|unverified\|no controlled'` ≥ 1 — pass if ≥ 1 (R15 colocation).
  - `grep -Ec '22% uniformity|4-7% yield|4[–-]7% yield|90% channeling|copper-core' knowledge/PUCK_SCREENS.md` = 0 — pass if 0 (R16).
  - `grep -ci 'missing.*row\|blank.*value\|non[- ]canonical\|mesh.*screen\|thick.*screen\|upside[- ]down' knowledge/PUCK_SCREENS.md` ≥ 3 — pass if ≥ 3 (R22).
  - `grep -c '## Screen Classification\|## When to Use\|## Effects on Extraction\|## Common Pitfalls\|## Cleaning\|## Diagnostic Guardrails' knowledge/PUCK_SCREENS.md` ≥ 6 — pass if ≥ 6 (six required top-level sections including Diagnostic Guardrails).
  - Diagnostic Guardrails section has both named sub-sections: `grep -ci 'Cold-Screen Sour Guardrail\|cold.screen.*guardrail' knowledge/PUCK_SCREENS.md` ≥ 1 AND `grep -ci 'Channeling-Nuance Note\|channeling.nuance' knowledge/PUCK_SCREENS.md` ≥ 1 — pass if both ≥ 1.
  - Cold-Screen Guardrail content: `grep -ci 'preheat' knowledge/PUCK_SCREENS.md` ≥ 1 AND `grep -B5 -A5 -i 'cold.screen.*guardrail' knowledge/PUCK_SCREENS.md | grep -ci 'preheat'` ≥ 1 — pass if both hold (preheat appears within 5 lines of the guardrail heading).
  - Channeling-Nuance content: `grep -ci 'upside.down\|wrong size\|bent.*screen\|screen.*orientation' knowledge/PUCK_SCREENS.md` ≥ 1 AND `grep -ci 'shower.screen.driven\|prep.driven\|puck.prep.driven' knowledge/PUCK_SCREENS.md` ≥ 2 — pass if both hold.
- **Status**: [x] complete (commit b2dd305)

### Task 2: Create `knowledge/reference/PUCK_SCREENS_REFERENCE.md` (deep with temperature-compensation table)

- **Files**: `knowledge/reference/PUCK_SCREENS_REFERENCE.md` (new)
- **What**: Author the deep-reference companion to PUCK_SCREENS.md owning the temperature-compensation numerics (the +1°C unpreheated-thin and +2–3°C thick claims) and heat-buffer physics. Satisfies R3, R16.
- **Depends on**: none
- **Complexity**: simple
- **Context**:
  - Sibling structural pattern: `knowledge/reference/BASKETS_REFERENCE.md` and `knowledge/reference/PRESSURE_REFERENCE.md` — long-form prose, deeper physics, often a numeric table the quick file references but does not duplicate.
  - **Required content** (R3):
    - Top-level section on heat-buffer physics covering why screens steal energy from the puck surface (water cooling on contact with a cold metal surface).
    - A table or labelled section on temperature compensation by thickness class. Must contain BOTH `+1°C` (or `+1 °C`/`+1C`) for thin-unpreheated AND a `+2–3°C` (or `+2-3°C`/`+2 to 3°C`) for thick.
    - File length ≥ 60 lines (`wc -l` ≥ 60).
  - Source: `research.md` lines 53–58 (temperature evidence) and §Adversarial Review item 11 (device-spec drift — only thickness class matters for behavior).
  - **Excludes** vendor-marketing numbers per R16 (`22% uniformity`, `4-7% yield`, `90% channeling`, `copper-core`).
- **Verification**:
  - `test -f knowledge/reference/PUCK_SCREENS_REFERENCE.md && echo OK` — pass if "OK".
  - `wc -l < knowledge/reference/PUCK_SCREENS_REFERENCE.md` ≥ 60 — pass if ≥ 60 (R3).
  - `grep -c '+1°C\|+1 °C\|+1C' knowledge/reference/PUCK_SCREENS_REFERENCE.md` ≥ 1 — pass if ≥ 1 (R3).
  - `grep -Ec '\+2[–-]3°C|\+2[–-]3 °C|\+2 to 3°C' knowledge/reference/PUCK_SCREENS_REFERENCE.md` ≥ 1 — pass if ≥ 1 (R3).
  - `grep -Ec '22% uniformity|4-7% yield|4[–-]7% yield|90% channeling|copper-core' knowledge/reference/PUCK_SCREENS_REFERENCE.md` = 0 — pass if 0 (R16).
  - `grep -ci 'heat.?buffer\|heat sink\|thermal mass\|energy.*surface\|cooling.*contact' knowledge/reference/PUCK_SCREENS_REFERENCE.md` ≥ 1 — pass if ≥ 1 (heat-buffer-physics section).
- **Status**: [x] complete (commit ef95fc0)

### Task 3: Migrate `knowledge/EXTRACTION_SCIENCE.md:42` row to stub + update line-44 forward reference

- **Files**: `knowledge/EXTRACTION_SCIENCE.md`
- **What**: Replace the line-42 Puck Prep Tools table row's pros/cons with a stub linking to `PUCK_SCREENS.md`, and add an inline `PUCK_SCREENS.md` reference to the line-44 "Recommended combo" line. The original "Protects puck from shower screen imprint" phrase already lives in PUCK_SCREENS.md (Task 1). Satisfies R4.
- **Depends on**: [1]
- **Complexity**: simple
- **Context**:
  - Current line 42: `| **Puck screen on top** | Protects puck from shower screen imprint, prevents surface erosion | Doesn't improve internal distribution |`
  - Required new line 42 (exact format per R4): `| **Puck screen on top** | See [PUCK_SCREENS.md](PUCK_SCREENS.md) | — |`
  - Current line 44: `**Recommended combo:** WDT → light tap to settle → tamp → (optional: puck screen on top)`
  - Required new line 44: append an inline `PUCK_SCREENS.md` reference (e.g., `**Recommended combo:** WDT → light tap to settle → tamp → (optional: puck screen on top — see [PUCK_SCREENS.md](PUCK_SCREENS.md))`).
  - The original phrase "Protects puck from shower screen imprint" must NOT remain in EXTRACTION_SCIENCE.md (R4 migration-out acceptance) — it was already migrated into PUCK_SCREENS.md by Task 1.
  - Pattern to follow: existing 3-column table row format with `**Tool**` column, two narrative columns, `|` delimiters.
- **Verification**:
  - `grep -c 'Protects puck from shower screen imprint' knowledge/EXTRACTION_SCIENCE.md` = 0 — pass if = 0 (R4 migration-out).
  - `grep -E '^\| \*\*Puck screen on top\*\* \| See \[PUCK_SCREENS\.md\]\(PUCK_SCREENS\.md\) \| — \|' knowledge/EXTRACTION_SCIENCE.md | wc -l` = 1 — pass if = 1 (R4 exact-row).
  - `grep -A0 'Recommended combo' knowledge/EXTRACTION_SCIENCE.md | grep -c 'PUCK_SCREENS'` ≥ 1 — pass if ≥ 1 (R4 line-44).
- **Status**: [x] complete (commit c8cad8d)

### Task 4: Add masking note to `knowledge/BASKETS.md` adjacent to existing mesh-imprint rule

- **Files**: `knowledge/BASKETS.md`
- **What**: Append a one-sentence note adjacent to the existing line-16 rule stating that the mesh-imprint dose-headroom evidence is MASKED when a puck screen is installed; recommend flow behavior / measured headroom as alternatives. Satisfies R5.
- **Depends on**: [1]
- **Complexity**: simple
- **Context**:
  - Current line 16: `**How to check headroom:** After pulling a shot, look at the top of the puck. It should be flat and smooth, with no screen imprint. If you see a mesh pattern pressed into the surface, reduce your dose by 0.5g.`
  - Both the "mesh pattern pressed into the surface" phrase AND the "reduce your dose by 0.5g" phrase must be preserved verbatim (R5 preservation acceptance).
  - The masking note must use one of: `mask(ed|s)` or `hide[sn]` (R5 content acceptance), and reference `puck screen` (R5 content acceptance).
  - The note must be in the same paragraph as the existing rule, OR the immediately adjacent paragraph (R5 proximity — verified by reading the diff). Recommended: append a new sentence to the existing paragraph, e.g., `If you have a puck screen installed, this check is masked — rely on flow behavior and measured headroom instead.`
  - Pattern reference: `knowledge/BASKETS.md` uses prose paragraphs separated by blank lines; bold-labelled sentences are common.
- **Verification**:
  - `grep -c 'puck screen' knowledge/BASKETS.md` ≥ 1 — pass if ≥ 1 (R5).
  - `grep -Ec 'mask(ed|s)|hide[sn]' knowledge/BASKETS.md` ≥ 1 — pass if ≥ 1 (R5).
  - `grep -c 'mesh pattern pressed into the surface' knowledge/BASKETS.md` = 1 — pass if = 1 (R5 preservation).
  - `grep -c 'reduce your dose by 0.5g' knowledge/BASKETS.md` = 1 — pass if = 1 (R5 preservation).
  - Interactive/session-dependent: paragraph proximity is judged by reading the diff in the review phase; no command reliably parses markdown paragraph adjacency.
- **Status**: [x] complete (commit 7678ae2)

### Task 5: Update `user-setup.example.md` Equipment table + Notes section

- **Files**: `user-setup.example.md`
- **What**: Add an optional `**Puck Screen**` row to the Equipment table with default `None`; add Notes-section documentation showing thin and thick canonical examples. Satisfies R1, R18.
- **Depends on**: none
- **Complexity**: simple
- **Context**:
  - Current Equipment table (lines 5–10) has rows: Machine, Grinder, Basket, Scale.
  - New row to add at end of table (R1): `| **Puck Screen** | None |`
  - Notes section (R18): document the field is optional, with examples showing at least one `thin` and one `thick` variant. Use the canonical examples from spec Technical Constraints:
    - Thin: `Normcore 58.5mm round-hole (0.8mm thin, 316 stainless)`
    - Thick: `Pesado Diffuser 58mm mesh (1.7mm thick)`
  - Pattern: existing Notes section already uses bullet entries with bold labels. Add a new bullet, e.g., `**Puck Screen (optional):** Default is "None" — leave as-is if you don't use one. Otherwise, fill in product details. Examples: …`.
  - `user-setup.example.md` is the public template; this row will appear in every fresh checkout — keep it minimal and self-explanatory.
- **Verification**:
  - `grep -c '^| \*\*Puck Screen\*\*' user-setup.example.md` = 1 — pass if = 1 (R1).
  - `grep -c '^| \*\*Puck Screen\*\* | None |' user-setup.example.md` = 1 — pass if = 1 (R1).
  - `grep -c 'Puck Screen' user-setup.example.md` ≥ 2 — pass if ≥ 2 (R18).
  - `grep -Eci 'thin|0\.8mm|≤ 1mm' user-setup.example.md` ≥ 1 — pass if ≥ 1 (R18).
  - `grep -Eci 'thick|1\.7mm|> 1mm' user-setup.example.md` ≥ 1 — pass if ≥ 1 (R18).
- **Status**: [x] complete (commit ad2972d)

### Task 6: Add `Puck Screen?` column + semantic-contract comment to `grind-map.example.md`

- **Files**: `grind-map.example.md`
- **What**: Add a 12th column "Puck Screen?" to the shot-history table header and example row; add a semantic-contract comment that blank means "unknown", explicitly NOT "no screen". Satisfies R6, R7.
- **Depends on**: none
- **Complexity**: simple
- **Context**:
  - Current header (line 7): `| Coffee | Roast | Process | Origin | Days Off Roast | Grind | Profile | Ratio | Temp | Rating | Date |` — 11 columns.
  - Current alignment row (line 8): `|--------|-------|---------|--------|----------------|-------|---------|-------|------|--------|------|`
  - Current example row (line 9): `| Example Roaster Ethiopia Yirgacheffe | Light | Washed | Ethiopia | 21 | 13C | Bloom Slide | 1:2.5 | 94°C | 5 | Jan 15 |`
  - **R6 requirement**: 12 fields. New header gains `| Puck Screen? |` at the end; new alignment cell `|--------------|` at the end; example row gains a 12th cell (suggested: blank — to demonstrate the "unknown" semantic).
  - **R6 awk acceptance** counts `NF` from `awk -F'|'` on row 9 = 14 (12 fields + 2 outer-edge empty fields from leading/trailing pipes). To get NF=14, the row must look like `| field1 | field2 | … | field12 |` — the leading and trailing pipes are required.
  - **R7 semantic-contract comment**: a markdown comment or italic line documenting the contract. The comment must contain BOTH:
    - Positive phrase matching `grep -ci 'blank.*unknown\|unknown.*blank'` ≥ 1
    - Contrast phrase matching `grep -Eci 'NOT.*\"?N\"?|not.*no screen|not.*absence'` ≥ 1
  - Suggested wording: `*Puck Screen? — "Y" if a screen was installed, blank if unknown. Blank is NOT "no screen" — use "N" to record explicit absence; this distinction matters because new rows from /feedback are blank-as-unknown for back-compat.*`
  - The existing italic line (line 11) about "Days Off Roast is optional—use \"—\"" provides the pattern.
- **Verification**:
  - `head -n 8 grind-map.example.md | grep -c 'Puck Screen?'` ≥ 1 — pass if ≥ 1 (R6 header).
  - `awk -F'|' 'NR==9 {print NF}' grind-map.example.md` = 14 — pass if = 14 (R6 example row width).
  - `grep -ci 'blank.*unknown\|unknown.*blank' grind-map.example.md` ≥ 1 — pass if ≥ 1 (R7 positive phrase).
  - `grep -Eci 'NOT.*\"?N\"?|not.*no screen|not.*absence' grind-map.example.md` ≥ 1 — pass if ≥ 1 (R7 contrast phrase).
- **Status**: [x] complete (commit 7c4fd30)

### Task 7: Update MEMORY.md SoT table — two distinct rows

- **Files**: `~/.claude/projects/-Users-charlie-hall-Workspaces-gaggimate-barista/memory/MEMORY.md` (resolves to `/Users/charlie.hall/.claude/projects/-Users-charlie-hall-Workspaces-gaggimate-barista/memory/MEMORY.md`)
- **What**: Add two distinct rows to the "Architecture: Single Source of Truth" table — one for `knowledge/PUCK_SCREENS.md` (quick-ref) and one for `knowledge/reference/PUCK_SCREENS_REFERENCE.md` (deep). Satisfies R8.
- **Depends on**: [1, 2]
- **Complexity**: simple
- **Context**:
  - Existing pattern: each topic has TWO rows in the table — quick file and deep reference. Examples: `Milk science & drinks` → `knowledge/MILK_AND_DRINKS.md`; `Milk & drinks (deep)` → `knowledge/reference/MILK_AND_DRINKS_REFERENCE.md`.
  - **Required new rows** (suggested labels):
    - `| Puck screens (quick) | knowledge/PUCK_SCREENS.md |`
    - `| Puck screens (deep) | knowledge/reference/PUCK_SCREENS_REFERENCE.md |`
  - Insert near existing Baskets / Milk / Pressure rows for topical proximity, but exact placement is editorial.
  - **R8 critically requires the two file paths on different lines** — never collapse to a single row with both files.
- **Verification**:
  - `grep -c '| .* | knowledge/PUCK_SCREENS\.md |' /Users/charlie.hall/.claude/projects/-Users-charlie-hall-Workspaces-gaggimate-barista/memory/MEMORY.md` = 1 — pass if = 1 (R8 row 1).
  - `grep -c '| .* | knowledge/reference/PUCK_SCREENS_REFERENCE\.md |' /Users/charlie.hall/.claude/projects/-Users-charlie-hall-Workspaces-gaggimate-barista/memory/MEMORY.md` = 1 — pass if = 1 (R8 row 2).
  - `grep -n 'PUCK_SCREENS' /Users/charlie.hall/.claude/projects/-Users-charlie-hall-Workspaces-gaggimate-barista/memory/MEMORY.md | awk -F: '{print $1}' | sort -u | wc -l` ≥ 2 — pass if ≥ 2 (R8 distinct lines).
- **Status**: [x] complete (no commit — MEMORY.md outside repo)

### Task 8: Update `.claude/skills/consult/SKILL.md` routing table

- **Files**: `.claude/skills/consult/SKILL.md`
- **What**: Add a routing-table row mapping puck-screen keywords to PUCK_SCREENS.md (primary) + PUCK_SCREENS_REFERENCE.md (deep). Satisfies R9.
- **Depends on**: [1, 2]
- **Complexity**: simple
- **Context**:
  - Existing routing table starts ~line 21. Format example (line 29): `| sour, bitter, taste, flavor, tasting | \`knowledge/ESPRESSO_TASTING_GUIDE.md\` | \`knowledge/ESPRESSO_BREWING_BASICS.md\` |`
  - Three columns: keywords | primary file (quick) | deep reference.
  - **Required new row** (suggested keywords): `| puck screen, normcore, screen imprint, screen orientation | \`knowledge/PUCK_SCREENS.md\` | \`knowledge/reference/PUCK_SCREENS_REFERENCE.md\` |`
  - Insert in the existing table block; column alignment mirroring sibling rows.
  - **No skill behavior changes** beyond the routing addition — `/consult`'s cascade-prevention rule (max 1 quick + 1 deep) is unchanged.
- **Verification**:
  - `grep -c 'puck screen' .claude/skills/consult/SKILL.md` ≥ 1 — pass if ≥ 1 (R9).
  - `grep -c 'PUCK_SCREENS' .claude/skills/consult/SKILL.md` ≥ 2 — pass if ≥ 2 (R9 — both quick and reference cited).
  - Interactive/session-dependent: confirming the new row sits inside the routing table block (not elsewhere in the file) is by reading the modified SKILL.md; line-anchored regex would drift on edits.
- **Status**: [x] complete (commit 79748b0)

### Task 9: Update `.claude/skills/diagnose/SKILL.md` — reference cold-screen guardrail + channeling-nuance from PUCK_SCREENS.md

- **Files**: `.claude/skills/diagnose/SKILL.md`
- **What**: Modify the CORRELATE Taste with Telemetry section to (a) add a Puck-Screen-presence detection step and (b) reference `knowledge/PUCK_SCREENS.md` §Diagnostic Guardrails for both the cold-screen sour guardrail (R10) and the channeling-nuance note (R11). The skill does NOT carry its own copy of the guardrail wording — it routes to PUCK_SCREENS.md as the Single Source of Truth. The Core Rule recommendation ("fix puck prep, NOT grind") is preserved verbatim. Satisfies R10, R11.
- **Depends on**: [1]
- **Complexity**: simple
- **Context**:
  - CORRELATE section starts at `.claude/skills/diagnose/SKILL.md:139` (`### 3. CORRELATE Taste with Telemetry`).
  - **Equipment-table read pattern**: existing skills already read user-setup.md statelessly (per research §Existing patterns #3). The skill scans the Equipment table for the Puck Screen row; treats a missing row, blank value, or value 'None' (case-insensitive) as no screen present per CLAUDE.md parsing contract.
  - **Required additions** (both gate on screen present):
    - When taste = sour AND screen present: load `knowledge/PUCK_SCREENS.md` §Diagnostic Guardrails → Cold-Screen Sour Guardrail; apply preheat-check before grind-finer recommendation. Reference must use the substring `PUCK_SCREENS.md` and surface "preheat" near the conditional.
    - When taste = sour+bitter AND screen present: load `knowledge/PUCK_SCREENS.md` §Diagnostic Guardrails → Channeling-Nuance Note; apply the prep-driven-vs-misaligned distinction. Reference must use the substring `PUCK_SCREENS.md` and surface a misaligned-screen token near the conditional.
  - **No reordering of the diagnostic hierarchy**: cold-screen check is a pre-check inserted before the existing sour → grind-finer path, NOT a replacement.
  - **Why reference instead of duplicate**: spec Technical Constraints invoke Single Source of Truth; PUCK_SCREENS.md (Task 1) owns the guardrail wording. Future updates to the guardrail edit ONE file (PUCK_SCREENS.md), not two.
- **Verification**:
  - `grep -ci 'puck screen' .claude/skills/diagnose/SKILL.md` ≥ 2 — pass if ≥ 2 (R10 token; one for the conditional read, one for the guardrail invocation).
  - `grep -c 'PUCK_SCREENS' .claude/skills/diagnose/SKILL.md` ≥ 2 — pass if ≥ 2 (knowledge-file references for cold-screen + channeling-nuance, not duplicated wording).
  - `grep -ci 'preheat' .claude/skills/diagnose/SKILL.md` ≥ 1 — pass if ≥ 1 (R10 surfaced near the conditional).
  - `grep -B5 -A5 -i 'preheat' .claude/skills/diagnose/SKILL.md | grep -ci 'puck screen\|PUCK_SCREENS'` ≥ 1 — pass if ≥ 1 (R10 colocation).
  - `grep -ci 'upside[- ]down\|wrong size\|bent.*screen\|screen.*orientation' .claude/skills/diagnose/SKILL.md` ≥ 1 — pass if ≥ 1 (R11 misaligned-screen flag surfaced).
  - **R11 distinction tokens via reference** (relaxed from spec literal because the guardrail wording lives in PUCK_SCREENS.md): `grep -ci 'puck.?prep.?driven\|prep-driven\|shower.?screen.?driven\|channeling.nuance\|PUCK_SCREENS.md.*Channeling\|Channeling.*PUCK_SCREENS' .claude/skills/diagnose/SKILL.md` ≥ 1 — pass if ≥ 1 (the skill either inlines a distinction token OR references PUCK_SCREENS.md's Channeling-Nuance section by name; spec R11's strict ≥2 in-skill mentions is satisfied by PUCK_SCREENS.md content via the routing reference). This is a documented spec deviation logged in events.log.
- **Status**: [x] complete (commit 35a8597)

### Task 10: Update `.claude/skills/feedback/SKILL.md` — sour-shot guardrail + channeling-nuance reference + 12-column grind-map writer

- **Files**: `.claude/skills/feedback/SKILL.md`
- **What**: (a) Add a Puck-Screen-presence detection step and reference `knowledge/PUCK_SCREENS.md` §Diagnostic Guardrails for both the cold-screen sour guardrail (R19) and the channeling-nuance note (R11 extended to /feedback per spec-internal-consistency: spec.md:9 establishes /feedback as primary sour-shot entry path); (b) extend the grind-map writer to 12 columns populating "Puck Screen?" from the user-setup Equipment table, with semantic blank-when-None / "Y"-when-present, no DATA back-fill of existing rows (R20). Satisfies R19, R20, plus extending R11 to /feedback.
- **Depends on**: [1, 6]
- **Complexity**: complex
- **Context**:
  - **R19 (sour-shot guardrail)**: when user reports sour AND Equipment shows Puck Screen ≠ `None`, load `knowledge/PUCK_SCREENS.md` §Diagnostic Guardrails → Cold-Screen Sour Guardrail and check preheat discipline BEFORE recommending grind-finer.
    - Adjustment hierarchy (`Grind → Yield → Temp → Pressure → Puck Prep`) preserved as ordering — guardrail is a pre-check, NOT a reordering.
    - The skill references PUCK_SCREENS.md by name; it does NOT carry its own copy of the guardrail wording (Single Source of Truth — same architectural move as R4's EXTRACTION_SCIENCE.md → PUCK_SCREENS.md migration, applied consistently in this change set).
  - **R11 extension (channeling-nuance, applied to /feedback by spec-internal consistency)**: when user reports sour+bitter AND Equipment shows Puck Screen ≠ `None`, load `knowledge/PUCK_SCREENS.md` §Diagnostic Guardrails → Channeling-Nuance Note. Apply the prep-driven-vs-misaligned distinction. Recommendation remains "fix puck prep, NOT grind" per CLAUDE.md Core Rule. The existing `/feedback` SKILL.md:86 sour+bitter rule is preserved; the screen-orientation pre-check is added before the existing puck-prep recommendation.
    - **Why this is in the plan even though spec R19 doesn't literally mandate it**: spec.md:9 already established "/feedback is the primary sour-shot entry path" as the rationale for extending R19 to /feedback. Applying that same logic to R11 is consistency, not scope expansion. Logged as a deliberate spec extension in events.log.
  - **R20 (12-column grind-map writer)**: feedback skill writes grind-map rows. Currently writes 11 columns (matching `grind-map.example.md` pre-Task-6 structure). Extend to 12 columns: `Coffee, Roast, Process, Origin, Days Off Roast, Grind, Profile, Ratio, Temp, Rating, Date, Puck Screen?`.
    - Semantic: missing row OR value = `None` (case-insensitive) OR whitespace → write blank cell. Any other value → write `Y`.
    - **No data back-fill** of existing rows in private `grind-map.md` — only new rows are written 12-column. Old rows' missing 12th cell parses as blank under markdown-table semantics → "unknown" per R7's contract. (Header is migrated separately by Task 13; not this task's concern.)
    - Existing grind-map writer is at `.claude/skills/feedback/SKILL.md:114` (`#### 4b. Grind Map → grind-map.md`) and following.
    - **MECHANISM CONTRACT (load-bearing — do not paraphrase away)**: the existing writer is read-then-append. Step 1 reads `grind-map.md`; step 2 appends ONE new row at the end. This task MUST preserve that shape:
      - The header line MUST NOT be touched by `/feedback`. (Task 13 migrates the header during implementation; after that, the schema is 12-col and the writer just appends 12-col rows.)
      - The alignment line MUST NOT be touched by `/feedback`.
      - Existing data rows MUST NOT be touched by `/feedback`.
      - The 12-column row is appended ONLY to the end of the file.
      - The skill MUST NOT contain any phrase like "rewrite the table", "update the header", "migrate the file", or any step that issues a write to lines 1..N where N is the existing row count. Schema migration is owned by Task 13, not the runtime writer.
  - **Fixture-based runtime verification (REQUIRED — captures the catastrophic-rewrite failure mode that prose-reading cannot)**:
    1. Create `/tmp/test-grind-map-fixture.md` containing a 6-line 12-column grind-map (header + alignment + 4 data rows; some rows can be 11-col data under the 12-col header to mimic the post-Task-13 state where old rows lack the 12th cell).
    2. SHA256 the fixture's first 5 lines (header through last existing data row): `head -n 5 /tmp/test-grind-map-fixture.md | shasum -a 256` — record digest as `FIXTURE_PRE_DIGEST`.
    3. Mentally walk through the modified `/feedback` SKILL.md writer instructions step-by-step against the fixture path: identify each line the writer would emit. Assert: the writer emits ONE new line and that line appears AFTER the existing 5 lines.
    4. Post-walkthrough digest: `head -n 5 /tmp/test-grind-map-fixture.md | shasum -a 256` MUST equal `FIXTURE_PRE_DIGEST` (file untouched by walkthrough — sanity check).
    5. The walkthrough's emit-list MUST contain exactly one new line (the appended row). If the walkthrough yields 2+ new emits or modifies existing lines, the writer instructions are wrong.
    6. Cleanup: `rm /tmp/test-grind-map-fixture.md`.
  - **Equipment-table read pattern**: same stateless read as Task 9.
  - **No write to user-setup.md Puck Screen row** (R17 negative-write invariant) — skill only reads.
- **Verification**:
  - `grep -ci 'puck screen' .claude/skills/feedback/SKILL.md` ≥ 1 — pass if ≥ 1 (R19/R20 token).
  - `grep -c 'PUCK_SCREENS' .claude/skills/feedback/SKILL.md` ≥ 2 — pass if ≥ 2 (knowledge-file references for cold-screen + channeling-nuance, not duplicated wording).
  - R19 guardrail: `grep -B5 -A5 -i 'preheat' .claude/skills/feedback/SKILL.md | grep -ci 'puck screen\|PUCK_SCREENS'` ≥ 1 OR (`grep -ci 'preheat' .claude/skills/feedback/SKILL.md` ≥ 1 AND `grep -ci 'cold.*screen\|screen.*cold' .claude/skills/feedback/SKILL.md` ≥ 1) — pass if either alternative holds (R19).
  - R11-extended (channeling-nuance for sour+bitter on /feedback): `grep -ci 'upside[- ]down\|wrong size\|bent.*screen\|screen.*orientation\|Channeling-Nuance' .claude/skills/feedback/SKILL.md` ≥ 1 — pass if ≥ 1 (the skill surfaces the misaligned-screen flag OR references the named PUCK_SCREENS.md sub-section).
  - R20 column header in writer: `grep -c 'Puck Screen?\|Puck Screen\?' .claude/skills/feedback/SKILL.md` ≥ 1 — pass if ≥ 1.
  - R20 12-field column list: `grep -c 'Coffee, Roast, Process, Origin, Days Off Roast, Grind, Profile, Ratio, Temp, Rating, Date, Puck Screen?' .claude/skills/feedback/SKILL.md` ≥ 1 OR equivalent ordered enumeration — Interactive/session-dependent: ordered enumeration may be presented as a numbered list across multiple lines; verification confirms the 12 names in order by reading the modified writer section.
  - R20 mechanism preservation (positive check): `grep -ci 'append.*end\|append.*new row\|append a new row' .claude/skills/feedback/SKILL.md` ≥ 1 — pass if ≥ 1 (writer instructions retain explicit append-only language).
  - R20 mechanism preservation (negative check): `grep -Eci 'rewrite.*table|rewrite.*header|migrate.*grind-map|update.*header.*column' .claude/skills/feedback/SKILL.md` = 0 — pass if = 0 (no instructions to rewrite or migrate existing file content; "back-fill" is intentionally NOT in this negative grep because the skill may legitimately reference R20's "no back-fill" rule by name).
  - R20 fixture walkthrough: completed per the fixture-based runtime verification steps in Context above; emit-count = 1 and pre/post fixture digests match — pass if both hold.
- **Status**: [x] complete (commit c791756)

### Task 11: Update `.claude/skills/new-coffee/SKILL.md` — conditional-load hook for PUCK_SCREENS.md

- **Files**: `.claude/skills/new-coffee/SKILL.md`
- **What**: Add a conditional-load entry that loads `knowledge/PUCK_SCREENS.md` when the user-setup Equipment table shows a Puck Screen row with value ≠ `None`. The load is gated on row presence, NOT always-loaded, and does NOT alter the skill's grind/temp/ratio starting recommendations. Satisfies R21.
- **Depends on**: [1]
- **Complexity**: simple
- **Context**:
  - Pattern reference: `.claude/skills/feedback/SKILL.md:24` (`## Conditionally Load`) — table format with trigger column.
  - `/new-coffee` does NOT currently have a `Conditionally Load` section. Add one (or extend existing context-loading instructions) following feedback's pattern: a new bullet/row stating "load `knowledge/PUCK_SCREENS.md` when the Equipment table's Puck Screen row is present with value ≠ `None`".
  - **No parameter logic changes** (R21): grind/temp/ratio starting recommendations flow from roast + processing + origin only, as today. The knowledge file informs discussion only.
  - Equipment-table read pattern: same stateless read as Tasks 9/10.
- **Verification**:
  - `grep -c 'PUCK_SCREENS' .claude/skills/new-coffee/SKILL.md` ≥ 1 — pass if ≥ 1 (R21).
  - `grep -ci 'puck screen' .claude/skills/new-coffee/SKILL.md` ≥ 1 — pass if ≥ 1 (R21).
  - Interactive/session-dependent: confirming "gated on Equipment-row presence (not always-loaded)" and "no parameter logic changes" is by reading the modified SKILL.md — natural-language behavior verification.
- **Status**: [x] complete (commit ad6aa7d)

### Task 12: Update CLAUDE.md — Knowledge Files list, Unconfigured-check Puck Screen field, parsing contract

- **Files**: `/Users/charlie.hall/Workspaces/gaggimate-barista/CLAUDE.md`
- **What**: (a) Add `PUCK_SCREENS.md` to the Knowledge Files list (line 18 area); (b) extend the Unconfigured check (line 45) with Puck-Screen-field handling and a clarifying note that field state is orthogonal to template detection; (c) document the parsing contract for the Puck Screen field. The Core Rule "Sour AND bitter = channeling..." block (line 132 area) is preserved byte-for-byte. Satisfies R12, R13.
- **Depends on**: [1, 2]
- **Complexity**: complex
- **Context**:
  - **R13a (Knowledge Files list)**: add `- \`PUCK_SCREENS.md\` - …` to the existing list at line 18 area. Brief description of contents.
  - **R13b (Unconfigured-check rule)**: extend the existing Unconfigured-check paragraph (line 45) with a sentence about the Puck Screen field. Required regex match: `grep -Eci 'Puck Screen.*(missing|absent|not present|omitted|no row).*None|treat.*Puck Screen.*None'` ≥ 1. Suggested phrasing: "Treat a missing Puck Screen row, or one with value `None`/blank/whitespace, as no screen present. Puck Screen field state is orthogonal to template detection — a populated Puck Screen row alone does NOT count as a configured setup."
  - **R13c (parsing contract)**: document how skills parse the Puck Screen value. Required behaviors:
    - (a) missing row → `None`
    - (b) row present with value "None" (case-insensitive) or whitespace-only → `None`
    - (c) row present with any other non-empty value → "screen present"; classification keyed on case-insensitive substring match for {`mesh`, `round-hole`, `thin`, `thick`}.
    - Verifiable via `grep -c 'Puck Screen' CLAUDE.md` ≥ 2 (field-reference + parsing-contract).
    - **PINNED LOCATION**: the parsing contract paragraph MUST be appended directly after the Unconfigured-check paragraph (line 45 area), as a sibling paragraph in the Data Architecture section. It MUST NOT be added to the Core Rules block (lines 126+) or anywhere below line 100. Verifiable via `awk '/^## Data Architecture/,/^## /' CLAUDE.md | grep -c 'Puck Screen.*parsing\|parsing.*Puck Screen'` ≥ 1 — confirms the parsing contract is co-located with Unconfigured check, not adrift in the file.
  - **R12 byte-preservation tripwire**: the Core Rule block (lines 130–133 area) MUST not be edited. Captured digest: `7976b6a572f2879ef72eb62e7c6ff9b71555ab34ae80807d808292dfcaf8f7ae`.
  - **PRE-FLIGHT VERIFICATION (REQUIRED — run before any Edit on CLAUDE.md begins)**: confirm the captured digest matches the current file state. If `awk '/Sour AND bitter = channeling/,/^$/' CLAUDE.md | shasum -a 256 | awk '{print $1}'` ≠ `7976b6a572f2879ef72eb62e7c6ff9b71555ab34ae80807d808292dfcaf8f7ae`, STOP. Either the digest in this plan is stale, the file has changed since plan-write, or an earlier task (Tasks 1–11) inadvertently edited CLAUDE.md. Investigate root cause before proceeding; do NOT update the digest in plan.md silently.
  - **AWK-RANGE STRUCTURAL INVARIANT (REQUIRED — run after Task 12's last edit)**: after all Task 12 edits complete, confirm the awk extraction still covers BOTH bullets — `awk '/Sour AND bitter = channeling/,/^$/' CLAUDE.md | grep -c '^- \*\*'` MUST equal 2. This catches the case where an inadvertently-inserted blank line within the block silently truncates the awk range and a partial-extraction SHA256 happens to match by coincidence.
  - To minimize risk: edit only sections AWAY from the Core Rule block (Knowledge Files at line 18 area; Data Architecture at line 35–55 area). Verify the pre-flight digest BEFORE editing and the awk-range invariant + post-edit digest AFTER editing.
- **Verification**:
  - `grep -c 'PUCK_SCREENS' /Users/charlie.hall/Workspaces/gaggimate-barista/CLAUDE.md` ≥ 1 — pass if ≥ 1 (R13a).
  - `grep -Eci 'Puck Screen.*(missing|absent|not present|omitted|no row).*None|treat.*Puck Screen.*None' /Users/charlie.hall/Workspaces/gaggimate-barista/CLAUDE.md` ≥ 1 — pass if ≥ 1 (R13b).
  - `grep -c 'Puck Screen' /Users/charlie.hall/Workspaces/gaggimate-barista/CLAUDE.md` ≥ 2 — pass if ≥ 2 (R13c).
  - `awk '/Sour AND bitter = channeling/,/^$/' /Users/charlie.hall/Workspaces/gaggimate-barista/CLAUDE.md | shasum -a 256 | awk '{print $1}'` = `7976b6a572f2879ef72eb62e7c6ff9b71555ab34ae80807d808292dfcaf8f7ae` — pass if exact match (R12 byte-preservation; uses captured snapshot, not git history, for resilience to commit count).
- **Status**: [x] complete (commit d1f3c83)

### Task 13: Migrate private `grind-map.md` header from 11→12 columns

- **Files**: `/Users/charlie.hall/Workspaces/gaggimate-barista/grind-map.md` (symlink → `/Users/charlie.hall/Workspaces/gaggimate-barista-data/grind-map.md`)
- **What**: One-time, idempotent schema migration of the private grind-map.md header line and alignment line from 11 to 12 columns. Existing data rows are NOT touched (their missing 12th cell parses as blank under markdown-table semantics → "unknown" per R7's contract). After this task, the schema is aligned and `/feedback`'s append-only writer (Task 10) can write 12-col rows without producing ragged output. Auto-commit per `.data-repo-path` policy applies.
- **Depends on**: [6]
- **Complexity**: simple
- **Context**:
  - Current header (line 7 of private grind-map.md): `| Coffee | Roast | Process | Origin | Days Off Roast | Grind | Profile | Ratio | Temp | Rating | Date |`
  - Current alignment (line 8): `|--------|-------|---------|--------|----------------|-------|---------|-------|------|--------|------|`
  - Required new header: `| Coffee | Roast | Process | Origin | Days Off Roast | Grind | Profile | Ratio | Temp | Rating | Date | Puck Screen? |`
  - Required new alignment: `|--------|-------|---------|--------|----------------|-------|---------|-------|------|--------|------|--------------|`
  - **Idempotency check (REQUIRED — run before edit)**: `head -n 7 grind-map.md | tail -n 1 | grep -c 'Puck Screen?'` — if = 1 the migration has already run; SKIP the task. If = 0, proceed with the edit.
  - **Data invariance**: only the header line (line 7) and alignment line (line 8) are edited. Lines 9..N (existing data rows) are NOT touched — they remain 11-col, and their missing 12th cell parses as blank under awk-style markdown parsing, which is exactly the R7 "blank = unknown" semantic.
  - **Distinguishes schema migration from data back-fill**: this task is a SCHEMA migration (one-time, lossless, idempotent — adds a header column). It is NOT a DATA back-fill (which would attempt to write Y/blank values into old rows whose Puck Screen state we do not know). R20's "no back-fill" prohibition applies to data, not schema.
  - **Auto-commit propagation**: after this edit, the private repo's auto-commit hook runs per CLAUDE.md Data Architecture policy. Verify via `git -C /Users/charlie.hall/Workspaces/gaggimate-barista-data/ log --oneline -1` showing the migration commit.
- **Verification**:
  - `head -n 7 /Users/charlie.hall/Workspaces/gaggimate-barista/grind-map.md | tail -n 1 | grep -c 'Puck Screen?'` = 1 — pass if = 1 (header migrated).
  - `awk -F'|' 'NR==7 {print NF}' /Users/charlie.hall/Workspaces/gaggimate-barista/grind-map.md` = 14 — pass if = 14 (12 columns + 2 outer pipes, matching grind-map.example.md width post-Task-6).
  - `awk -F'|' 'NR==8 {print NF}' /Users/charlie.hall/Workspaces/gaggimate-barista/grind-map.md` = 14 — pass if = 14 (alignment line matches header width).
  - Existing data rows untouched: `awk -F'|' 'NR>=9 {print NF}' /Users/charlie.hall/Workspaces/gaggimate-barista/grind-map.md | sort -u` = `13` (single value: existing 11-col rows have NF=13 from `awk -F'|'`; if any row reads 14, a row was edited — fail). Pass if the only value is 13.
  - Idempotent re-run: rerunning Task 13 on the migrated file MUST detect via the idempotency check and skip with no edits. Interactive/session-dependent: idempotency is verified by reading the task's instructions and confirming the head-grep precondition is checked before the edit.
- **Status**: [x] complete (private-repo commit 3a23a1d)

### Task 14: Final integration verification — full R1–R22 acceptance sweep

- **Files**: none modified; verification-only (a script may be authored at `/tmp/puck_screen_acceptance.sh` for convenience but is not committed).
- **What**: Run every R1–R22 acceptance command in sequence and confirm pass/fail for each. Manually inspect R5 paragraph proximity, R8 row distinctness, R9 routing-table location, R11 hedge-clause completeness, R17 negative-write invariant across all four skill diffs, R20 semantic + no-data-back-fill behavior, R21 gating + no-parameter-change.
- **Depends on**: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
- **Complexity**: simple
- **Context**:
  - This is the read-only end-to-end check before review. Each requirement's grep acceptance is replicated here as a single sweep so any drift across the 13 implementation tasks surfaces in one place.
  - For Interactive/session-dependent acceptances (R5 proximity, R8 distinct lines visual confirmation, R9 routing-table location, R17 negative-write invariant, R20 mechanism preservation, R21 gating, Task 13 idempotency), inspect the diffs in the review phase.
- **Verification**:
  - All grep commands listed in Tasks 1–13 verifications run and pass — pass if every command's exit/count assertion holds.
  - SHA256 check from Task 12 runs and matches captured digest — pass if hash equals `7976b6a572f2879ef72eb62e7c6ff9b71555ab34ae80807d808292dfcaf8f7ae`.
  - Awk-range structural invariant from Task 12 holds — `awk '/Sour AND bitter = channeling/,/^$/' CLAUDE.md | grep -c '^- \*\*'` = 2.
  - Task 13 schema-migration acceptance: private grind-map.md header is 12-col AND existing data rows are 11-col (untouched).
- **Status**: [x] complete (verification-only; 22/22 R1–R22 pass)

## Verification Strategy

End-to-end:
1. `awk '/Sour AND bitter = channeling/,/^$/' CLAUDE.md | shasum -a 256` digest equals captured `7976b6a572f2879ef72eb62e7c6ff9b71555ab34ae80807d808292dfcaf8f7ae` AND `awk '/Sour AND bitter = channeling/,/^$/' CLAUDE.md | grep -c '^- \*\*'` = 2 — Core Rule preserved byte-for-byte (R12) AND awk-range still covers both bullets.
2. `knowledge/PUCK_SCREENS.md` and `knowledge/reference/PUCK_SCREENS_REFERENCE.md` both exist and pass their R2/R3/R14/R15/R16/R22 grep checks — knowledge layer is complete and honest.
3. `EXTRACTION_SCIENCE.md` no longer carries the migrated phrase; line-42 row stub points to PUCK_SCREENS; line-44 forward reference includes PUCK_SCREENS reference (R4).
4. `BASKETS.md` carries the masking note adjacent to the existing rule (R5).
5. `user-setup.example.md` Equipment row + Notes-section thin/thick examples land (R1, R18); `grind-map.example.md` 12th column + semantic-contract comment land (R6, R7); MEMORY.md has two distinct PUCK_SCREENS rows (R8); CLAUDE.md gains Knowledge-Files entry, Unconfigured-check Puck Screen rule, and parsing contract (R13).
6. Skill grep checks pass for `/consult` (R9), `/diagnose` (R10, R11), `/feedback` (R19, R20), `/new-coffee` (R21).
7. Manual diff review of all four skills for R17 negative-write invariant: no skill instruction edits/appends/overwrites the Equipment-table Puck Screen row in user-setup.md.
8. Private `grind-map.md` schema is 12-col after Task 13 migration; existing data rows untouched (11-col); `/feedback`'s next write produces a clean 12-col row, no ragged output.
9. Functional spot-check via the user invoking `/consult "puck screen"` and `/feedback` with a shot to confirm runtime behavior matches the spec.

## Veto Surface

- **R12 verification deviation from spec literal.** R12's spec acceptance command uses `git show HEAD~1:CLAUDE.md` which is fragile to commit cadence. Plan substitutes a captured-digest comparison + awk-range structural invariant. This deviation is registered as a `plan_deviation` event in `events.log` when the plan is approved, so the audit trail is explicit and not buried in this Veto Surface alone. The user can revert to R12's git-history form if they prefer; doing so constrains the commit cadence to one CLAUDE.md commit landing last.
- **Task 9 / Task 10 guardrail Single Source of Truth.** Both `/diagnose` and `/feedback` reference `knowledge/PUCK_SCREENS.md` §Diagnostic Guardrails (added by Task 1) for cold-screen and channeling-nuance wording rather than each carrying their own copy. Same architectural move as R4's EXTRACTION_SCIENCE.md → PUCK_SCREENS.md migration applied consistently. Future updates to the guardrail edit one file, not two. Spec deviation: spec R10/R11/R19 use grep tokens that were originally drafted assuming inline duplication; verifications are relaxed to allow either inline tokens OR named PUCK_SCREENS.md references. Logged as `plan_deviation` events.
- **R11 extended to /feedback.** Spec literally scopes R11 (channeling-nuance note) to `/diagnose` only. Plan extends it to `/feedback` because spec.md:9 already established "/feedback is the primary sour-shot entry path" as the rationale for extending R19 to /feedback; applying that same rationale to R11 is internal consistency, not scope expansion. Logged as a deliberate spec extension.
- **Task 6 example-row blank cell semantic.** Plan suggests the example row's "Puck Screen?" cell be blank to demonstrate the "unknown" semantic from R7. An alternative is to populate it with `Y` (matches the Active Coffee user's Normcore screen). Blank is recommended because the example file is for users without configured data — a blank cell exemplifies the "we don't know" default. The user can override.
- **Task 11 placement of conditional-load section.** `/new-coffee` does not currently have a `Conditionally Load` section the way `/feedback` does. Plan introduces one. An alternative is to extend the existing skill prose at line 46 (`### 3. CONSULT Grind Map`) with a hook. Consistent-with-feedback structure is recommended; the user can prefer prose-extension if they want to minimize structural change.
- **Task 7 row labels.** Suggested labels are `Puck screens (quick)` and `Puck screens (deep)`. The MEMORY.md table uses varied label styles — `Milk science & drinks` for quick, `Milk & drinks (deep)` for deep. Editorial choice; either label scheme passes R8.

## Scope Boundaries

Explicitly excluded per spec Non-Requirements:

- No changes to `.claude/skills/gaggimate-profiles/SKILL.md`. Pre-infusion +1–2s effect deferred to a future lifecycle.
- No changes to `/new-coffee` starting-grind, starting-temperature, or starting-ratio parameter logic.
- No changes to `grind-map.md` similarity-matching logic in `/new-coffee`.
- No new temperature compensation baked into any skill — knowledge reference owns the +1°C and +2–3°C numbers.
- No modification of the `CLAUDE.md` Core Rules block beyond adding the Unconfigured-check and parsing-contract lines for the Puck Screen field. Core Rule "Sour AND bitter = channeling..." preserved byte-for-byte (R12).
- No vendor-specific skill logic. Skill conditionals key on `value ≠ None` + canonical classification substrings.
- No automatic detection from Gaggimate telemetry.
- No grind-map retroactive **data** back-fill — existing rows' Puck Screen? cells remain unset and parse as blank → "unknown" per R7's contract. (Distinction: schema migration of the header line from 11→12 columns is in scope and is performed once during implementation by Task 13. Schema migration ≠ data back-fill.)
- No changes to `bin/setup-data-repo.sh`.
- No support for concurrent multi-screen tracking.
