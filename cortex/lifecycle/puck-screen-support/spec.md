# Specification: puck-screen-support

## Problem Statement

The user bought a Normcore 58.5mm round-hole 0.8mm puck screen to reduce channeling on light roasts. The agent currently has no way to know whether a given user has a puck screen installed, which creates four gaps: (a) `/diagnose` and `/feedback` cannot guard against the cold-screen-causes-sour misdiagnosis trap (grinding finer makes it worse); (b) `knowledge/BASKETS.md:16`'s "mesh pattern = reduce dose" rule is silently masked when a puck screen is installed, quietly eroding a diagnostic cue; (c) there is no authoritative knowledge file to route puck-screen questions to (content is scattered across a single row in `EXTRACTION_SCIENCE.md`); (d) `/new-coffee` has no mechanism to load puck-screen guidance during light-roast dial-in — the user's stated primary motivation. This feature adds optional Equipment-table tracking, a new quick+deep knowledge file pair with explicit classification dispatch (thin/thick × round-hole/mesh), and narrow conditional logic in `/diagnose`, `/feedback`, `/new-coffee`, and `/consult`. The public repo template must remain correct for users without a screen.

## Scope Note

Scope extended from initial "tight — 2 skills" after critical review established that `/feedback` is the primary sour-shot entry path (making the cold-screen guardrail dead code in `/diagnose` alone) and that `/new-coffee` must gain a conditional-load hook for PUCK_SCREENS.md to serve the Problem Statement's motivation. `/gaggimate-profiles` remains unchanged — the +1–2s pre-infusion effect is deferred to a future lifecycle (see Non-Requirements).

## Requirements

**R1 (Must)**: `user-setup.example.md` gains an optional "Puck Screen" row in the Equipment table, defaulting to `None`.
- Acceptance: `grep -c '^| \*\*Puck Screen\*\*' user-setup.example.md` = 1 AND `grep -c '^| \*\*Puck Screen\*\* | None |' user-setup.example.md` = 1.

**R2 (Must)**: `knowledge/PUCK_SCREENS.md` exists as a quick-ref with an explicit classification dispatcher.
- Acceptance (structural): file exists; contains a `## Screen Classification` (or equivalent) section; contains at least four other top-level `##` sections covering "When to Use", "Effects on Extraction", "Common Pitfalls", "Cleaning & Maintenance"; contains a "See reference for deep physics" pointer to `reference/PUCK_SCREENS_REFERENCE.md`.
- Acceptance (classification dispatcher): the Screen Classification section must name at least two categories on each axis: thickness (`thin ≤ 1mm` and `thick > 1mm`) AND hole type (`round-hole` and `mesh`); each downstream recommendation section must label its applicability using the canonical tokens above. `grep -c 'thin ≤ 1mm\|thin (≤ 1mm)\|thin (≤1mm)' knowledge/PUCK_SCREENS.md` ≥ 1 AND `grep -c 'thick > 1mm\|thick (> 1mm)\|thick (>1mm)' knowledge/PUCK_SCREENS.md` ≥ 1 AND `grep -c 'round-hole' knowledge/PUCK_SCREENS.md` ≥ 2 AND `grep -c 'mesh' knowledge/PUCK_SCREENS.md` ≥ 2.

**R3 (Must)**: `knowledge/reference/PUCK_SCREENS_REFERENCE.md` exists with a temperature-compensation table owning the numeric claims.
- Acceptance (structural): file exists; `wc -l knowledge/reference/PUCK_SCREENS_REFERENCE.md` ≥ 60; contains a top-level section on heat-buffer physics.
- Acceptance (temperature ownership): contains a table or labelled section documenting temperature compensation by thickness class. `grep -c '+1°C\|+1 °C\|+1C' knowledge/reference/PUCK_SCREENS_REFERENCE.md` ≥ 1 AND `grep -Ec '\+2[–-]3°C|\+2[–-]3 °C|\+2 to 3°C' knowledge/reference/PUCK_SCREENS_REFERENCE.md` ≥ 1.

**R4 (Must)**: Migrate `knowledge/EXTRACTION_SCIENCE.md:42` content and update the forward reference on line 44.
- Acceptance (migration out): `grep -c 'Protects puck from shower screen imprint' knowledge/EXTRACTION_SCIENCE.md` = 0 AND the line-42 table row is preserved in the 3-column Puck Prep Tools table with the specific stub content `See [PUCK_SCREENS.md](PUCK_SCREENS.md)` in cell 2 and the literal em-dash `—` in cell 3 (Acceptance: `grep -E '^\| \*\*Puck screen on top\*\* \| See \[PUCK_SCREENS\.md\]\(PUCK_SCREENS\.md\) \| — \|' knowledge/EXTRACTION_SCIENCE.md` matches exactly 1 line).
- Acceptance (migration in): `grep -c 'Protects puck from shower screen imprint' knowledge/PUCK_SCREENS.md` ≥ 1.
- Acceptance (line-44 forward reference update): the "Recommended combo" line at `knowledge/EXTRACTION_SCIENCE.md:44` which currently reads `**Recommended combo:** WDT → light tap to settle → tamp → (optional: puck screen on top)` is updated to include an inline reference to PUCK_SCREENS.md so a reader hitting line 44 has local context. Acceptance: `grep -A0 'Recommended combo' knowledge/EXTRACTION_SCIENCE.md | grep -c 'PUCK_SCREENS'` ≥ 1.

**R5 (Must)**: `knowledge/BASKETS.md` masking note.
- Acceptance (content): `grep -c 'puck screen' knowledge/BASKETS.md` ≥ 1 AND the note explicitly states the mesh-imprint evidence is MASKED when a puck screen is installed, recommending flow behavior / measured headroom as alternatives. Acceptance: `grep -Ec 'mask(ed|s)|hide[sn]' knowledge/BASKETS.md` ≥ 1.
- Acceptance (preservation): the existing sentence containing "mesh pattern pressed into the surface" AND the existing dose guidance "reduce your dose by 0.5g" both still appear in `knowledge/BASKETS.md` (both `grep -c` results = 1).
- Acceptance (proximity): the masking note is in the same markdown paragraph or the immediately adjacent paragraph as the existing rule. Interactive/session-dependent: adjacency is judged by reading the diff; no command reliably verifies paragraph proximity without parsing markdown.

**R6 (Must)**: `grind-map.example.md` gains a "Puck Screen?" column at the end of the shot-history table.
- Acceptance (header): `head -n 8 grind-map.example.md | grep -c 'Puck Screen?'` ≥ 1.
- Acceptance (example row): the existing example shot row has exactly 12 pipe-separated fields after header-row update. Acceptance: `awk -F'|' 'NR==9 {print NF}' grind-map.example.md` = 14 (12 fields + 2 outer delimiter pipes = 14 fields by `awk -F'|'` counting).

**R7 (Must)**: `grind-map.example.md` includes a semantic-contract comment: blank means "unknown", explicitly NOT "no screen".
- Acceptance (positive phrase): `grep -ci 'blank.*unknown\|unknown.*blank' grind-map.example.md` ≥ 1.
- Acceptance (contrast phrase — enforces the semantic the literal-only check would miss): `grep -Eci 'NOT.*\"?N\"?|not.*no screen|not.*absence' grind-map.example.md` ≥ 1.

**R8 (Must)**: MEMORY.md gains TWO DISTINCT rows in the "Architecture: Single Source of Truth" table — following the one-topic-per-row convention used throughout.
- Acceptance (two distinct rows): `grep -c '| .* | knowledge/PUCK_SCREENS\.md |' ~/.claude/projects/-Users-charlie-hall-Workspaces-gaggimate-barista/memory/MEMORY.md` = 1 AND `grep -c '| .* | knowledge/reference/PUCK_SCREENS_REFERENCE\.md |' ~/.claude/projects/-Users-charlie-hall-Workspaces-gaggimate-barista/memory/MEMORY.md` = 1 (the two file paths appear in table rows with `|` delimiters, NOT on the same line).
- Acceptance (structural negative): the two `PUCK_SCREENS`-containing rows are on different lines. Acceptance: `grep -n 'PUCK_SCREENS' MEMORY.md | awk -F: '{print $1}' | sort -u | wc -l` ≥ 2.

**R9 (Must)**: `.claude/skills/consult/SKILL.md` routing table gains a row for puck-screen keywords → `PUCK_SCREENS.md` (primary) + `PUCK_SCREENS_REFERENCE.md` (deep).
- Acceptance: `grep -c 'puck screen' .claude/skills/consult/SKILL.md` ≥ 1 AND `grep -c 'PUCK_SCREENS' .claude/skills/consult/SKILL.md` ≥ 2 (both quick and reference cited). The new content appears within the classification/routing table — Interactive/session-dependent: the "within the routing table" constraint is location-dependent; line-range anchors drift on edits, so verification is by reading the modified SKILL.md.

**R10 (Must)**: `.claude/skills/diagnose/SKILL.md` CORRELATE section gains a cold-screen guardrail — when the shot tastes sour AND the user's Equipment table shows a Puck Screen row with value ≠ `None`, the skill asks about preheat discipline BEFORE recommending a grind-finer adjustment.
- Acceptance (token): `grep -ci 'puck screen' .claude/skills/diagnose/SKILL.md` ≥ 2 (at least two references — one for the conditional read, one for the guardrail itself).
- Acceptance (guardrail wording): `grep -ci 'preheat' .claude/skills/diagnose/SKILL.md` ≥ 1 AND the preheat word appears within 10 lines of a "puck screen" mention (Acceptance: `grep -B5 -A5 -i 'preheat' .claude/skills/diagnose/SKILL.md | grep -ci 'puck screen'` ≥ 1).

**R11 (Must)**: `.claude/skills/diagnose/SKILL.md` channeling-nuance note — when diagnosing sour+bitter with a screen present, remaining channeling is **likely** (NOT "almost certainly") puck-prep-driven, EXCEPT when the screen itself could be misaligned (upside-down, wrong size, bent). The recommendation remains "fix puck prep, NOT grind" per CLAUDE.md Core Rule.
- Acceptance (distinction tokens): `grep -ci 'puck.?prep.?driven\|prep-driven\|shower.?screen.?driven' .claude/skills/diagnose/SKILL.md` ≥ 2 (at least one mention of each side of the distinction).
- Acceptance (reasoning chain): the skill contains a sentence wiring the reasoning: if a screen is present, shower-screen-driven channeling is already mitigated, so remaining channeling is likely prep-driven. Acceptance: `grep -B2 -A2 -i 'shower.?screen.?driven' .claude/skills/diagnose/SKILL.md | grep -ci 'mitigat\|reduc'` ≥ 1.
- Acceptance (hedge for misaligned screens): the nuance note must flag screen-caused channeling as a separate category. Acceptance: `grep -ci 'upside[- ]down\|wrong size\|bent.*screen\|screen.*orientation' .claude/skills/diagnose/SKILL.md` ≥ 1.

**R12 (Must)**: `CLAUDE.md` Core Rule "Sour AND bitter = channeling..." preserved byte-for-byte via SHA256 checksum comparison.
- Acceptance (pre-implementation capture): before implementation starts, capture the exact Core Rule paragraph content via `grep -A0 -B0 'Sour AND bitter = channeling' CLAUDE.md` extended until the next blank line or heading; compute its SHA256 with `sha256sum`. Record the digest in the implementation plan or commit message.
- Acceptance (post-implementation verification): after implementation, extract the same block and compute SHA256. The two digests must be byte-identical. Acceptance command: `diff <(git show HEAD~1:CLAUDE.md | awk '/Sour AND bitter = channeling/,/^$/') <(awk '/Sour AND bitter = channeling/,/^$/' CLAUDE.md)` → exit 0, no output.

**R13 (Must)**: `CLAUDE.md` updates — Knowledge Files list gains `PUCK_SCREENS.md`; an "Unconfigured check" rule added for the Puck Screen field; parsing contract documented.
- Acceptance (knowledge files list): `grep -c 'PUCK_SCREENS' CLAUDE.md` ≥ 1.
- Acceptance (unconfigured rule — broader regex to accept natural phrasings): `grep -Eci 'Puck Screen.*(missing|absent|not present|omitted|no row).*None|treat.*Puck Screen.*None' CLAUDE.md` ≥ 1.
- Acceptance (parsing contract): `CLAUDE.md` documents how skills parse the Puck Screen field value. Required behaviors: (a) missing row → `None`, (b) row present with value "None" (case-insensitive) or whitespace-only → `None`, (c) row present with any other non-empty value → "screen present"; classification is keyed on presence of substrings {"mesh", "round-hole", "thin", "thick"} in the value. Acceptance: `grep -c 'Puck Screen' CLAUDE.md` ≥ 2 (field-reference + parsing contract).

**R14 (Must — safety)**: `knowledge/PUCK_SCREENS.md` explicitly states the agent never proposes adding a puck screen as a diagnostic output.
- Acceptance: `grep -ci 'never propose\|do not propose\|will not suggest\|never suggest' knowledge/PUCK_SCREENS.md` ≥ 1.

**R15 (Must — honesty)**: `knowledge/PUCK_SCREENS.md` hedges the "screens help light roasts more" claim, and the hedge is co-located with the claim.
- Acceptance (hedge phrase): `grep -ci 'community-reported\|not controlled\|anecdotal\|unverified\|no controlled' knowledge/PUCK_SCREENS.md` ≥ 1.
- Acceptance (colocation): `grep -B3 -A3 -i 'light roast' knowledge/PUCK_SCREENS.md | grep -ci 'community-reported\|not controlled\|anecdotal\|unverified\|no controlled'` ≥ 1 (the hedge phrase appears within 3 lines of a "light roast" mention).

**R16 (Must — honesty)**: Knowledge files exclude vendor-marketing numbers flagged in research.
- Acceptance: `grep -Ec '22% uniformity|4-7% yield|4[–-]7% yield|90% channeling|copper-core' knowledge/PUCK_SCREENS.md knowledge/reference/PUCK_SCREENS_REFERENCE.md` = 0.

**R17 (Must — concurrency)**: No skill writes the Puck Screen row of `user-setup.md`. The field is user-edited only.
- Acceptance (Interactive/session-dependent): this is a negative-write invariant that cannot be verified automatically — "absence of a write instruction" is not a grep pattern. During review, inspect diffs of all four modified skills (`.claude/skills/{consult,diagnose,feedback,new-coffee}/SKILL.md`) and confirm none contains an instruction to edit, append, or overwrite the Equipment-table Puck Screen row in `user-setup.md`. Rationale for manual check: skill-modification steps are natural-language instructions, not code — there is no enumerable write API to grep for; any regex heuristic would either over-match (flagging `user-setup.md` reads) or under-match (missing paraphrased write instructions).

**R18 (Should)**: `user-setup.example.md` includes a brief Notes-section line documenting the Puck Screen field is optional with canonical-format examples showing at least one "thin" and one "thick" variant.
- Acceptance: `grep -c 'Puck Screen' user-setup.example.md` ≥ 2 AND `grep -Eci 'thin|0\.8mm|≤ 1mm' user-setup.example.md` ≥ 1 AND `grep -Eci 'thick|1\.7mm|> 1mm' user-setup.example.md` ≥ 1.

**R19 (Must — /feedback extension)**: `.claude/skills/feedback/SKILL.md` sour-shot adjustment path gains the cold-screen guardrail equivalent to R10.
- Acceptance (token): `grep -ci 'puck screen' .claude/skills/feedback/SKILL.md` ≥ 1.
- Acceptance (guardrail): when the user reports a sour-tasting shot AND the Equipment table shows a Puck Screen row with value ≠ `None`, the skill checks preheat discipline BEFORE recommending a grind-finer adjustment. Acceptance: `grep -B5 -A5 -i 'preheat' .claude/skills/feedback/SKILL.md | grep -ci 'puck screen'` ≥ 1 OR `grep -ci 'preheat' .claude/skills/feedback/SKILL.md` ≥ 1 AND `grep -ci 'cold.*screen\|screen.*cold' .claude/skills/feedback/SKILL.md` ≥ 1.
- Acceptance (scope limit): the adjustment table ordering remains "Grind → Yield → Temp → Pressure → Puck Prep"; the guardrail is a pre-check, NOT a reordering of the hierarchy.

**R20 (Must — /feedback grind-map writer)**: `.claude/skills/feedback/SKILL.md` grind-map writer extends to 12 columns — populating "Puck Screen?" from the user-setup Equipment table.
- Acceptance (column count in writer): the skill's grind-map append step lists 12 fields. `grep -c 'Puck Screen?\|Puck Screen\?' .claude/skills/feedback/SKILL.md` ≥ 1 AND the column list in the skill includes all 12 field names in order (Coffee, Roast, Process, Origin, Days Off Roast, Grind, Profile, Ratio, Temp, Rating, Date, Puck Screen?).
- Acceptance (semantic): when no Puck Screen row exists in user-setup (or value = `None`), the written value is blank (not "N"). When a Puck Screen row has any other value, the written value is "Y".
- Acceptance (back-compat): the skill does not attempt to back-fill existing 11-column rows; only new rows are written with 12 columns. Interactive/session-dependent: back-compat is verified by reading the skill's append-only behavior in the modified SKILL.md.

**R21 (Must — /new-coffee extension)**: `.claude/skills/new-coffee/SKILL.md` gains a conditional-load hook that loads `PUCK_SCREENS.md` when the user-setup Equipment table shows a Puck Screen row with value ≠ `None`.
- Acceptance (conditional-load entry): `grep -c 'PUCK_SCREENS' .claude/skills/new-coffee/SKILL.md` ≥ 1.
- Acceptance (trigger): `grep -ci 'puck screen' .claude/skills/new-coffee/SKILL.md` ≥ 1 AND the load is gated on Equipment-row presence (not always-loaded).
- Acceptance (no parameter change): `/new-coffee`'s grind/temp/ratio starting recommendations are NOT modified by screen presence (the knowledge file informs discussion only; parameters flow from roast + processing + origin only, as today).

**R22 (Must — documentation)**: Edge Cases section in this spec is mirrored in `knowledge/PUCK_SCREENS.md` or `CLAUDE.md` as a user-facing parsing/handling reference (so behavior is documented, not just specified).
- Acceptance: `grep -ci 'missing.*row\|blank.*value\|non[- ]canonical\|mesh.*screen\|thick.*screen\|upside[- ]down' knowledge/PUCK_SCREENS.md` ≥ 3 (at least three edge-case scenarios documented).

## Non-Requirements

- No changes to `.claude/skills/gaggimate-profiles/SKILL.md`. Web research flagged a possible +1–2s pre-infusion benefit for light roasts with screens — this is deferred to a future lifecycle because (a) effect is modest at 0.8mm, (b) profile design is already per-coffee hand-tuned via `/gaggimate-profiles` so the user can apply this discretion manually, (c) the scope of this lifecycle has already grown from 2 → 4 skills and further expansion crosses into "full port" territory that review already pushed back on.
- No changes to `/new-coffee`'s starting-grind, starting-temperature, or starting-ratio parameter logic. Web research confirmed no shift is warranted for 0.8mm round-hole screens. R21's conditional load is for discussion context only.
- No changes to the `grind-map.md` similarity-matching logic in `/new-coffee` (Non-Requirement). The new "Puck Screen?" column is data capture only — matchers continue to match on roast/processing/origin. R7's "blank = unknown" is documentary; future similarity-matcher changes are out of scope.
- No new temperature compensation baked into any skill. R3 makes the knowledge reference file the sole owner of the +1°C (unpreheated thin) and +2–3°C (thick) numeric claims. Skills only ask about preheat discipline; they do not recommend `±°C` adjustments.
- No modification of `CLAUDE.md` Core Rules beyond adding the "Unconfigured check" and parsing-contract lines for the Puck Screen field. The "Sour AND bitter = channeling → fix puck prep, NOT grind" rule stays byte-for-byte (R12).
- No vendor-specific skill logic. Skill conditionals key on value ≠ `None` + classification substrings per the parsing contract (R13), NOT on brand name.
- No automatic detection from Gaggimate telemetry — device does not report screen presence.
- No grind-map retroactive back-fill. Existing 11-column rows keep their shape; writer appends new 12-column rows (R20).
- No changes to `bin/setup-data-repo.sh` — the Equipment row is added manually by the user.
- No support for concurrent multi-screen tracking (user owns only one screen at a time per the schema). Screen swaps happen between sessions via user editing.

## Edge Cases

- **Missing Puck Screen row entirely**: skill parses as `None` silently per R13's Unconfigured check.
- **Row present but value blank or whitespace-only**: parsed as `None` (same as missing row).
- **Value = "None" (case-insensitive)**: parsed as `None`.
- **Value with recognized keywords (case-insensitive substring match)**: `mesh`, `round-hole`, `thin`, `thick` set the classification. Missing classification → default `thin round-hole` (the reference product assumption), with a note in the knowledge file that this default may mis-advise.
- **Non-canonical value (e.g., "yes", "true", "I have one")**: parsed as "screen present with default thin round-hole classification". Cold-screen guardrail fires regardless.
- **Mesh screen**: knowledge-file classification dispatcher routes guidance to the mesh section; cleaning cadence differs (oil retention); R11's shower-screen-driven-is-mitigated claim still applies.
- **Thick screen (≥1.7mm)**: knowledge-file classification dispatcher routes to the thick section; temperature compensation (+2–3°C unpreheated, per R3's reference-file table) applies.
- **Upside-down / wrong-size / bent screen**: R11's channeling-nuance note flags screen-as-channeling-source as a separate category; agent prompts user to verify orientation/fit before applying the "remaining channeling is prep-driven" heuristic.
- **User removes the Puck Screen row**: next skill invocation reads as `None`; behavior reverts automatically.
- **Cold screen + sour shot on `/feedback` path**: R19's guardrail asks about preheat before grind.
- **Cold screen + sour shot on `/diagnose` path**: R10's guardrail asks about preheat before grind.
- **Sour+bitter + screen present**: R11 applies — remaining channeling is *likely* puck-prep-driven (not "almost certainly"); agent also verifies screen orientation. Fix remains "puck prep, NOT grind" per Core Rule.
- **Grind-map row with blank "Puck Screen?" cell**: treated as "unknown" (R7). New writes populate Y/blank (R20).
- **Grind-map symlink skew** (private 11-col, public template 12-col): first user `/feedback` invocation after feature ship writes a 12-column row into an 11-column table → ragged in the private data until user manually adds the header column. Acceptable transitional state; R20's writer does not back-fill.
- **Auto-commit race**: existing race between `/feedback` and manual `user-setup.md` edits is unchanged. R17 ensures no new write paths are added to the Puck Screen row.
- **Public-repo user who forgets to edit the template**: sentinel `None` in `user-setup.example.md` ensures no misinformation.
- **Template-detection interaction**: existing CLAUDE.md "Unconfigured check" flags generic-equipment placeholder Active Coffee, no grind history. A populated Equipment table with Puck Screen = `None` does NOT count as template-ness; a Puck Screen set to the example vendor string in an otherwise-template file does NOT auto-resolve the template warning. Add a note to CLAUDE.md's Unconfigured check clarifying that Puck Screen field state is orthogonal to template detection.

## Changes to Existing Behavior

- **MODIFIED**: `knowledge/EXTRACTION_SCIENCE.md:42` → row cell 2 becomes `See [PUCK_SCREENS.md](PUCK_SCREENS.md)`; cell 3 becomes `—`. Line-44 "Recommended combo" gains an inline `PUCK_SCREENS.md` reference. Original phrase moves into `PUCK_SCREENS.md`.
- **MODIFIED**: `knowledge/BASKETS.md:16` → masking note appended adjacent to existing mesh-imprint rule.
- **MODIFIED**: `grind-map.example.md` → 12th column "Puck Screen?" added; existing example row populated; semantic-contract comment added.
- **MODIFIED**: `.claude/skills/consult/SKILL.md` → routing row added for puck-screen keywords.
- **MODIFIED**: `.claude/skills/diagnose/SKILL.md` → CORRELATE gains cold-screen guardrail (R10) + channeling-nuance note (R11) covering screen-caused and screen-related cases.
- **MODIFIED**: `.claude/skills/feedback/SKILL.md` → sour-shot adjustment path gains cold-screen guardrail (R19); grind-map writer extends to 12 columns populating Puck Screen? from Equipment (R20).
- **MODIFIED**: `.claude/skills/new-coffee/SKILL.md` → conditional-load hook for `PUCK_SCREENS.md` gated on Equipment row presence (R21).
- **MODIFIED**: `CLAUDE.md` → Knowledge Files list gains `PUCK_SCREENS.md`; new Unconfigured-check line for the field; new parsing-contract documentation.
- **MODIFIED**: `MEMORY.md` Architecture table → two new rows (quick + deep).
- **MODIFIED**: `user-setup.example.md` → Equipment table gains Puck Screen row (default `None`); Notes section gains optional-field documentation with thin + thick canonical examples.
- **ADDED**: `knowledge/PUCK_SCREENS.md` (new, with classification dispatcher).
- **ADDED**: `knowledge/reference/PUCK_SCREENS_REFERENCE.md` (new, with temperature-compensation table).

## Technical Constraints

- **Uniform quick+deep pattern** (MEMORY.md SoT): every top-level file in `knowledge/` has a matching `knowledge/reference/TOPIC_REFERENCE.md`. This feature honors the pattern.
- **One-row-per-topic in MEMORY.md SoT table**: R8 requires two distinct rows, one per file, consistent with how MILK_AND_DRINKS and BASKETS and others are listed.
- **`/consult` cascade prevention** (max 1 quick + 1 deep per question): the classification dispatcher (R2) front-loads the quick file so users who route to it for a mesh/thick question still get the correct classification signal without needing to also load the reference file.
- **Single Source of Truth** (MEMORY.md): R4 migrates EXTRACTION_SCIENCE.md:42 content into PUCK_SCREENS.md to avoid duplication.
- **Temperature claim ownership**: R3 anchors numeric offset claims in the reference file; skills do not duplicate them.
- **Public-repo shared-by-others** (CLAUDE.md Data Architecture): template defaults are `None`; skills handle missing row silently.
- **Auto-commit policy** (CLAUDE.md Data Architecture): user edits to `user-setup.md` Puck Screen row propagate via existing `.data-repo-path` auto-commit. R20's `/feedback` grind-map writes also auto-commit per the existing pattern.
- **Core Rule tripwire** (CLAUDE.md): "Sour AND bitter = channeling. Fix puck prep, NOT grind." preserved byte-for-byte via SHA256 (R12).
- **Equipment-table row format**: matches existing product-first-with-classification-in-parens pattern. Template default: `None`. Example configured (thin): `Normcore 58.5mm round-hole (0.8mm thin, 316 stainless)`. Example configured (thick, for R18): `Pesado Diffuser 58mm mesh (1.7mm thick)`.
- **Parsing contract** (R13): canonical tokens are `None`, `thin`, `thick`, `round-hole`, `mesh`. Skills substring-match case-insensitively.
- **Read-only skill access to user-setup.md Puck Screen row** (R17): no skill writes the field; prevents lost-write races with existing Active Coffee updates.
- **Skills directory location**: `.claude/skills/{consult,diagnose,feedback,new-coffee}/SKILL.md` (project-local; `gaggimate-profiles` not in scope).
- **Back-compat writer policy** (R20): `/feedback`'s grind-map writer appends 12-column rows after feature ship; existing 11-column rows are NOT migrated automatically. Users see one transitional ragged state until they add the header column to their private `grind-map.md` manually.

## Open Decisions

None. All design choices resolved during Clarify, Spec interview, and critical-review loop.
